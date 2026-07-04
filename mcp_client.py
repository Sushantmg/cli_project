import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(name=tool_name, arguments=tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name: str, args: dict[str, str]):
        return await self.session().get_prompt(name=prompt_name, arguments=args)

    async def read_resource(self, uri: str) -> Any:
        return await self.session().read_resource(uri=uri)

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# For testing
async def main():
    async with MCPClient(
        command="python",
        args=["-u", "mcp_server.py"],  # Forces unbuffered stream interaction
    ) as client:
        print("\n--- Testing Connection and Discovery ---")
        
        # 1. Test Tools Listing
        tools = await client.list_tools()
        print(f"Discovered Tools: {[t.name for t in tools]}")
        
        # 2. Test Calling the newly renamed 'read_doc_contents' Tool
        print("\nCalling tool 'read_doc_contents'...")
        tool_res = await client.call_tool("read_doc_contents", {"doc_id": "report.pdf"})
        if tool_res and hasattr(tool_res, 'content') and tool_res.content:
            print(f"Tool Execution Result: {tool_res.content[0].text}")
        else:
            print("Tool Execution returned no content.")
            
        # 3. Test Calling the newly renamed 'edit_document' Tool
        print("\nCalling tool 'edit_document' (Modifying report.pdf)...")
        edit_res = await client.call_tool(
            "edit_document", 
            {
                "doc_id": "report.pdf", 
                "old_str": "20m condenser tower", 
                "new_str": "45m upgraded cooling tower"
            }
        )
        if edit_res and hasattr(edit_res, 'content') and edit_res.content:
            print(f"Tool Execution Result: {edit_res.content[0].text}")
            
            # Re-read to prove it actually updated in the server's memory!
            verify_res = await client.call_tool("read_doc_contents", {"doc_id": "report.pdf"})
            print(f"Verified Updated Content: {verify_res.content[0].text}")
        
        # 4. Test Resources Loading
        print("\nFetching resource 'docs://list'...")
        resource_res = await client.read_resource("docs://list")
        if resource_res and hasattr(resource_res, 'contents') and resource_res.contents:
            print(f"Resource Retrieval Layout:\n{resource_res.contents[0].text}")
        
        print("\n--- Testing Complete. Cleaning up channels... ---")
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())