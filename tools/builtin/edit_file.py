from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind
from utils.paths import resolve_path

class EditFileParams(BaseModel):
    path : str = Field(
        ...,description='Path to the file to edit(relative to working directory or absolute path)'
    )

    old_string : str = Field(
        "",description="The exact text to find and replace. Must match exactly including all whitespace and indetaion. For new files, leave this empty."
    )

    new_string: str = Field(
        ...,description="The text to replace old_string with. Can be empty to delete text"
    )

    replace_all: bool = Field(
        False, description="Replace all occurance of old_string (default: false)"
    )

class EditFileTool(Tool):
    name = "edit_file"

    description = (
        "Edit a file by replacing text. The old_string must match exactly "
        "(including whitespace and indentation) and must be unique in the file "
        "unless replace_all is true. Use this for precise, surgical edits. "
        "For creating new files or complete rewrites, use write_file instead."
    )

    kind = ToolKind.WRITE
    schema = EditFileParams

    async def execute(self, invocation: ToolInvocation):
        params = invocation.params
        path = resolve_path(invocation.cwd,params.path)

        