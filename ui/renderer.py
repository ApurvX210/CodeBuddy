from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.syntax import Syntax
from config.config import Config
from utils.paths import display_path_rel_to_cwd, resolve_path
import re

from utils.text import truncate_text

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
    def __init__(self,config : Config,console : Console | None = None) -> None:
        self.console = console or get_console()
        self.config = config
        self._assistant_stream_open = False
        self._tool_args_by_call_id: dict[str,dict[str,Any]] = {}
        self.cwd = config.cwd
        self._max_block_tokens = 240

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
            'write_file' : ['path','create_directory','content'],
            'edit_file' : ['path','replace_all','old_string','new_string'],
            'shell' : ['command','timeout',"cwd"],
            'list_dir' : ['path','include_hidden'],
            'grep' : ['path','case_insensitive','pattern']
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
            if isinstance(value,str):
                if key in ['content','old_string','new_string']:
                    line_count = len(value.splitlines()) or 0
                    byte_count = len(value.encode('utf-8',errors='replace'))
                    value = f"<{line_count} lines • {byte_count}>"
            table.add_row(key,f"{value}")

        return table
    
    def print_welcome(self, title: str, lines: list[str]) -> None:
        body = "\n".join(lines)
        self.console.print(
            Panel(
                Text(body, style="code"),
                title=Text(title, style="highlight"),
                title_align="left",
                border_style="border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )


    def tool_call_start(self,call_id : str,name : str,tool_kind:str, arguments: dict[str,Any]):
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("•","muted"),
            (name,"tool"),
            (" ","muted"),
            (f"#{call_id[:8]}","muted"),
        )

        display_args = arguments
        for key in ('path','cwd'):
            val = display_args.get(key)
            if isinstance(val,str) and self.cwd:
                display_args[key] = str(display_path_rel_to_cwd(self.cwd,val))
        pannel = Panel(
            self._render_args_tab(name,arguments) if arguments else Text('(no args)',style="muted"),
            title=title,
            title_align="left",
            padding=(1,2),
            box=box.ROUNDED,
            border_style=border_style,
            subtitle=Text("running","muted"),
            subtitle_align='right'
        )

        self.console.print()
        self.console.print(pannel)

    def _extract_read_file_code(self,text: str) -> tuple[int,str] | None:
        body = text
        header_match = re.match(r"^Showing lines (\d+)-(\d+) of (\d+)\n\n",text)
        if header_match:
            body = text[header_match.end():]

        code_lines : list[str] = []
        start_line: int = None
        for line in body.splitlines():
            m = re.match(r"^\s*(\d+)\s*\|(.*)",line)
            if not m:
                continue
            line_no = int(m.group(1))
            if start_line is None:
                start_line = line_no
            code_lines.append(m.group(2))

        if start_line is None:
            return None
        
        return start_line,"\n".join(code_lines)
    
    def _guess_language(self, path: str | None) -> str:
        if not path:
            return "text"
        suffix = Path(path).suffix.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".toml": "toml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".hpp": "cpp",
            ".css": "css",
            ".html": "html",
            ".xml": "xml",
            ".sql": "sql",
        }.get(suffix, "text")

    def tool_call_complete(
                self,
                call_id : str,
                name : str,
                tool_kind:str,
                success : bool,
                output: str,
                error : str|None,
                metadata : dict[str,Any] | None,
                truncated:bool,
                diff: str | None,
                exit_code: int | None,
            ):
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"
        status_icon = "✓" if success else "✗"
        status_style = 'success' if success else 'error'

        title = Text.assemble(
            (status_icon,"status_style"),
            (name,"tool"),
            (" ","muted"),
            (f"#{call_id[:8]}","muted"),
        )

        primary_path = None
        blocks = []
        if isinstance(metadata,dict) and isinstance(metadata.get("path"),str):
            primary_path = metadata.get("path")
        
        args = self._tool_args_by_call_id.get(call_id,{})
        if name == "read_file" and success:
            if primary_path:
                start_line,code = self._extract_read_file_code(output)
                shown_start = metadata.get("shown_start")
                shown_end = metadata.get("shown_end")
                total_lines = metadata.get("shown_start")

                pl = self._guess_language(primary_path)
                blocks.append(Text())
                
                header_parts = [display_path_rel_to_cwd(primary_path,self.cwd)]
                header_parts.append(" • ")

                if shown_start and shown_end and total_lines:
                    header_parts.append(f"lines {shown_start}-{shown_end} of {total_lines}")

                header = "".join(header_parts)

                blocks.append(Text(header,style="muted"))
                blocks.append(Syntax(
                    code,
                    pl,
                    theme='monokai',
                    line_numbers=True,
                    word_wrap=False
                ))
            else:
                output_display = truncate_text(output,self.config.model_name,self._max_block_tokens)
                blocks.append(Syntax(
                    output_display,
                    "text",
                    theme='monokai',
                    word_wrap=False
                ))
        elif name in ["write_file","edit_file"] and success and diff:
            output_line = output.strip() if output.strip() else 'Completed'
            blocks.append(Text(output_line,style="muted"))
            diff_text = diff
            diff_display = truncate_text(diff_text,model=self.config.model_name,max_tokens=self._max_block_tokens)
            blocks.append(Syntax(diff_display,'diff',theme='monokai',word_wrap=True))
        elif name == "shell":
            command = args.get("command")
            if isinstance(command,str) and command.strip():
                blocks.append(Text(f'$ {command.strip()}',style='muted'))

            if exit_code is not None:
                blocks.append(Text(f"exit_code={exit_code}",style='muted'))

            output_display = truncate_text(output,self.config.model_name,self._max_block_tokens)
            blocks.append(Syntax(
                    output_display,
                    "text",
                    theme='monokai',
                    word_wrap=True
                ))
        elif name == "list_dir" and success:
            entries = metadata.get("entries")
            path = metadata.get('path')
            summary = []
            if isinstance(path,str):
                summary.append(path)
            if isinstance(entries,int):
                summary.append(f"{entries} entries")
            
            if summary:
                blocks.append(Text(" • ".join(summary),style='muted'))
            output_display = truncate_text(output,self.config.model_name,self._max_block_tokens)
            blocks.append(Syntax(
                    output_display,
                    "text",
                    theme='monokai',
                    word_wrap=True
                ))
        elif name == "grep" and success:
            path = metadata.get('path')
            matches = metadata.get("matches")
            file_searched = metadata.get("file_searched")
            summary = []
            if isinstance(path,str):
                summary.append(path)
            if isinstance(matches,int):
                summary.append(f"{matches} matches")
            if isinstance(file_searched,int):
                summary.append(f"{file_searched} file_searched")
            
            if summary:
                blocks.append(Text(" • ".join(summary),style='muted'))
            output_display = truncate_text(output,self.config.model_name,self._max_block_tokens)
            blocks.append(Syntax(
                    output_display,
                    "text",
                    theme='monokai',
                    word_wrap=True
                ))
        if truncated:
            blocks.append(Text('note: tool output was truncated',style="warning"))
        
        if error and not success:
            blocks.append(Text(error,style="error"))

            output_display = truncate_text(output,self.config.model_name,self._max_block_tokens)
            if output_display.strip():
                blocks.append(Syntax(
                        output_display,
                        "text",
                        theme='monokai',
                        word_wrap=True
                    ))
            else:
                blocks.append(Syntax(
                        Text("(No output)",style="muted"),
                        "text",
                        theme='monokai',
                        word_wrap=True
                    ))
            
        pannel = Panel(
            Group(
                *blocks
            ),
            title=title,
            title_align="left",
            padding=(1,2),
            box=box.ROUNDED,
            border_style="border",
            subtitle=Text("done" if success else "failed",style=status_style),
            subtitle_align='right'
        )

        self.console.print()
        self.console.print(pannel)