from anthropic.types import Message, TextBlock, ToolUseBlock

class Claude:
    def __init__(self, model: str):
        # Removed self.client = Anthropic() so it never looks for a real API key
        self.model = model

    def add_user_message(self, messages: list, message):
        user_message = {
            "role": "user",
            "content": message.content if isinstance(message, Message) else message,
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        assistant_message = {
            "role": "assistant",
            "content": message.content if isinstance(message, Message) else message,
        }
        messages.append(assistant_message)

    def text_from_message(self, message: Message):
        return "\n".join(
            [block.text for block in message.content if block.type == "text"]
        )

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ) -> Message:
        """
        MOCK CHAT ENVIRONMENT
        This intercepts the requests completely locally and simulates Claude's responses
        without needing any internet or Anthropic API credentials.
        """
        # 1. Get the last text message typed by the user
        last_message = messages[-1]["content"] if messages else ""
        user_query = ""
        
        if isinstance(last_message, list):
            # If the last message contains structured blocks (like tool results)
            for block in last_message:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    # Simulate Claude summarizing the tool data
                    mock_content = [
                        TextBlock(
                            text=f"[MOCK CLAUDE RESPONSE]\nI evaluated the tool outcome data you provided. The document data states:\n\n\"{block.get('content')}\"",
                            type="text"
                        )
                    ]
                    return Message(id="mock_msg_id", content=mock_content, role="assistant", stop_reason="end_turn", model=self.model, type="message", usage={"input_tokens": 0, "output_tokens": 0})
        else:
            user_query = str(last_message).lower()

        # 2. Simulate tool triggers depending on what keyword the user typed
        if "report.pdf" in user_query:
            # Fake a tool trigger requesting the tool 'read_doc_contents'
            mock_content = [
                TextBlock(text="Let me look into the document system registry to fetch that file content...", type="text"),
                ToolUseBlock(id="mock_tool_use_id", input={"doc_id": "report.pdf"}, name="read_doc_contents", type="tool_use")
            ]
            return Message(id="mock_msg_id", content=mock_content, role="assistant", stop_reason="tool_use", model=self.model, type="message", usage={"input_tokens": 0, "output_tokens": 0})
            
        elif "list" in user_query or "files" in user_query:
            mock_content = [
                TextBlock(text="I can see you want a resource file inventory summary. Let me scan the server paths.", type="text")
            ]
            return Message(id="mock_msg_id", content=mock_content, role="assistant", stop_reason="end_turn", model=self.model, type="message", usage={"input_tokens": 0, "output_tokens": 0})

        # 3. Default fallback text response
        mock_content = [
            TextBlock(
                text=f"[MOCK CLAUDE] You said: '{last_message}'. To run tools, try asking: 'What is inside report.pdf?'",
                type="text"
            )
        ]
        return Message(id="mock_msg_id", content=mock_content, role="assistant", stop_reason="end_turn", model=self.model, type="message", usage={"input_tokens": 0, "output_tokens": 0})