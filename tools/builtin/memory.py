import json
import uuid

from ddgs import DDGS
from pydantic import BaseModel, Field

from config.loader import get_data_dir
from tools.base import Tool, ToolInvocation, ToolKind, ToolResult

class MemoryParams(BaseModel):
    action: str = Field(
        ...,description="Action: 'set','get','delete','list','clear'"
    )
    key: str | None = Field(None, description="Memory key (required for set,get and delete)")
    value: str | None = Field(None, description="Value to store (required for `set`)")

class MemoryTool(Tool):
    name = "todos"
    kind = ToolKind.MEMORY
    description = "Store and retrieve persistent memory. Use this to remember user preferences., important context or notes"
    schema = MemoryParams

    def _load_memory(self) -> dict:
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True,exist_ok=True)
        path = data_dir / "user_memory.json"

        if not path.exists():
            return {
                'entries' :{}
            }
        
        try:
            content = path.read_text(encoding='utf-8')
            return json.loads(content)
        except Exception as e:
            return {
                'entries' :{}
            } 
        
    def _save_memory(self, memory: dict):
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True,exist_ok=True)
        path = data_dir / "user_memory.json"

        path.write_text(json.dumps(memory,indent=2,ensure_ascii=False))
    
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = MemoryParams(**invocation.params)

        action = params.action

        match action.lower():
            case "set":
                if not params.key or not params.value:
                    ToolResult.error_result(
                        f"`key` and `value` are required for set action"
                    )
                memory = self._load_memory()
                memory['entries'][params.key] = params.value

                self._save_memory(memory=memory)
                return ToolResult.success_result(
                    f"set memory [{params.key}]"
                )
            case "get":
                if not params.key:
                    ToolResult.error_result(
                        f"`key` is required for `get` action"
                    )
                
                memory = self._load_memory()
                if params.key not in  memory['entries']:
                    return ToolResult.error_result(
                        f"Memory not found: {params.key}"
                    )

                value = memory['entries'][params.key]
                return ToolResult.success_result(
                    f"Memory found : [{params.key} : {value}]"
                )
            case "delete":
                if not params.key:
                    ToolResult.error_result(
                        f"`key` is required for `delete` action"
                    )
                
                memory = self._load_memory()
                if params.key not in  memory['entries']:
                    return ToolResult.error_result(
                        f"Memory not found: {params.key}"
                    )

                del memory['entries'][params.key]
                self._save_memory(memory=memory)
                return ToolResult.success_result(
                    f"Memory found : [{params.key} : {value}]"
                )
            case "list":
                memory = self._load_memory()
                entries = memory.get("entries",{})
                if not entries:
                    return ToolResult.success_result(
                        f"No Memory stored"
                    )
                
                lines = ['Stored Memories:']
                for key,value in entries.items():
                    lines.append(f" [{key} : {value}]")

                return ToolResult.success_result(
                    "\n".join(lines)
                )
            case "clear":
                memory = self._load_memory()
                count = len(memory.get('entries',{}))
                memory['entries'] = {}
                return ToolResult.success_result(
                    f"Cleared {count} todo"
                )
            case _:
                return ToolResult.error_result(f"Unkown action: {params.action}")

