from pydantic import BaseModel,Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult


class WriteFileParams(BaseModel):
    path : str = Field(
        ...,description='Path to the file to write (relative to the working directory or absolute)'
    )
    content: str = Field(...,description="Content to write to the file")
    create_directory : bool = Field(
        True,description="Create Parent directory if it doesnt exist"
    )

class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Write content to a file. Creates the file if it doesn't exist, "
        "or overwrites if it does. Parent directories are created automatically. "
        "Use this for creating new files or completely replacing file contents. "
        "For partial modifications, use the edit tool instead."
    )
    kind = ToolKind.WRITE
    schema = WriteFileParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        return await super().execute(invocation)