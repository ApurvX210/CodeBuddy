from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path,is_binary_file
from utils.text import count_token

class ReadFileParams(BaseModel):
    path : str = Field(
        ...,description='Path to the file to read (related to working directory or absolute)'
    )

    offset : int = Field(1, ge=1,description='Line number to start reading from from (1-nased). Default to 1')

    limit : int | None = Field(
        None,
        ge=1,
        description='Maximum number of line to read. If not specified read entire file'
    )

class ReadFileTool(Tool):
    name = 'read_file'
    description = (
        "Read the content of a text file. Return the file content with line numbers."
        "For large files, use offset and limit to read specific portion."
        "cannot read binary files (image,executable,etc.)."
    )
    kind = ToolKind.READ

    schema = ReadFileParams

    MAX_FILE_SIZE = 1024 * 1024 * 10

    MAX_OUTPUT_TOKENS = 25000

    async def execute(self, invocation : ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)

        path = resolve_path(invocation.cwd,params.path)

        if not path.exists():
            return ToolResult.error_result(
                error=f"File not found : {path}"
            )
        
        if not path.is_file():
            return ToolResult.error_result(
                error=f"Path is not a file : {path}"
            )
        
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            return ToolResult.error_result(
                f"File to large ({file_size/(1024*1024):.1f}MB)."
                f"Maximum is {self.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        if is_binary_file(path):
            file_size_mb = file_size / (1024 * 1024)
            size_str = f"{file_size_mb:2f} MB" if file_size_mb >= 1 else f"{file_size} bytes"
            return ToolResult.error_result(
                f"Cannot read Binary file {path.name}. ({size_str})"
                f"This tool only reads text files."
            )
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='latin-1')

        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return ToolResult.success_result(
                "File is empty.",
                metadata={
                    "Lines" : 0,
                }
            )
        
        start_idx = max(0,params.offset - 1)
        end_idx = None
        if params.limit is not None:
            end_idx = min(start_idx + params.limit,total_lines)
        else:
            end_idx = total_lines

        selected_lines = lines[start_idx:end_idx]
        formatted_line = []

        for i,line in enumerate(selected_lines,start=start_idx+1):
            formatted_line.append(f"{i:6} | {line}")

        output = "\n".join(formatted_line)
        token_count = count_token(output)

        if token_count > self.MAX_OUTPUT_TOKENS:
            output = []