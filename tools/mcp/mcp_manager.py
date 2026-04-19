import asyncio

from config.config import Config
from tools.mcp.client import MCPClient, MCPServerStatus
from tools.mcp.mcp_tool import MCPTool
from tools.registery import ToolRegistery


class MCPManager:
    def __init__(self,config: Config):
        self.config = config
        self._clients : dict[str,MCPClient] = {}
        self._initialized = False

    async def initialized(self) -> None:
        if self._initialized:
            return


        mpc_config = self.config.mcp_servers

        if not mpc_config:
            return
        
        for name,server_config in mpc_config.items():
            if not server_config.enabled:
                continue

            self._clients[name] = MCPClient(
                name=name,
                config=server_config,
                cwd=self.config.cwd
            )

        connection_task = [asyncio.wait_for(client.connect(),timeout=client.config.startup_timeout_sec) for name,client in self._clients.items()]
        
        await asyncio.gather(*connection_task,return_exceptions=True)

        self._initialized = True

    def register_tools(self, registry: ToolRegistery) -> int:
        count = 0

        for client in self._clients.values():
            if client.status != MCPServerStatus.CONNECTED:
                continue

            for tool_info in client.tools:
                mcp_tool = MCPTool(
                    tool_info=tool_info,
                    client=client,
                    config=self.config,
                    name=f"{client.name}__{tool_info.name}",
                )
                registry.register_mcp_tool(mcp_tool)
                count += 1

        return count
    
    async def shutdown(self) -> None:
        disconnection_tasks = [client.disconnect() for client in self._clients.values()]

        await asyncio.gather(*disconnection_tasks, return_exceptions=True)

        self._clients.clear()
        self._initialized = False

    def get_all_servers(self) -> list[dict[str, Any]]:
        servers = []
        for name, client in self._clients.items():
            server_info = {
                "name": name,
                "status": client.status.value,
                "tools": len(client.tools),
            }
            servers.append(server_info)

        return servers