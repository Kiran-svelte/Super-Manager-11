"""
Document Generation Tool
=========================
Creates downloadable text, CSV, JSON, or markdown files.
Returns as base64 data URI for client-side download.
No server storage needed.
"""

import base64
import json as json_module

from .base import Tool, ToolResult


class DocumentTool(Tool):
    name = "generate_document"
    description = "Create a downloadable document file (text, CSV, JSON, or markdown). The file will be available for the user to download."
    parameters = {
        "content": {
            "description": "The document content (text, CSV rows, JSON data, or markdown)",
            "required": True,
            "type": "string",
        },
        "filename": {
            "description": "Desired filename with extension (e.g. 'report.txt', 'data.csv', 'config.json', 'notes.md')",
            "required": True,
            "type": "string",
        },
    }
    requires_confirmation = False

    async def execute(self, **params) -> ToolResult:
        content = params.get("content", "")
        filename = params.get("filename", "document.txt")

        if not content:
            return ToolResult(
                success=False,
                output="No content provided for the document.",
                error="missing_content",
            )

        # Determine MIME type from extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        mime_types = {
            "txt": "text/plain",
            "csv": "text/csv",
            "json": "application/json",
            "md": "text/markdown",
            "html": "text/html",
            "xml": "text/xml",
        }
        mime_type = mime_types.get(ext, "text/plain")

        # Validate JSON if .json extension
        if ext == "json":
            try:
                json_module.loads(content)
            except json_module.JSONDecodeError:
                # Try to wrap as valid JSON
                try:
                    content = json_module.dumps(json_module.loads(f'[{content}]'), indent=2)
                except Exception:
                    pass  # Leave as-is, user can fix

        # Create base64 data URI
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{encoded}"
        size_bytes = len(content.encode("utf-8"))

        # Format size
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        return ToolResult(
            success=True,
            output=f"Document '{filename}' created ({size_str}).",
            data={
                "filename": filename,
                "size": size_bytes,
                "size_str": size_str,
                "mime_type": mime_type,
                "ui_components": {
                    "type": "file_download",
                    "url": data_uri,
                    "filename": filename,
                    "size": size_str,
                    "mime_type": mime_type,
                },
            },
        )
