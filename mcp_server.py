from mcp.server.fastmcp import FastMCP, Context
from mcp.types import SamplingMessage, TextContent
from pydantic import Field  # Essential for using the Field decorator arguments
# Initialize FastMCP server instance
mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# 1. Updated Tool to read doc contents using explicit Pydantic Fields
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document(
    doc_id: str = Field(..., description="Id of the document to read")
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]

# 2. Updated Tool to edit a document with find-and-replace using Fields
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string."
)
def edit_document(
    doc_id: str = Field(..., description="Id of the document that will be edited"),
    old_str: str = Field(..., description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(..., description="The new text to insert in place of the old text.")
) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
    return f"Success: Document '{doc_id}' updated successfully."

# 3. Resource to return all doc IDs
@mcp.resource("docs://documents")
def list_doc_ids() -> str:
    """Returns a list of all available document IDs in the registry."""
    return "\n".join(docs.keys())

# 4. Resource to return the contents of a particular doc
@mcp.resource("docs://documents/{doc_id}")
def get_doc_content(doc_id: str) -> str:
    """Fetches the raw, static content of a specific document registry item."""
    if doc_id in docs:
        return docs[doc_id]
    return f"Document '{doc_id}' not found."

# 5. Prompt to rewrite a doc in markdown format
@mcp.prompt()
def rewrite_to_markdown(doc_id: str) -> str:
    """Generates a prompt instructions layout to convert a target document into valid Markdown formatting."""
    content = docs.get(doc_id, f"[Document '{doc_id}' not found]")
    return f"Please rewrite the following document text into beautifully formatted Markdown, preserving all technical details:\n\n{content}"

# 6. Prompt to summarize a doc
@mcp.prompt()
def summarize_doc(doc_id: str) -> str:
    """Generates a structured prompt command telling an LLM to outline and summarize a document."""
    content = docs.get(doc_id, f"[Document '{doc_id}' not found]")
    return f"Please provide a concise high-level summary and bulleted key takeaways for this document:\n\n{content}"

# 7. Advanced Agentic Sampling Tool to summarize text using the LLM session context
@mcp.tool()
async def summarize(text_to_summarize: str, ctx: Context) -> str:
    """Uses Agentic Sampling to let the host AI summarize any raw input block of text."""
    prompt = f"""
Please summarize the following text:
{text_to_summarize}
"""

    # Ask the host AI model via the current active session to process the summary
    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=prompt.strip()
                )
            )
        ],
        max_tokens=4000,
        system_prompt="You are a helpful research assistant.",
    )

    # Validate and return the response text cleanly
    if hasattr(result.content, "text"):
        return result.content.text
    elif isinstance(result.content, dict) and "text" in result.content:
        return result.content["text"]
    else:
        raise ValueError("Sampling response did not contain expected text content.")

if __name__ == "__main__":
    mcp.run(transport="stdio")