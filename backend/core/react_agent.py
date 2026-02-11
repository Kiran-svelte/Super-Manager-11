"""
ReAct Agent - The General-Purpose AI Agent Loop
=================================================
Implements the Reasoning + Acting (ReAct) pattern:

1. THINK - LLM reasons about what to do next
2. ACT   - Execute a tool call
3. OBSERVE - Process tool result
4. Repeat until done or max steps reached

Uses Groq LLM (llama-3.3-70b) with XML tag formatting.
"""

import os
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, AsyncGenerator
import httpx

from .tools import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


@dataclass
class AgentEvent:
    """Event yielded by the agent during execution"""
    type: str  # thinking, tool_call, tool_result, answer, confirm_needed, error
    content: str
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PendingConfirmation:
    """Stores a pending tool call waiting for user confirmation"""
    tool_name: str
    tool_params: Dict[str, Any]
    thinking: str  # The LLM's reasoning
    scratchpad: List[Dict[str, str]]  # Context so far
    history: List[Dict[str, str]]  # Conversation history


class ReactAgent:
    """
    General-purpose AI agent using the ReAct pattern.

    The LLM decides what tools to use at runtime.
    No hardcoded task types - handles ANY request.
    """

    def __init__(self, tool_registry: ToolRegistry = None):
        self.tools = tool_registry or ToolRegistry()
        self.max_steps = 10
        self.groq_key = os.getenv("GROQ_API_KEY", "")

    def _build_system_prompt(self, feedback_context: str = "") -> str:
        """Build the system prompt with all available tools"""
        tools_section = self.tools.get_tools_prompt()

        feedback_section = ""
        if feedback_context:
            feedback_section = f"""
USER FEEDBACK HISTORY:
{feedback_context}
Use this feedback to improve your responses. Avoid patterns that got negative feedback. Repeat patterns that got positive feedback.
"""

        return f"""You are Super Manager, a highly capable AI personal assistant. You GENUINELY complete tasks for users - providing real, actionable results, not surface-level responses.

AVAILABLE TOOLS:
{tools_section}

RESPONSE FORMAT:

1. To use a tool:
<think>Your detailed reasoning about what to do and why</think>
<tool_call>{{"tool": "tool_name", "params": {{"key": "value"}}}}</tool_call>

2. To give your final answer:
<think>Summary of what I found/did</think>
<answer>Your complete, detailed response to the user</answer>

3. To ask the user for clarification:
<answer>Your specific question about what you need to know</answer>

PLANNING & EXECUTION:
- For complex requests, plan your approach FIRST in your <think> tag before acting.
- Break multi-step tasks into individual tool calls: search → browse → analyze → answer.
- Use multiple tools in sequence to gather complete information.
- If a search gives partial results, browse the most relevant URLs for details.
- Always verify you have ENOUGH information before giving your final answer.
- If you need 3 pieces of data, make 3 tool calls - don't stop after 1.

QUALITY STANDARDS:
- Give SPECIFIC, ACTIONABLE answers with real data (numbers, names, prices, links).
- Don't just list raw search results - synthesize, compare, and recommend.
- When generating content (emails, images, documents), make it professional and complete.
- Include relevant details: prices, ratings, addresses, dates, specifications.
- If you searched the web, provide SOURCE URLs so users can verify.
- For comparisons, create clear structured comparisons, not vague summaries.

TOOL USAGE EXAMPLES:

Example 1 - Research task:
User: "Find best laptops under $800"
<think>I need to search for laptops, then browse a review site for detailed specs and prices.</think>
<tool_call>{{"tool": "web_search", "params": {{"query": "best laptops under 800 dollars 2025 reviews"}}}}</tool_call>
[After getting results, browse top result for details, then give comprehensive comparison]

Example 2 - Image generation:
User: "Create a logo for my bakery called Sweet Dreams"
<think>I'll generate a professional logo with bakery-related imagery.</think>
<tool_call>{{"tool": "generate_image", "params": {{"prompt": "Professional bakery logo for 'Sweet Dreams', elegant typography, cupcake icon, pastel pink and gold colors, minimalist design", "style": "logo"}}}}</tool_call>
[After generation, present the result with the rendered image]

Example 3 - Multi-step task:
User: "Send a meeting invite to john@example.com for our project review"
<think>I need to create a meeting link first, then compose and send an email with the link.</think>
<tool_call>{{"tool": "create_meeting", "params": {{"title": "Project Review Meeting"}}}}</tool_call>
[After getting meeting link, compose email with the link and send it]

RULES:
- ONE tool call per turn. After getting the result, think again about next steps.
- For actions like sending email or making payment, the system handles user confirmation.
- NEVER fabricate data. Use tools for real information.
- For simple questions, math, or general knowledge, answer directly.
- Be conversational, specific, and genuinely helpful.
- Maximum {self.max_steps} tool calls per request.
- When you reach your final answer, make it comprehensive and well-formatted.
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
        Main ReAct loop. Yields AgentEvent objects for streaming.

        Events:
        - thinking: LLM is reasoning
        - tool_call: About to execute a tool
        - tool_result: Tool returned a result
        - answer: Final response to user
        - confirm_needed: Tool requires user confirmation
        - error: Something went wrong
        """
        if not self.groq_key:
            yield AgentEvent(
                type="error",
                content="Groq API key not configured. Set GROQ_API_KEY environment variable.",
            )
            return

        system_prompt = self._build_system_prompt(feedback_context)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        scratchpad: List[Dict[str, str]] = []

        for step in range(self.max_steps):
            # THINK: Call LLM
            try:
                llm_response = await self._call_groq(messages + scratchpad)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                yield AgentEvent(type="error", content=f"AI service error: {str(e)}")
                return

            # Parse XML tags from response
            thinking = self._extract_tag(llm_response, "think")
            tool_call_str = self._extract_tag(llm_response, "tool_call")
            answer = self._extract_tag(llm_response, "answer")

            # Yield thinking event
            if thinking:
                yield AgentEvent(type="thinking", content=thinking)

            # If we have an answer, we're done
            if answer:
                yield AgentEvent(type="answer", content=answer)
                return

            # If we have a tool call, execute it
            if tool_call_str:
                try:
                    # Clean up common LLM JSON issues
                    cleaned = tool_call_str.strip()
                    # Strip markdown code fences
                    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
                    # Fix trailing commas
                    cleaned = re.sub(r',\s*}', '}', cleaned)
                    cleaned = re.sub(r',\s*]', ']', cleaned)
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    try:
                        fixed = tool_call_str.replace("'", '"')
                        parsed = json.loads(fixed)
                    except json.JSONDecodeError:
                        yield AgentEvent(
                            type="error",
                            content=f"Failed to parse tool call. LLM returned invalid JSON.",
                        )
                        # Add error to scratchpad so LLM can retry
                        scratchpad.append({"role": "assistant", "content": llm_response})
                        scratchpad.append({
                            "role": "user",
                            "content": "<tool_result>Error: Your tool_call JSON was malformed. Please try again with valid JSON like: {\"tool\": \"tool_name\", \"params\": {\"key\": \"value\"}}</tool_result>",
                        })
                        continue

                tool_name = parsed.get("tool", "")
                tool_params = parsed.get("params", {})
                tool = self.tools.get_tool(tool_name)

                if not tool:
                    available = ", ".join(self.tools.list_tools())
                    scratchpad.append({"role": "assistant", "content": llm_response})
                    scratchpad.append({
                        "role": "user",
                        "content": f"<tool_result>Error: Unknown tool '{tool_name}'. Available tools: {available}</tool_result>",
                    })
                    continue

                # Check if confirmation needed
                if tool.requires_confirmation:
                    yield AgentEvent(
                        type="confirm_needed",
                        content=thinking or f"Ready to execute {tool_name}",
                        data={
                            "tool": tool_name,
                            "params": tool_params,
                            "scratchpad": scratchpad,
                            "history": history,
                        },
                    )
                    return  # Stop here - wait for user to confirm

                # ACT: Execute tool
                yield AgentEvent(
                    type="tool_call",
                    content=f"Using {tool_name}...",
                    data={"tool": tool_name, "params": tool_params},
                )

                try:
                    # Pass context params for memory/reminder tools
                    tool_params["_user_id"] = user_id
                    tool_params["_session_id"] = session_id
                    result = await tool.execute(**tool_params)
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    result = ToolResult(
                        success=False,
                        output=f"Tool error: {str(e)}",
                        error=str(e),
                    )

                # OBSERVE: Yield result and add to scratchpad
                yield AgentEvent(
                    type="tool_result",
                    content=result.output[:500] if result.output else "No output",
                    data=result.data,
                )

                scratchpad.append({"role": "assistant", "content": llm_response})
                remaining = self.max_steps - step - 1
                budget_note = f" [{remaining} steps remaining]" if remaining <= 3 else ""
                scratchpad.append({
                    "role": "user",
                    "content": f"<tool_result>{result.output}</tool_result>{budget_note}",
                })

            else:
                # No XML tags at all - treat the raw response as an answer
                clean = self._strip_tags(llm_response)
                yield AgentEvent(type="answer", content=clean)
                return

        # Reached max steps
        yield AgentEvent(
            type="answer",
            content="I've used all my available steps for this request. Here's what I've found so far based on my research above.",
        )

    async def execute_confirmed_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        history: List[Dict[str, str]],
        scratchpad: List[Dict[str, str]],
        user_id: str = "default",
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Execute a tool that was previously pending confirmation.
        Called when user confirms "yes".
        """
        tool = self.tools.get_tool(tool_name)
        if not tool:
            yield AgentEvent(type="error", content=f"Tool {tool_name} not found.")
            return

        yield AgentEvent(
            type="tool_call",
            content=f"Executing {tool_name}...",
            data={"tool": tool_name, "params": tool_params},
        )

        try:
            result = await tool.execute(**tool_params)
        except Exception as e:
            yield AgentEvent(type="error", content=f"Tool failed: {str(e)}")
            return

        yield AgentEvent(
            type="tool_result",
            content=result.output[:500] if result.output else "Done",
            data=result.data,
        )

        # Let LLM summarize the result
        scratchpad_copy = list(scratchpad)
        scratchpad_copy.append({
            "role": "assistant",
            "content": f"<think>The user confirmed. Executing {tool_name}.</think>\n<tool_call>{json.dumps({'tool': tool_name, 'params': tool_params})}</tool_call>",
        })
        scratchpad_copy.append({
            "role": "user",
            "content": f"<tool_result>{result.output}</tool_result>",
        })

        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + history + scratchpad_copy

        try:
            llm_response = await self._call_groq(messages)
            answer = self._extract_tag(llm_response, "answer")
            if answer:
                yield AgentEvent(type="answer", content=answer)
            else:
                clean = self._strip_tags(llm_response)
                yield AgentEvent(type="answer", content=clean)
        except Exception:
            # Fallback: just use the tool result as the answer
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

            # Retry once on rate limit
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
        cleaned = re.sub(r"</?(?:think|tool_call|tool_result|answer)>", "", text)
        return cleaned.strip()
