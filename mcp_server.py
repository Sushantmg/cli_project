from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server instance matching your variable name 'mcp'
mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

# 1. Tool to read a doc
@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read the content of a specific document by its ID."""
    if doc_id in docs:
        return docs[doc_id]
    return f"Error: Document '{doc_id}' not found."

# 2. Tool to edit a doc
@mcp.tool()
def edit_doc(doc_id: str, content: str) -> str:
    """Edit or update the content of an existing document or create a new one."""
    docs[doc_id] = content
    return f"Success: Document '{doc_id}' updated successfully."

# 3. Resource to return all doc IDs
@mcp.resource("docs://list")
def list_doc_ids() -> str:
    """Returns a list of all available document IDs in the registry."""
    return "\n".join(docs.keys())

# 4. Resource to return the contents of a particular doc
@mcp.resource("docs://item/{doc_id}")
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


if __name__ == "__main__":
    mcp.run(transport="stdio")