"""
Adaptive Agent - Dynamic Code Generation AI Agent
====================================================
Replaces the predefined-tool ReactAgent with a dynamic system that
generates Python code on-the-fly using primitives.

Architecture (10-Step Pipeline per README):
1. INPUT LAYER: Receive message
2. INTENT ENGINE: Classify intent
3. TASK CLASSIFIER: Categorize by type/complexity/risk  ← NEW
4. PLANNER: Generate multi-step plan
5. CAPABILITY ROUTER: Route to execution engine
6. INTEGRATION MANAGER: Check API availability
7. EXECUTION LAYER: Run actions
8. HUMAN-IN-LOOP: Confirm risky actions
9. FEEDBACK: Update memory
10. LEARNING: Cache successful strategies

Key components:
- THINK: LLM analyzes task + context
- GENERATE: LLM outputs <action>, <code>, <ask>, or <answer>
- CLASSIFY: RiskClassifier + TaskClassifier determine safe/risky/blocked
- EXECUTE: SandboxExecutor runs code (or waits for confirmation)
- OBSERVE: Results fed back to LLM
- ADAPT: If error, LLM tries alternative approach
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, AsyncGenerator
from pathlib import Path
import httpx

from dotenv import load_dotenv

# Explicitly load .env from project root
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)

from .sandbox import SandboxExecutor, RiskClassifier, ExecutionResult
from .strategy_store import StrategyStore
from .tool_registry import get_tool_registry
from .task_classifier import get_task_classifier, TaskClassification, TaskRiskLevel

logger = logging.getLogger(__name__)

# OpenAI is PRIMARY provider for agentic tasks (best instruction following)
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenRouter is SECONDARY provider (200+ models including Claude, GPT-4, Llama, etc.)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("AI_MODEL", "openai/gpt-3.5-turbo")

# Groq is FALLBACK provider
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Ollama is LOCAL FALLBACK provider (use 8b model for better instruction following)
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


@dataclass
class AgentEvent:
    """Event yielded by the agent during execution"""
    type: str  # thinking, action, code_exec, action_result, answer, ask, confirm_needed, step_progress, error
    content: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    """Final result from agent execution"""
    success: bool
    response: str
    data: Dict[str, Any] = field(default_factory=dict)
    steps_taken: int = 0
    primitives_used: List[str] = field(default_factory=list)
    needs_confirmation: bool = False
    pending_action: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PendingConfirmation:
    """Stores a pending action waiting for user confirmation"""
    action_type: str  # "action" or "code"
    primitive_name: Optional[str]  # for action type
    params: Dict[str, Any]  # for action type
    code: Optional[str]  # for code type
    thinking: str
    scratchpad: List[Dict[str, str]]
    history: List[Dict[str, str]]
    context: Dict[str, Any]  # accumulated results from previous steps


class AdaptiveAgent:
    """
    Adaptive AI agent that generates code on-the-fly.
    No predefined tools - composes primitives dynamically.
    
    Implements 10-Layer Pipeline:
    1. Input → 2. Intent → 3. Task Classification → 4. Planning →
    5. Capability Routing → 6. Integration Check → 7. Execution →
    8. Human-in-Loop → 9. Memory → 10. Learning
    """

    def __init__(self):
        self.max_steps = 15
        self.sandbox = SandboxExecutor(timeout=30.0)
        self.classifier = RiskClassifier()
        self.task_classifier = get_task_classifier()  # Layer 3: Task Classification
        self.strategies = StrategyStore()
        # OpenAI is PRIMARY (best for agentic tasks)
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        # OpenRouter is SECONDARY (200+ models)
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        # Groq is FALLBACK
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        
        # Priority: OpenAI > OpenRouter > Ollama
        self.use_openai = bool(self.openai_key)
        self.use_openrouter = bool(self.openrouter_key) and not self.use_openai
        logger.info(f"[AdaptiveAgent] Initialized - use_openai: {self.use_openai}, use_openrouter: {self.use_openrouter}")

    def _build_system_prompt(self, feedback_context: str = "", strategy_hint: str = "") -> str:
        """Build the system prompt with dynamic tools documentation"""
        registry = get_tool_registry()
        primitives_section = registry.get_prompt_section()

        feedback_section = ""
        if feedback_context:
            feedback_section = f"""
