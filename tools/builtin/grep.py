from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path
import re
class GrepParams(BaseModel):
    pattern: str = Field(
        ...,description="Regular expression pattern to search for"
    )
    path: str = Field('.',description="File or directory to search in(default: current directory)")
    case_insensitive: bool = Field(False,description="Case-insensitive search (default: false)")

class GrepTool(Tool):
    name = "grep"
    kind = ToolKind.READ
    description = "Search for a regex pattern in file contents. Return matching lines with file paths and line number"
    schema = GrepParams

    def _find_files(self,search_path: Path) -> list[Path]:
        pass

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = GrepParams(**invocation.params)

        search_path = resolve_path(invocation.cwd,params.path)

        if not search_path.exists():
            return ToolResult.error_result(
                f"Path does not exist {search_path}"
            )
        try:
            flag = re.IGNORECASE if params.case_insensitive else 0
            pattern = re.compile(params.pattern,flags=flag)
        except Exception as e:
            return ToolResult.error_result(
                f"Error listing directory {e}"
            )
        
        if search_path.is_dir():
            files = self._find_files(search_path)
        else:
            files = [search_path]

        # return ToolResult.success_result(
        #     '\n'.join(lines),
        #     metadata = {
        #         'path':str(dir_path),
        #         'entries': len(lines)
        #     }
        # )



