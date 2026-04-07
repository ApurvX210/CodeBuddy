from tools.base import Tool
from tools.builtin.read_file import ReadFileTool
from tools.builtin.write_file import WriteFileTool
from tools.builtin.edit_file import EditFileTool

__all__ = [
    'ReadFileTool'
]

def get_all_builtin_tool() -> list[Tool]:
    return [
        ReadFileTool,
        WriteFileTool,
        EditFileTool
    ]