USER FEEDBACK HISTORY:
{feedback_context}
Use this feedback to improve your responses. Avoid patterns that got negative feedback.
"""

        strategy_section = ""
        if strategy_hint:
            strategy_section = f"\n{strategy_hint}\n"

        return f"""You are Super Manager, an autonomous AI agent that EXECUTES tasks - not one that explains how to do them.

ABSOLUTE RULE: YOU MUST USE <action> OR <code> TAGS TO ACT. Never just say "I will do X" in an <answer> - ACTUALLY DO IT.

CORE IDENTITY:
- You are an AGENT that DOES things, not an assistant that gives instructions
- When asked to do something, USE <action> or <code> to DO IT. Never say "I will" - just do it
- You have full access to the internet, can browse any website, fill forms, and execute real actions
- You are CONFIDENT in your abilities and STAND BY your actions
- If something fails, try an alternative approach. NEVER give up after one attempt

CRITICAL RULES - NEVER VIOLATE:
1. When you receive a task, IMMEDIATELY use <action> or <code> to start doing it
2. NEVER respond with <answer> containing "I will..." or "Let me..." - use <action> instead
3. NEVER say "I don't have access to..." - Use browse_page or web_search
4. NEVER give step-by-step instructions to the user - DO the steps yourself
5. NEVER apologize and say you'll try to help - USE YOUR TOOLS NOW
6. NEVER make excuses about limitations - Use your tools to work around them
7. When a user challenges you, STAND BY your work. Don't backtrack unnecessarily
8. If you make a mistake, FIX IT immediately with another <action> or <code>

YOUR CAPABILITIES:
- Search any information on the web (web_search)
- Browse any public website (browse_page)
- Scrape specific data from pages (scrape_data)
- Generate images (generate_image)
- Fill forms and interact with websites (fill_form) [requires confirmation]
- Execute Python code for data processing (run_python) [requires confirmation]
- All additional tools registered: payment links, stealth browser, MCP tools

{primitives_section}

HOW TO RESPOND (use exactly ONE of these formats per turn):

1. SIMPLE PRIMITIVE CALL - For single operations:
<think>Your reasoning about what to do and why</think>
<action>{{"primitive": "TOOL_NAME", "params": {{"param1": "value1", "param2": "value2"}}}}</action>

EXAMPLES:
- <action>{{"primitive": "web_search", "params": {{"query": "best restaurants in Mumbai"}}}}</action>
- <action>{{"primitive": "browse_page", "params": {{"url": "https://example.com"}}}}</action>
- <action>{{"primitive": "scrape_data", "params": {{"url": "https://example.com", "extract": "prices, names"}}}}</action>
- <action>{{"primitive": "generate_image", "params": {{"prompt": "sunset over mountains"}}}}</action>
- <action>{{"primitive": "create_meeting", "params": {{"topic": "Team Call", "participants": ["john@email.com"], "platform": "zoom"}}}}</action>
- <action>{{"primitive": "send_email", "params": {{"to": "john@email.com", "subject": "Hello", "body": "Hi there"}}}}</action>

2. MULTI-STEP CODE - When you need logic, loops, or data processing:
<think>Your reasoning</think>
<code>
results = await web_search("best resorts Goa budget")
urls = [r["url"] for r in results.data.get("results", [])[:3]]
all_info = []
for url in urls:
    info = await scrape_data(url, extract="hotel name, price, rating, amenities")
    all_info.append(info.output)
print("\\n---\\n".join(all_info))
</code>

3. PRESENT OPTIONS TO USER - When user needs to make a choice:
<think>Your reasoning</think>
<ask>
{{
    "message": "I found these resorts in Goa. Which one interests you?",
    "options": [
        {{"label": "Resort A - Rs4500/night, 4.5 stars", "value": "resort_a", "description": "Beachfront, pool, spa", "url": "https://..."}},
        {{"label": "Resort B - Rs3200/night, 4.2 stars", "value": "resort_b", "description": "City center, restaurant", "url": "https://..."}}
    ]
}}
</ask>

4. FINAL ANSWER - When you have the complete response:
<think>Summary of what you did</think>
<answer>Your complete, detailed response to the user with all relevant information</answer>

