from tools.base import Tool
from tools.builtin.read_file import ReadFileTool

__all__ = [
    'ReadFileTool'
]

def get_all_builtin_tool() -> list[Tool]:
    return [
        ReadFileTool
    ]
