import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.types import CreateMessageResult, TextContent

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

    async def sampling_callback(self, context: Any, params: Any) -> CreateMessageResult:
        """
        Intercepts sampling requests sent from the server, runs them through 
        your local free Ollama engine, and sends the answer back to the server.
        """
        print("\n[MCP Client] Intercepted an Agentic Sampling request from the server...")
        
        # Pull incoming prompt text safely
        incoming_prompt = ""
        if hasattr(params, "messages") and params.messages:
            incoming_prompt = params.messages[0].content.text
        elif isinstance(params, dict) and "messages" in params:
            incoming_prompt = params["messages"][0]["content"]["text"]

        print("[MCP Client] Forwarding sampled request to local Llama model...")
        try:
            import ollama
            # Call your local offline engine for free
            response = ollama.chat(
                model='llama3.2', 
                messages=[{'role': 'user', 'content': incoming_prompt}]
            )
            ai_response = response['message']['content']
        except Exception as e:
            print(f"[MCP Client] Local model call failed: {e}")
            ai_response = "Local processing error fallback wrapper."

        return CreateMessageResult(
            role="assistant",
            model="local-llama3.2",
            content=TextContent(type="text", text=ai_response),
        )

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
            ClientSession(_stdio, _write, sampling_callback=self.sampling_callback)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("Client session not initialized. Call connect first.")
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, tool_input: dict) -> types.CallToolResult | None:
        return await self.session().call_tool(name=tool_name, arguments=tool_input)

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# Production Integration Test Block
async def main():
    async with MCPClient(
        command="python",
        args=["-u", "mcp_server.py"],
    ) as client:
        print("\n--- Testing Live Sampling Architecture (Ollama) ---")
        tools = await client.list_tools()
        print(f"Discovered Tools: {[t.name for t in tools]}")
        
        if "summarize" in [t.name for t in tools]:
            print("\nExecuting agentic sampling test string on 'summarize'...")
            
            test_paragraph = (
                "The Model Context Protocol (MCP) is an open standard that enables developers to build "
                "secure, bidirectional connections between AI models and data sources. It simplifies "
                "integrations by using standardized JSON-RPC architectures over simple transports."
            )
            
            res = await client.call_tool("summarize", {"text_to_summarize": test_paragraph})
            if res and hasattr(res, 'content') and res.content:
                print(f"\nFinal Tool Output Result From Server:\n{res.content[0].text}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())