IMPORTANT RULES:
- Use ONE response format per turn. After getting results, you'll think again.
- <action> for simple single calls. <code> for anything needing loops/logic/multiple calls.
- Primitives return PrimitiveResult objects. Access: result.success, result.output, result.data
- In <code>, use `await` before calling any primitive: `result = await web_search("query")`
- In <code>, use `print()` to output results that you want to see in the next step.
- fill_form and run_python ALWAYS require user confirmation before execution.
- NEVER fabricate URLs, prices, or data. ALWAYS search/scrape for real information.
- Previous step results are available in the `context` dict variable.
- If a step fails, analyze the error and try an ALTERNATIVE approach. NEVER GIVE UP.
- For complex tasks: Search first -> Scrape details -> Present options -> Act on selection.
- When presenting options with <ask>, include labels, descriptions, and URLs when available.
- Maximum {self.max_steps} steps per request. Be efficient.
- SIMPLE QUESTIONS: For basic math (2+2=4), general knowledge (capital of France), or conversational questions, use <answer> directly. DON'T use tools for these!

EXECUTION MINDSET:
- Think like an employee who gets things done, not a professor who explains concepts
- User says "book a flight" → You SEARCH for flights, PRESENT options, FILL the booking form
- User says "find me a hotel" → You SEARCH hotels, SCRAPE prices, PRESENT best matches
- User says "send an email" → You COMPOSE the email and EXECUTE the send action
- NEVER respond with "Here's how you can..." - JUST DO IT
- If you need login credentials, ASK for them. Don't assume you can't do something
- If a website blocks you, try a different website. There's always an alternative
{strategy_section}
TASK EXECUTION FLOW:
1. UNDERSTAND: Parse what the user wants done
2. ACT IMMEDIATELY: Start executing - search, browse, scrape
3. GATHER INFO: If you need user input, ASK specifically what you need
4. PRESENT OPTIONS: When multiple choices exist, show them clearly
5. EXECUTE: Fill forms, submit requests, complete the action
6. CONFIRM: Report what you did with proof (URLs, screenshots, results)

