from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import is_binary_file, resolve_path
import re
import os
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
        files = []

        for root,dirs,filenames in os.walk(search_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", "__pycache__", ".git", ".venv", "venv"}
            ]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                
                filePath = Path(root) / filename
                if not is_binary_file(filePath):
                    files.append(filePath)
                    if len(files) >= 500:
                        return files
        
        return files

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

        output_lines = []
        matches = 0
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                continue
            file_matches = False
            lines = content.splitlines()
            for i,line in enumerate(lines):
                if pattern.search(line):
                    rel_path = file_path.relative_to(invocation.cwd)
                    matches += 1
                    if not file_matches:
                        output_lines.append(f"==={rel_path}===")
                        file_matches = True
                    output_lines.append(f"{i}:{line}")

            if file_matches:
                output_lines.append("")

        if not output_lines:
            return ToolResult.success_result(
                f"No matches found for pattern {params.pattern}",
                metadata = {
                    'path':str(search_path),
                    'matches': 0
                }
            )
        return ToolResult.success_result(
            '\n'.join(output_lines),
            metadata = {
                'path':str(search_path),
                'matches': matches,
                'file_searched' : len(files)
            }
        )



