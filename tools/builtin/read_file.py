from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path,is_binary_file

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