WHEN CHALLENGED OR CORRECTED:
- If user says you're wrong → First verify your data. If you're RIGHT, politely but firmly maintain your position.
- If user says "sugarcoating" or "lying" → This means you're being vague. Be SPECIFIC with evidence.
- If user says you didn't do something → Check the action results. If done, show the proof. If not done, DO IT NOW.
- STAND BY correct information. Don't apologize for being right. Say: "I've verified this and..."
- If you made an actual mistake → Say briefly "You're right, let me fix that" and FIX IT immediately.
- NEVER say "I apologize, you're correct" without actually verifying - that's sugarcoating.
- Confidence comes from EVIDENCE. When challenged, SHOW your proof (URLs, data, results).
{feedback_section}"""

    async def run(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        user_id: str = "default",
        feedback_context: str = "",
        session_id: str = "",
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Main adaptive loop. Yields AgentEvent objects for streaming.

        Events:
        - thinking: LLM is reasoning
        - action: Executing a single primitive
        - code_exec: Executing generated code
        - action_result: Primitive/code returned a result
        - answer: Final response to user
        - ask: Presenting options to user
        - confirm_needed: Risky action needs user confirmation
        - step_progress: Current step / total info
        - error: Something went wrong
        """
        # Check if any AI provider is configured
        if not self.openai_key and not self.openrouter_key and not self.groq_key:
            # Check if Ollama is available as local fallback
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{OLLAMA_URL}/api/tags")
                    if resp.status_code != 200:
                        raise Exception("Ollama not responding")
            except Exception:
                yield AgentEvent(
                    type="error",
                    content="No AI API key configured. Set OPENAI_API_KEY, OPENROUTER_API_KEY, or run Ollama locally.",
                )
                return

        # ========================================
        # LAYER 3: TASK CLASSIFICATION (per README)
        # ========================================
        # Classify task BEFORE execution to:
        # 1. Determine category (meeting, email, shopping, etc.)
        # 2. Assess complexity (simple/medium/complex)
        # 3. Pre-compute risk level
        # 4. Route to appropriate capability
        task_classification = self.task_classifier.classify(user_message)
        
        logger.info(
            f"[TaskClassifier] Category: {task_classification.category.value}, "
            f"Complexity: {task_classification.complexity.value}, "
            f"Risk: {task_classification.risk_level.value}"
        )
        
        suggested_tools = getattr(task_classification, "suggested_tools", None) or []

        # Emit classification event for frontend awareness
        yield AgentEvent(
            type="task_classified",
            content=f"Task: {task_classification.category.value}",
            data={
                "category": task_classification.category.value,
                "complexity": task_classification.complexity.value,
                "risk_level": task_classification.risk_level.value,
                "requires_confirmation": task_classification.requires_confirmation,
                "requires_verification": task_classification.requires_verification,
                "suggested_tools": suggested_tools,
                "required_integrations": getattr(task_classification, "required_integrations", []) or [],
                "routing_hint": getattr(task_classification, "routing_hint", None),
            }
        )

        # Check for cached strategy
        strategy_hint = self.strategies.get_strategy_hint(user_message)

        # Include task classification in system prompt for better routing
        classification_context = f"""
TASK CLASSIFICATION (pre-analyzed):
- Category: {task_classification.category.value}
- Complexity: {task_classification.complexity.value}
- Risk Level: {task_classification.risk_level.value}
- Suggested Tools: {', '.join(suggested_tools) if suggested_tools else 'auto'}
Use this classification to guide your approach.
"""
        
        system_prompt = self._build_system_prompt(feedback_context + classification_context, strategy_hint)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        scratchpad: List[Dict[str, str]] = []
        context: Dict[str, Any] = {
            'user_id': user_id, 
            'session_id': session_id,
            'task_classification': {
                'category': task_classification.category.value,
                'risk_level': task_classification.risk_level.value,
                'requires_confirmation': task_classification.requires_confirmation
            }
        }  # Accumulated results from steps
        steps_executed: List[Dict[str, Any]] = []  # For strategy caching

        for step in range(self.max_steps):
            # Emit step progress
            yield AgentEvent(
                type="step_progress",
                content=f"Step {step + 1}",
                data={"current_step": step + 1, "max_steps": self.max_steps},
            )

            # THINK: Call LLM (OpenRouter primary, Groq fallback)
            try:
                llm_response = await self._call_llm(messages + scratchpad)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                yield AgentEvent(type="error", content=f"AI service error: {str(e)}")
                return

            # Parse XML tags
            thinking = self._extract_tag(llm_response, "think")
            action_str = self._extract_tag(llm_response, "action")
            code_str = self._extract_tag(llm_response, "code")
            ask_str = self._extract_tag(llm_response, "ask")
            answer = self._extract_tag(llm_response, "answer")

            # Handle case where LLM outputs raw JSON action without tags
            if not action_str and not code_str and not ask_str and not answer:
                stripped = llm_response.strip()
                logger.info(f"[LLM Response] No tags found. Raw response (first 200 chars): {stripped[:200]}")
                
                # Check if it looks like a JSON action ({"primitive": ...})
                if stripped.startswith('{"primitive":') or stripped.startswith('{"primitive" :'):
                    action_str = stripped
                    logger.info(f"[LLM Response] Detected raw JSON action starting with 'primitive'")
                elif '"primitive"' in stripped:
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{[^{}]*"primitive"[^{}]*\}', stripped)
                    if json_match:
                        action_str = json_match.group(0)
                        logger.info(f"[LLM Response] Extracted JSON from response: {action_str[:100]}")

            # Yield thinking
            if thinking:
                yield AgentEvent(type="thinking", content=thinking)

            # --- ANSWER ---
            if answer:
                yield AgentEvent(type="answer", content=answer)
                # Cache successful strategy if we executed multiple steps
                if len(steps_executed) >= 2:
                    self._cache_strategy(user_message, steps_executed)
                return

            # --- ASK (present options) ---
            if ask_str:
                try:
                    cleaned = self._clean_json(ask_str)
                    ask_data = json.loads(cleaned)
                    yield AgentEvent(
                        type="ask",
                        content=ask_data.get("message", "Please choose an option:"),
                        data={
                            "options": ask_data.get("options", []),
                            "scratchpad": scratchpad,
                            "history": history,
                            "context": context,
                        },
                    )
                    return  # Pause for user selection
                except json.JSONDecodeError:
                    # If JSON fails, treat as a question in answer format
                    yield AgentEvent(type="answer", content=ask_str)
                    return

            # --- ACTION (single primitive call) ---
            if action_str:
                try:
                    cleaned = self._clean_json(action_str)
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    scratchpad.append({"role": "assistant", "content": llm_response})
                    scratchpad.append({
                        "role": "user",
                        "content": '<action_result>Error: Invalid JSON in action tag. Use format: {"primitive": "name", "params": {"key": "value"}}</action_result>',
                    })
                    continue

                primitive_name = parsed.get("primitive", "")
                params = parsed.get("params", {})

                # =====================================================================
                # 🔐 INTEGRATION MANAGER: Layer 6 - Secure Credential Management
                # Check API availability. If not connected -> ask user.
                # =====================================================================
                from backend.core.integration_manager.integration_store import integration_store
                required_integration = None
                
                if primitive_name == "create_meeting":
                    platform = params.get("platform", "")
                    platform_l = platform.lower() if isinstance(platform, str) else str(platform).lower()
                    # Only hard-gate providers that have no meaningful fallback.
                    # Zoom requests are handled inside the primitive (prompt to connect or offer Jitsi fallback).
                    if "meet" in platform_l or "google" in platform_l:
                        required_integration = "google_calendar"
                # send_email: handled inside primitive (OAuth if available, SMTP fallback otherwise)

                # Only hard-gate when the integration store is actually usable (Supabase-backed).
                # In memory-only/dev mode, let primitives handle fallbacks (e.g., Zoom -> offer Jitsi).
                if required_integration and context.get("user_id") and getattr(integration_store, "supabase", None):
                    user_id = context.get("user_id", "default")
                    if not integration_store.is_connected(user_id, required_integration):
                        app_name = integration_store.AVAILABLE_INTEGRATIONS.get(required_integration, {}).get("name", required_integration.title())
                        # If integration is missing, dynamically ask user to connect it
                        fallback_msg = (
                            f"To proceed with this, I need to connect to your **{app_name}** account.\n\n"
                            f"> **Secure Token Storage:** We use token-based OAuth and never store your raw credentials.\n\n"
                            f"Please click on **⚙️ Integrations** in the settings panel to connect your account safely."
                        )
                        yield AgentEvent(
                            type="answer",
                            content=fallback_msg,
                            data={"requires_connection": True, "required_integration": required_integration}
                        )
                        return
                # =====================================================================

                # Risk classification
                classification = self.classifier.validate_action(primitive_name)

                if classification["risk"] == "blocked":
                    scratchpad.append({"role": "assistant", "content": llm_response})
                    scratchpad.append({
                        "role": "user",
                        "content": f'<action_result>Error: {classification["reason"]}</action_result>',
                    })
                    continue

                if classification["risk"] == "risky":
                    # Needs user confirmation
                    yield AgentEvent(
                        type="confirm_needed",
                        content=thinking or f"Ready to execute {primitive_name}",
                        data={
                            "action_type": "action",
                            "primitive": primitive_name,
                            "params": params,
                            "code": None,
                            "scratchpad": scratchpad,
                            "history": history,
                            "context": context,
                        },
                    )
                    return

                # SAFE - auto execute
                yield AgentEvent(
                    type="action",
                    content=f"Executing {primitive_name}...",
                    data={"primitive": primitive_name, "params": params},
                )

                result = await self.sandbox.execute_action(primitive_name, params, context)

                # Store result in context
                context[f"step_{step + 1}"] = {
                    "type": "action",
                    "primitive": primitive_name,
                    "result": result.output[:2000],
                    "data": result.data,
                }

                steps_executed.append({
                    "step_type": "action",
                    "description": f"{primitive_name}({json.dumps(params)[:100]})",
                    "primitive_or_code": primitive_name,
                    "params_template": params,
                })

                yield AgentEvent(
                    type="action_result",
                    content=result.output[:500] if result.output else "No output",
                    data={
                        **(result.data or {}),
                        "_meta": {
                            "success": bool(result.success),
                            "error": result.error,
                            "primitive": primitive_name,
                            "params": params,
                        },
                    },
                )

                # Add to scratchpad with error guidance if failed
                scratchpad.append({"role": "assistant", "content": llm_response})
                remaining = self.max_steps - step - 1
                budget_note = f" [{remaining} steps remaining]" if remaining <= 3 else ""
                
                if result.success:
                    scratchpad.append({
                        "role": "user",
                        "content": f"<action_result>{result.output}</action_result>{budget_note}",
                    })
                else:
                    # Add helpful guidance for failed actions
                    error_guidance = ""
                    if "missing" in result.output.lower() or "wrong_params" in (result.error or ""):
                        error_guidance = f"\n\nREMINDER: Use this format: {{\"primitive\": \"{primitive_name}\", \"params\": {{\"url\": \"the_url_here\", ...}}}}"
                    scratchpad.append({
                        "role": "user",
                        "content": f"<action_result>Error: {result.output}{error_guidance}</action_result>{budget_note}",
                    })

            # --- CODE (multi-step execution) ---
            elif code_str:
                # Risk classification
                classification = self.classifier.classify(code_str)

                if classification["risk"] == "blocked":
                    scratchpad.append({"role": "assistant", "content": llm_response})
                    scratchpad.append({
                        "role": "user",
                        "content": f'<code_result>Error: Code blocked - {classification["reason"]}. Use only the available primitives.</code_result>',
                    })
                    continue

                if classification["risk"] == "risky":
                    yield AgentEvent(
                        type="confirm_needed",
                        content=thinking or "Code requires confirmation before execution",
                        data={
                            "action_type": "code",
                            "primitive": None,
                            "params": {},
                            "code": code_str,
                            "scratchpad": scratchpad,
                            "history": history,
                            "context": context,
                        },
                    )
                    return

                # SAFE - auto execute
                yield AgentEvent(
                    type="code_exec",
                    content="Executing generated code...",
                    data={"code": code_str, "primitives_used": classification["primitives_used"]},
                )

                result = await self.sandbox.execute_code(code_str, context)

                context[f"step_{step + 1}"] = {
                    "type": "code",
                    "result": result.output[:2000],
                    "data": result.data,
                }

                steps_executed.append({
                    "step_type": "code",
                    "description": f"Code block using {', '.join(classification['primitives_used'])}",
                    "primitive_or_code": code_str[:200],
                    "params_template": {},
                })

                if result.error == "integration_required":
                    yield AgentEvent(
                        type="integration_needed",
                        content=f"Connecting to {result.data.get('required_integration')} is required to proceed.",
                        data={
                            "service": result.data.get("required_integration"),
                            "status": "not_connected"
                        }
                    )
                    return # Pause execution until user connects

                yield AgentEvent(
                    type="action_result",
                    content=result.output[:500] if result.output else "No output",
                    data={
                        **(result.data or {}),
                        "_meta": {
                            "success": bool(result.success),
                            "error": result.error,
                            "primitive": "__code__",
                            "params": {},
                        },
                    },
                )

                scratchpad.append({"role": "assistant", "content": llm_response})
                remaining = self.max_steps - step - 1
                budget_note = f" [{remaining} steps remaining]" if remaining <= 3 else ""

                if result.success:
                    scratchpad.append({
                        "role": "user",
                        "content": f"<code_result>{result.output}</code_result>{budget_note}",
                    })
                else:
                    scratchpad.append({
                        "role": "user",
                        "content": f"<code_result>Error: {result.output}\n\nPlease try a different approach or fix the error.</code_result>{budget_note}",
                    })

            else:
                # No recognized tags - treat raw response as answer
                clean = self._strip_tags(llm_response)
                yield AgentEvent(type="answer", content=clean)
                return

        # Reached max steps
        yield AgentEvent(
            type="answer",
            content="I've used all my available steps for this request. Here's what I've gathered so far based on my research above. Let me know if you'd like me to continue or try a different approach.",
        )

    async def execute_confirmed_action(
        self,
        action_type: str,
        primitive_name: Optional[str],
        params: Dict[str, Any],
        code: Optional[str],
        history: List[Dict[str, str]],
        scratchpad: List[Dict[str, str]],
        context: Dict[str, Any],
        user_id: str = "default",
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Execute an action that was previously pending confirmation.
        Called when user confirms "yes".
        """
        if action_type == "action" and primitive_name:
            yield AgentEvent(
                type="action",
                content=f"Executing {primitive_name}...",
                data={"primitive": primitive_name, "params": params},
            )
            result = await self.sandbox.execute_action(primitive_name, params, context)

        elif action_type == "code" and code:
            yield AgentEvent(
                type="code_exec",
                content="Executing confirmed code...",
                data={"code": code},
            )
            result = await self.sandbox.execute_code(code, context)

        else:
            yield AgentEvent(type="error", content="Invalid confirmation data.")
            return

        if result.error == "integration_required":
            yield AgentEvent(
                type="integration_needed",
                content=f"Connecting to {result.data.get('required_integration')} is required to proceed.",
                data={
                    "service": result.data.get("required_integration"),
                    "status": "not_connected"
                }
            )
            return # Pause execution

        yield AgentEvent(
            type="action_result",
            content=result.output[:500] if result.output else "Done",
            data={
                **(result.data or {}),
                "_meta": {
                    "success": bool(result.success),
                    "error": result.error,
                    "primitive": primitive_name or "__code__",
                    "params": params if primitive_name else {},
                },
            },
        )

        # Let LLM summarize the result
        scratchpad_copy = list(scratchpad)
        if action_type == "action":
            scratchpad_copy.append({
                "role": "assistant",
                "content": f"<think>User confirmed. Executing {primitive_name}.</think>\n<action>{json.dumps({'primitive': primitive_name, 'params': params})}</action>",
            })
        else:
            scratchpad_copy.append({
                "role": "assistant",
                "content": f"<think>User confirmed. Executing code.</think>\n<code>{code}</code>",
            })

        result_tag = "action_result" if action_type == "action" else "code_result"
        scratchpad_copy.append({
            "role": "user",
            "content": f"<{result_tag}>{result.output}</{result_tag}>",
        })

        system_prompt = self._build_system_prompt()
        all_messages = [{"role": "system", "content": system_prompt}] + history + scratchpad_copy

        try:
            llm_response = await self._call_llm(all_messages)
            answer = self._extract_tag(llm_response, "answer")
            if answer:
                yield AgentEvent(type="answer", content=answer)
            else:
                clean = self._strip_tags(llm_response)
                yield AgentEvent(type="answer", content=clean)
        except Exception:
            yield AgentEvent(type="answer", content=result.output)

    async def _call_llm(self, messages: List[Dict[str, str]], retry: bool = True) -> str:
        """Call LLM API - OpenAI primary, OpenRouter secondary, Ollama fallback"""
        logger.info(f"[_call_llm] use_openai={self.use_openai}, use_openrouter={self.use_openrouter}")
        if self.use_openai:
            return await self._call_openai(messages, retry)
        elif self.use_openrouter:
            return await self._call_openrouter(messages, retry)
        else:
            return await self._call_ollama(messages)
    
    async def _call_openai(self, messages: List[Dict[str, str]], retry: bool = True) -> str:
        """Call OpenAI API directly (best for agentic tasks)"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENAI_URL,
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )

            if response.status_code == 429 and retry:
                import asyncio
                logger.warning("OpenAI rate limit hit, retrying in 2s...")
                await asyncio.sleep(2)
                return await self._call_openai(messages, retry=False)

            if response.status_code != 200:
                error_text = response.text[:500]
                logger.error(f"OpenAI error {response.status_code}: {error_text}")
                # Fallback to OpenRouter, then Ollama
                if self.openrouter_key:
                    logger.warning(f"OpenAI failed ({response.status_code}), trying OpenRouter...")
                    try:
                        return await self._call_openrouter(messages, retry)
                    except Exception as e:
                        logger.warning(f"OpenRouter also failed: {e}, trying Ollama...")
                        return await self._call_ollama(messages)
                logger.warning(f"OpenAI failed ({response.status_code}), trying Ollama...")
                return await self._call_ollama(messages)

            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise Exception("OpenAI API returned no choices")

            return data["choices"][0]["message"]["content"]
    
    async def _call_openrouter(self, messages: List[Dict[str, str]], retry: bool = True) -> str:
        """Call OpenRouter API with retry on rate limit"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "HTTP-Referer": os.getenv("APP_URL", "http://localhost:8000"),
                    "X-Title": "Super Manager AI",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                    "top_p": 0.9,
                },
            )

            if response.status_code == 429 and retry:
                import asyncio
                logger.warning("OpenRouter rate limit hit, retrying in 2s...")
                await asyncio.sleep(2)
                return await self._call_openrouter(messages, retry=False)

            if response.status_code != 200:
                error_text = response.text[:500]
                logger.error(f"OpenRouter error {response.status_code}: {error_text}")
                # Try Groq as fallback, then Ollama
                if self.groq_key:
                    logger.warning(f"OpenRouter failed ({response.status_code}), trying Groq...")
                    try:
                        return await self._call_groq(messages, retry)
                    except Exception as e:
                        logger.warning(f"Groq also failed: {e}, trying Ollama...")
                        return await self._call_ollama(messages)
                # No Groq key - try Ollama directly
                logger.warning(f"OpenRouter failed ({response.status_code}), trying Ollama...")
                return await self._call_ollama(messages)

            data = response.json()
            if "error" in data:
                # Try Groq as fallback, then Ollama
                if self.groq_key:
                    logger.warning(f"OpenRouter error, trying Groq: {data['error']}")
                    try:
                        return await self._call_groq(messages, retry)
                    except Exception as e:
                        logger.warning(f"Groq also failed: {e}, trying Ollama...")
                        return await self._call_ollama(messages)
                # No Groq key - try Ollama directly
                logger.warning(f"OpenRouter error, trying Ollama: {data['error']}")
                return await self._call_ollama(messages)
            if "choices" not in data or not data["choices"]:
                raise Exception("OpenRouter API returned no choices")

            return data["choices"][0]["message"]["content"]

    async def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API (local fallback)"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )

            if response.status_code != 200:
                error_text = response.text[:200]
                raise Exception(f"Ollama API error {response.status_code}: {error_text}")

            data = response.json()
            if "message" not in data:
                raise Exception("Ollama API returned no message")

            return data["message"]["content"]

    async def _call_groq(self, messages: List[Dict[str, str]], retry: bool = True) -> str:
        """Call Groq API with retry on 429 rate limit (fallback provider)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                    "top_p": 0.9,
                },
            )

            if response.status_code == 429 and retry:
                import asyncio
                logger.warning("Groq rate limit hit, retrying in 2s...")
                await asyncio.sleep(2)
                return await self._call_groq(messages, retry=False)

            if response.status_code != 200:
                error_text = response.text[:200]
                raise Exception(f"Groq API error {response.status_code}: {error_text}")

            data = response.json()
            if "error" in data:
                raise Exception(f"Groq API error: {data['error'].get('message', str(data['error']))}")
            if "choices" not in data or not data["choices"]:
                raise Exception("Groq API returned no choices")

            return data["choices"][0]["message"]["content"]

    def _extract_tag(self, text: str, tag: str) -> Optional[str]:
        """Extract content between XML tags - also handles unclosed tags"""
        # First try to match with closing tag
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no closing tag, try to extract everything after the opening tag
        open_pattern = rf"<{tag}>(.*)$"
        match = re.search(open_pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Remove any other opening tags that might follow
            content = re.sub(rf"</?(?:think|action|code|ask|answer)>.*", "", content, flags=re.DOTALL)
            return content.strip()
        
        return None

    def _strip_tags(self, text: str) -> str:
        """Remove all XML tags from text"""
        cleaned = re.sub(r"</?(?:think|action|code|code_result|action_result|ask|answer)>", "", text)
        return cleaned.strip()

    def _clean_json(self, text: str) -> str:
        """Clean up common LLM JSON issues"""
        cleaned = text.strip()
        # Strip markdown code fences
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        # Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        return cleaned

    def _cache_strategy(self, user_message: str, steps: List[Dict[str, Any]]):
        """Cache a successful multi-step task as a strategy"""
        # Extract keywords from message
        stop_words = {"i", "want", "to", "a", "the", "in", "for", "my", "me", "please", "can", "you", "help"}
        words = user_message.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        if len(keywords) < 2:
            return

        # Generate task type from keywords
        task_type = "_".join(keywords[:3])

        try:
            self.strategies.save_strategy(task_type, keywords, steps)
        except Exception as e:
            logger.error(f"Failed to cache strategy: {e}")
