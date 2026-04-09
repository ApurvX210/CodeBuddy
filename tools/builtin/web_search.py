from ddgs import DDGS
from pydantic import BaseModel, Field

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult

class WebSearchParams(BaseModel):
    query: str = Field(
        ...,description="Search Query"
    )
    max_results: int = Field(
        10,ge=1,le=20,description="Maximum result to return (default: 10)"
    )

class WebSearchTool(Tool):
    name = "web_search"
    kind = ToolKind.NETWORK
    description = "Search the web for information. Return search result with titles, URLs and snippets"
    schema = WebSearchParams

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


