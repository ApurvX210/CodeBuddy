from pathlib import Path
from typing import Any

from rich.console import Console
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from utils.paths import display_path_rel_to_cwd, resolve_path

AGENT_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bright_red bold",
        "success": "green",
        "dim": "dim",
        "muted": "grey50",
        "border": "grey35",
        "highlight": "bold cyan",
        "user": "bright_blue bold",
        "assistant": "bright_white",
        "tool": "bright_magenta bold",
        "tool.read": "cyan",
        "tool.write": "yellow",
        "tool.shell": "magenta",
        "tool.network": "bright_blue",
        "tool.memory": "green",
        "tool.mcp": "bright_cyan",
        "code": "white",
    }
)

_console: Console | None = None

def get_console() -> Console:
    global _console
    if _console is None:
        _console = Console(theme=AGENT_THEME)

    return _console

class AgentUI:
    def __init__(self,console : Console | None = None) -> None:
        self.console = console or get_console()
        self._assistant_stream_open = False
        self._tool_args_by_call_id: dict[str,dict[str,Any]] = {}
        self.cwd = Path.cwd()

    def begin_assistant(self):
        self.console.print()
        self.console.print(Rule(Text("Assistent",style='assistant')))
        self._assistant_stream_open = True

    def end_assistant(self):
        if self._assistant_stream_open:
            self.console.print()
            self.console.print(Rule(Text("Assistent Response Ends",style='assistant')))
            self._assistant_stream_open = False

    def stream_assistant_delta(self,content: str):
        self.console.print(content,end="",markup=False)

    def _ordered_args(self,tool_name:str,args:dict[str,Any]) -> list[tuple]:
        _PREFERRED_ORDER = {
            'read_file' : ['path','offset','limit'],
        }

        prefered = _PREFERRED_ORDER.get(tool_name,[])
        order :list[tuple[str,Any]] = []
        seen = set()
        for key in prefered:
            if key in prefered:
                order.append((key,args.get(key,"None")))
                seen.add(key)

        remaining_keys = set(args.keys()) - seen
        for key in remaining_keys:
            order.append((key,args[key]))

        return order

    def _render_args_tab(self,tool_name:str,args:dict[str,Any]) -> Table:
        table = Table.grid(padding=(0,1))
        table.add_column(style="muted",justify="left",no_wrap=True)
        table.add_column(style="code",overflow="fold")

        for key,value in self._ordered_args(tool_name,args):
            table.add_row(key,value)

        return table


    def tool_call_start(self,call_id : str,name : str,tool_kind:str, arguments: dict[str,Any]):
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("*","muted"),
            (name,"tool"),
            (" ","muted"),
            (f"#{call_id}","muted"),
        )

        display_args = arguments
        for key in ('path','cwd'):
            val = display_args.get(key)
            if isinstance(val,str) and self.cwd:
                display_args[key] = str(display_path_rel_to_cwd(self.cwd,val))
        pannel = Panel(
            self._render_args_tab(name,arguments) if arguments else Text('(no args)',style="muted"),
            title=title,
            padding=(1,2),
            box=box.ROUNDED,
            border_style="border",
            subtitle=Text("running","muted"),
            subtitle_align='right'
        )

        self.console.print()
        self.console.print(pannel)

    def tool_call_complete(self,call_id : str,name : str,success : bool, output: str, error : str|None,metadata : dict[str,Any] | None,truncated:bool):
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("*","muted"),
            (name,"tool"),
            (" ","muted"),
            (f"#{call_id}","muted"),
        )

        display_args = arguments
        for key in ('path','cwd'):
            val = display_args.get(key)
            if isinstance(val,str) and self.cwd:
                display_args[key] = str(display_path_rel_to_cwd(self.cwd,val))
        pannel = Panel(
            self._render_args_tab(name,arguments) if arguments else Text('(no args)',style="muted"),
            title=title,
            padding=(1,2),
            box=box.ROUNDED,
            border_style="border",
            subtitle=Text("running","muted"),
            subtitle_align='right'
        )

        self.console.print()
        self.console.print(pannel)