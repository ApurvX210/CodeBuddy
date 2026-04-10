from ddgs import DDGS
from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult

class TodosParams(BaseModel):
    action: str = Field(
        ...,description="Action: 'add','complete','list','clear'"
    )
    id: str | None = Field(None, description="Todo Id (for complete)")
    content: str | None = Field(None, description="Todo content (for add)")

class TodosTool(Tool):
    name = "web_search"
    kind = ToolKind.MEMORY
    description = "Manage a task list of current session. Use this to track progress on multi-steps complex task."
    schema = TodosParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebSearchParams(**invocation.params)

        try:
            results = DDGS().text(params.query, region='us-en', safesearch='off', timelimit='y', page=1, backend="auto")
        except Exception as e:
            return ToolResult.error_result(f"Searched failed: {e}")
        
        if not results:
            return ToolResult.success_result(f"No result found for: {params.query}",metadata = {
                "results": 0,
            })
        
        output_lines = [f"Search results for :{params.query}"]

        for i,result in enumerate(results,start=1):
            output_lines.append(f"{i}. Title: {result['title']}")
            output_lines.append(f"   URL: {result['href']}")
            if result.get('body'):
                output_lines.append(f"   Snippets: {result['body']}")

            output_lines.append("")

        return ToolResult.success_result(
            '\n'.join(output_lines),
            metadata = {
                "results": len(results),
            }
        )


