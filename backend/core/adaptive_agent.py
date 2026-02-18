"""
Adaptive Agent - Dynamic Code Generation AI Agent
====================================================
Replaces the predefined-tool ReactAgent with a dynamic system that
generates Python code on-the-fly using primitives.

Architecture:
- THINK: Groq LLM analyzes task + context
- GENERATE: LLM outputs <action>, <code>, <ask>, or <answer>
- CLASSIFY: RiskClassifier determines safe/risky/blocked
- EXECUTE: SandboxExecutor runs code (or waits for confirmation)
- OBSERVE: Results fed back to LLM
- ADAPT: If error, LLM tries alternative approach

No predefined tools. Just 6 primitives and unlimited code generation.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from .sandbox import SandboxExecutor, RiskClassifier, ExecutionResult
from .strategy_store import StrategyStore
from .tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


@dataclass
class AgentEvent:
    """Event yielded by the agent during execution"""
    type: str  # thinking, action, code_exec, action_result, answer, ask, confirm_needed, step_progress, error
    content: str
    data: Dict[str, Any] = field(default_factory=dict)

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
    """

    def __init__(self):
        self.max_steps = 15
        self.sandbox = SandboxExecutor(timeout=30.0)
        self.classifier = RiskClassifier()
        self.strategies = StrategyStore()
        self.groq_key = os.getenv("GROQ_API_KEY", "")

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

        return f"""You are Super Manager, an adaptive AI agent that can handle ANY task. You solve problems by writing Python code using tools - building blocks that let you search the web, browse pages, scrape data, generate images, fill forms, generate payment links, and more. New tools may be dynamically discovered via MCP servers.

{primitives_section}

HOW TO RESPOND (use exactly ONE of these formats per turn):

1. SIMPLE PRIMITIVE CALL - For single operations:
<think>Your reasoning about what to do and why</think>
<action>{{"primitive": "web_search", "params": {{"query": "resorts in Goa December 2025"}}}}</action>

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
- If a step fails, analyze the error and try an alternative approach.
- For complex tasks: Search first -> Scrape details -> Present options -> Act on selection.
- When presenting options with <ask>, include labels, descriptions, and URLs when available.
- Maximum {self.max_steps} steps per request. Be efficient.
- For simple questions or general knowledge, just use <answer> directly.
{strategy_section}
TASK APPROACH:
1. Understand what the user needs
2. If info is missing, ask the user (use <ask> or <answer> with a question)
3. Search for information (web_search, browse_page)
4. Scrape specific details if needed (scrape_data)
5. Present options if applicable (<ask>)
6. Execute actions with user confirmation if risky (fill_form)
7. Provide final answer with all details
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
        if not self.groq_key:
            yield AgentEvent(
                type="error",
                content="Groq API key not configured. Set GROQ_API_KEY environment variable.",
            )
            return

        # Check for cached strategy
        strategy_hint = self.strategies.get_strategy_hint(user_message)

        system_prompt = self._build_system_prompt(feedback_context, strategy_hint)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        scratchpad: List[Dict[str, str]] = []
        context: Dict[str, Any] = {}  # Accumulated results from steps
        steps_executed: List[Dict[str, Any]] = []  # For strategy caching

        for step in range(self.max_steps):
            # Emit step progress
            yield AgentEvent(
                type="step_progress",
                content=f"Step {step + 1}",
                data={"current_step": step + 1, "max_steps": self.max_steps},
            )

            # THINK: Call LLM
            try:
                llm_response = await self._call_groq(messages + scratchpad)
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
                    data=result.data,
                )

                # Add to scratchpad
                scratchpad.append({"role": "assistant", "content": llm_response})
                remaining = self.max_steps - step - 1
                budget_note = f" [{remaining} steps remaining]" if remaining <= 3 else ""
                scratchpad.append({
                    "role": "user",
                    "content": f"<action_result>{result.output}</action_result>{budget_note}",
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

                yield AgentEvent(
                    type="action_result",
                    content=result.output[:500] if result.output else "No output",
                    data=result.data,
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

        yield AgentEvent(
            type="action_result",
            content=result.output[:500] if result.output else "Done",
            data=result.data,
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
            llm_response = await self._call_groq(all_messages)
            answer = self._extract_tag(llm_response, "answer")
            if answer:
                yield AgentEvent(type="answer", content=answer)
            else:
                clean = self._strip_tags(llm_response)
                yield AgentEvent(type="answer", content=clean)
        except Exception:
            yield AgentEvent(type="answer", content=result.output)

    async def _call_groq(self, messages: List[Dict[str, str]], retry: bool = True) -> str:
        """Call Groq API with retry on 429 rate limit"""
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
        """Extract content between XML tags"""
        pattern = rf"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
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
