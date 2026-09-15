"""
FastAPI REST API Server for the API Documentation Agent.
Exposes endpoints for code analysis, doc generation, zip project processing, file export, and static SPA serving.
"""

import io
import os
import zipfile
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.parsers.base import EndpointInfo
from backend.parsers.manager import ParserManager
from backend.generator.template_gen import TemplateDocGenerator
from backend.generator.ai_gen import AIDocGenerator
from backend.generator.exporter import DocExporter

app = FastAPI(
    title="API Documentation Agent",
    description="Automated multi-framework API endpoint extraction and documentation generator.",
    version="1.0.0",
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser_manager = ParserManager()
template_generator = TemplateDocGenerator()
exporter = DocExporter()


class CodeAnalysisRequest(BaseModel):
    code: str
    filename: str = "app.py"
    framework: Optional[str] = "auto"


class GenerateRequest(BaseModel):
    endpoints: List[EndpointInfo]
    api_key: Optional[str] = None
    mode: str = "template"  # "template" or "ai"


class FullPipelineRequest(BaseModel):
    code: Optional[str] = None
    filename: str = "app.py"
    framework: Optional[str] = "auto"
    api_key: Optional[str] = None
    mode: str = "template"


@app.get("/api/health")
def health_check():
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {
        "status": "healthy",
        "parsers": ["fastapi", "flask", "express"],
        "anthropic_key_configured": api_key_set,
        "default_mode": "ai" if api_key_set else "template",
    }


@app.post("/api/analyze")
async def analyze_code(
    request: Optional[CodeAnalysisRequest] = None,
    file: Optional[UploadFile] = File(None),
    framework: Optional[str] = Form("auto"),
):
    """
    Parses single file or uploaded zip archive and extracts endpoints.
    """
    files_to_process: Dict[str, str] = {}

    if file:
        filename = file.filename or "uploaded_file"
        content_bytes = await file.read()

        if filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
                    for zip_info in zf.infolist():
                        if not zip_info.is_dir():
                            try:
                                text_content = zf.read(zip_info).decode("utf-8", errors="ignore")
                                files_to_process[zip_info.filename] = text_content
                            except Exception:
                                pass
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid zip file: {str(e)}")
        else:
            try:
                text_content = content_bytes.decode("utf-8", errors="ignore")
                files_to_process[filename] = text_content
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    elif request and request.code:
        files_to_process[request.filename] = request.code
        framework = request.framework
    else:
        raise HTTPException(status_code=400, detail="Must provide source code string or upload a file.")

    if not files_to_process:
        raise HTTPException(status_code=400, detail="No readable source code files found.")

    endpoints, frameworks_map = parser_manager.parse_project(files_to_process, framework_hint=framework)

    return {
        "total_endpoints": len(endpoints),
        "frameworks_detected": frameworks_map,
        "endpoints": [ep.model_dump() for ep in endpoints],
    }


@app.post("/api/generate")
async def generate_docs(req: GenerateRequest):
    """
    Generates documentation for a list of parsed endpoints.
    """
    if not req.endpoints:
        raise HTTPException(status_code=400, detail="No endpoints provided for documentation generation.")

    endpoints_info = req.endpoints
    use_ai = req.mode == "ai" or bool(req.api_key)
    ai_gen = AIDocGenerator(api_key=req.api_key)

    if use_ai and ai_gen.is_available:
        docs = await ai_gen.generate_batch_docs(endpoints_info)
        active_mode = "ai"
    else:
        docs = [template_generator.generate_endpoint_doc(ep) for ep in endpoints_info]
        active_mode = "template"

    combined_md = exporter.combine_markdown(docs, endpoints_info)
    combined_html = exporter.render_html(combined_md)

    return {
        "mode_used": active_mode,
        "endpoint_docs": docs,
        "combined_markdown": combined_md,
        "combined_html": combined_html,
    }


@app.post("/api/analyze-and-generate")
async def analyze_and_generate(req: FullPipelineRequest):
    """
    Single endpoint combining analyze and generate steps for UI ease of use.
    """
    if not req.code:
        raise HTTPException(status_code=400, detail="No code provided")

    files = {req.filename: req.code}
    endpoints, frameworks_map = parser_manager.parse_project(files, framework_hint=req.framework)

    if not endpoints:
        return {
            "total_endpoints": 0,
            "endpoints": [],
            "combined_markdown": "### No API Endpoints Detected\n\nCould not find any routes matching supported frameworks (FastAPI, Flask, Express).",
            "combined_html": "<h3>No API Endpoints Detected</h3>",
            "mode_used": req.mode,
        }

    use_ai = req.mode == "ai" or bool(req.api_key)
    ai_gen = AIDocGenerator(api_key=req.api_key)

    if use_ai and ai_gen.is_available:
        docs = await ai_gen.generate_batch_docs(endpoints)
        active_mode = "ai"
    else:
        docs = [template_generator.generate_endpoint_doc(ep) for ep in endpoints]
        active_mode = "template"

    combined_md = exporter.combine_markdown(docs, endpoints)
    combined_html = exporter.render_html(combined_md)

    return {
        "total_endpoints": len(endpoints),
        "frameworks_detected": frameworks_map,
        "mode_used": active_mode,
        "endpoints": [ep.model_dump() for ep in endpoints],
        "endpoint_docs": docs,
        "combined_markdown": combined_md,
        "combined_html": combined_html,
    }


@app.get("/api/export")
def export_docs(
    markdown_content: str = Query(..., description="Markdown content to export"),
    format: str = Query("md", description="Export format: md or html"),
):
    if format == "html":
        html_out = exporter.render_html(markdown_content)
        return Response(
            content=html_out,
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=api_documentation.html"},
        )
    else:
        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=api_documentation.md"},
        )


# Mount static React SPA assets if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return HTMLResponse("<h1>API Documentation Agent Backend Running</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

