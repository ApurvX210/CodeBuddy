import asyncio
import fnmatch
import os
from pathlib import Path
import sys

from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult

BLOCKED_COMMANDS = {
    "rm -rf /",
    "rm -rf ~",
    "rm -rf /*",
    "dd if=/dev/zero",
    "dd if=/dev/random",
    "mkfs",
    "fdisk",
    "parted",
    ":(){ :|:& };:",  # Fork bomb
    "chmod 777 /",
    "chmod -R 777",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
}

class ShellParams(BaseModel):
    command : str = Field(
        ...,description="The shell command to execute"
    )
    timeout: int = Field(
        120, ge=1,le=60,description="Timeout in second (default: 120)"
    )
    cwd: str | None = Field(None,description="Working directory for the command")

class ShellTool(Tool):
    name = "shell"
    kind = ToolKind.SHELL
    description = "Execute a shell command. Use this for runnning system commands, scripts and CLI tools."

    schema = ShellParams

    def _build_environment(self) -> dict[str,str]:
        env = os.environ.copy()
        shell_env = self.config.shell_environment

        if not shell_env.ignore_default_excludes:
            for pattern in shell_env.exclude_pattern:
                keys_to_remove = [key for key in env.keys() if fnmatch.fnmatch(key.upper(),pattern.upper())]
            
                for k in keys_to_remove:
                    del env[k]

        if shell_env.set_vars:
            env.update(shell_env.set_vars)

        return env

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ShellParams(**invocation.params)

        command = params.command.lower().strip()
        for blocked in BLOCKED_COMMANDS:
            if blocked in command:
                return ToolResult.error_result(
                    f"Command blocked for safety: {command}",
                    metadata={'blocked':True}
                )
            
        if params.cwd:
            cwd = Path(params.cwd)
            if not cwd.is_absolute():
                cwd = invocation.cwd / cwd
        else:
            cwd = invocation.cwd

        if not cwd.exists():
            return ToolResult.error_result(
                f"Working directory doesn't exist: {cwd}"
            )

        env = self._build_environment()
        if sys.platform == 'win32':
            shell_cmd = ['cmd.exe','/c',params.command]
        else:
            shell_cmd = ['/bin/bash','-c',params.command]
        

        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd = cwd,
            env=env,
            start_new_session=True
        )

        try:
            stdout_data,stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=params.timeout
            )
        except asyncio.TimeoutError:
            if sys.platform != 'win32':
                os.killpg(os.getpid(process.pid),signal.SIGKILL)
            else:
                process.kill()

            await process.wait()
            return ToolResult.error_result(
                f"Command time out after {params.timeout}"
            )
        
        stdout = stdout_data.decode('utf-8',errors='replace')
        stderr = stderr_data.decode('utf-8',errors='replace')
        exit_code = process.returncode

        output = ""
        if stdout.strip():
            output += stdout.rstrip()

        if stderr.strip():
            output += '\n---stderr---\n'
            output += stdout.rstrip()

        if exit_code != 0:
            output += f"\nExit Code: {exit_code}"

        if len(output) > 100*1024:
            output = output[:100*1024] + '\n... [output truncated]'

        return ToolResult(
            success=exit_code==0,
            error=stderr if exit_code != 0 else None,
            exit_code=exit_code,
            output=output
        )
        