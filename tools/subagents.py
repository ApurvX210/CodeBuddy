import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel,Field

from agent.agent import Agent
from agent.events import AgentEvent
from config.config import Config
from tools.base import Tool, ToolInvocation, ToolResult

class SubAgentParams(BaseModel):
    goal : str = Field(
        ...,description="Goal of the Agent"
    )

@dataclass
class SubagentDefinition:
    name : str #sunagent_name
    description : str
    goal_prompt: str
    allowed_tools: list[str] | None = None
    max_turns: int = 20
    timeout_second: float = 600

class SubAgentTool(Tool):
    def __init__(self, config: Config,definition: SubagentDefinition):
        super().__init__(config)
        self.definition = definition

    @property
    def name(self) -> str:
        return f"subagent_{self.definition.name}"
    
    @property
    def description(self) -> str:
        return f"subagent_{self.definition.description}"
    
    schema = SubAgentParams

    def is_mutating(self, params: dict[str,Any]) -> bool:
        return True
    
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = SubAgentParams(**invocation.params)

        if not params.goal:
            return ToolResult.error_result(
                f"No goal was specified here for sub-agent as well"
            )
        
        config_dict = self.config.to_dict()
        config_dict["max_turn"] = self.definition.max_turns
        if self.definition.allowed_tools:
            config_dict["allowed_tools"] = self.definition.allowed_tools

        subagent_config = Config(**config_dict)

        prompt = f"""You are a specialized sub-agent with a specific task to complete.

        {self.definition.goal_prompt}

        YOUR TASK:
        {params.goal}

        IMPORTANT:
        - Focus only on completing the specified task
        - Do not engage in unrelated actions
        - Once you have completed the task or have the answer, provide your final response
        - Be concise and direct in your output
        """
        tool_calls = []
        final_response = None
        error = None
        terminate_response = 'goal'
        try:
            async with Agent(config=subagent_config) as agent:
                deadline = asyncio.get_event_loop().time() + self.definition.timeout_second
                async for event in agent.run(prompt):
                    if asyncio.get_event_loop().time() > deadline:
                        terminate_response = 'timeout'
                        final_response = f"Sub-agent timeout"
                        break

                    if event.type == AgentEvent.tool_call_start:
                        tool_calls.append(event.data.get("name"))
                    elif event.type == AgentEvent.text_complete:
                        final_response = event.data.get('content')
                    elif event.type == AgentEvent.agent_error:
                        terminate_response = "error"
                        error = event.data.get('error',"Unknown")
                        final_response = f"Sub-agent error: {error}"
                        break
        except Exception as e:
            terminate_response = "error"
            error = str(e)
            final_response = f"Sub-agent fail: {e}"

        result = f"""Sub-agent '{self.definition.name}' completed.
        Termination: {terminate_response}
        Tools called: {', '.join(tool_calls) if tool_calls else 'None'}
        Result:
        {final_response or "None"}
        """

        if error:
            return ToolResult.error_result(result)
        
        return ToolResult.success_result(result)
    
CODEBASE_INVESTIGATOR = SubagentDefinition(
    name="codebase_investigator",
    description="Investigates the codebase to answer questions about code structure, patterns, and implementations",
    goal_prompt="""You are a codebase investigation specialist.
Your job is to explore and understand code to answer questions.
Use read_file, grep, glob, and list_dir to investigate.
Do NOT modify any files.""",
    allowed_tools=["read_file", "grep", "glob", "list_dir"],
)

CODE_REVIEWER = SubagentDefinition(
    name="code_reviewer",
    description="Reviews code changes and provides feedback on quality, bugs, and improvements",
    goal_prompt="""You are a code review specialist.
Your job is to review code and provide constructive feedback.
Look for bugs, code smells, security issues, and improvement opportunities.
Use read_file, list_dir and grep to examine the code.
Do NOT modify any files.""",
    allowed_tools=["read_file", "grep", "list_dir"],
    max_turns=10,
    timeout_seconds=300,
)

def get_all_subagents_definitions() -> list[SubagentDefinition]:
    return [
        CODEBASE_INVESTIGATOR,
        CODE_REVIEWER
    ]
