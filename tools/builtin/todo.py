import uuid

from ddgs import DDGS
from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult

class TodosParams(BaseModel):
    action: str = Field(
        ...,description="Action: 'add','complete','list','clear'"
    )
    id: str | None = Field(None, description="Todo Id (for complete)")
    content: str | None = Field(None, description="Todo content (for add)")

class TodosTool(Tool):
    name = "todos"
    kind = ToolKind.MEMORY
    description = "Manage a task list of current session. Use this to track progress on multi-steps complex task."
    schema = TodosParams

    def __init__(self, config):
        super().__init__(config)
        self._todos: dict[str,str] = {}

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = TodosParams(**invocation.params)

        action = params.action

        match action.lower():
            case "add":
                if not params.content:
                    ToolResult.error_result(
                        f"content is required for add action"
                    )
                todoId = str(uuid.uuid4())[:8]
                self._todos[todoId] = params.content
                return ToolResult.success_result(
                    f"Added todo [{todoId} : {params.content}]"
                )
            case "complete":
                if not params.id:
                    ToolResult.error_result(
                        f"`id` is required for `complete` action"
                    )

                if params.id not in  self._todos:
                    return ToolResult.error_result(
                        f"Todo not found: {params.id}"
                    )

                content = self._todos.pop(params.id)
                return ToolResult.success_result(
                    f"Completed the todo [{params.id} : {content}]"
                )
            case "list":
                if not self._todos:
                    return ToolResult.success_result(
                        f"No todos are left"
                    )
                
                lines = ['Todos:']
                for todo_id,content in self._todos.items():
                    lines.append(f" [{todo_id} : {content}]")

                return ToolResult.success_result(
                    "\n".join(lines)
                )
            case "clear":
                count = len(self._todos)
                self._todos.clear()
                return ToolResult.success_result(
                    f"Cleared {count} todo"
                )
            case _:
                return ToolResult.error_result(f"Unkown action: {params.action}")

