# API Documentation Agent

A full-stack, production-ready **API Documentation Agent** web application that automatically extracts API endpoints from Python (**FastAPI**, **Flask**) and JavaScript/TypeScript (**Express**) backend source code, generating clean, complete Markdown and standalone HTML documentation.

Supports both **Template Mode** (zero-configuration, offline, deterministic) and **AI Mode** (powered by Anthropic Claude for natural language descriptions, realistic payload examples, and edge case notes with per-endpoint graceful fallback).

---

## Key Features

- **Multi-Language & Multi-Framework Extraction**:
  - **FastAPI**: AST parser extracting `@app.get/post/...`, `APIRouter(prefix=...)`, Pydantic body schemas, type annotations, docstrings, status codes, and `Depends(...)` auth.
  - **Flask**: AST parser extracting `@app.route`, Blueprint `url_prefix`, path converters (`<int:id>`), `@login_required` decorators, methods, and docstrings.
  - **Express (JS/TS)**: Babel AST parser (`@babel/parser`) parsing ES6+/TypeScript route definitions (`app.get`, `router.post`), `app.use('/prefix', router)`, middleware chains, JSDoc comments, and path params (`:id`).
- **Pluggable Parser Architecture**: Easily add support for new frameworks (e.g., Django, Spring Boot, NestJS) by implementing `BaseParser`.
- **Dual-Engine Documentation Generator**:
  - **Template Mode (Default)**: Zero-config, fast, deterministic Markdown doc generator with Table of Contents, parameter tables, curl commands, JSON response previews, and status code tables.
  - **AI Mode (Claude)**: Asynchronous parallelized Anthropic Claude integration. Per-endpoint fallback ensures whole-project documentation never fails if one API call encounters errors.
- **Responsive React SPA Frontend**:
  - Drag-and-drop file/zip uploader + Raw code editor with instant sample app loaders (FastAPI, Flask, Express).
  - Filterable sidebar with color-coded HTTP method badges (`GET` emerald, `POST` blue, `PUT` amber, `DELETE` rose, `PATCH` purple).
  - Live progress timeline, interactive code snippet previews, and one-click `.md` / `.html` exports.
- **Dual Interface**: Use as a web application or standalone Command Line Interface (CLI).

---

## Directory Structure

```
hackathon-2/
├── backend/
│   ├── parsers/
│   │   ├── base.py            # Base dataclasses & BaseParser interface
│   │   ├── fastapi_parser.py  # FastAPI AST parser
│   │   ├── flask_parser.py    # Flask AST parser
│   │   ├── js_ast_parser.js   # Babel JS/TS AST route extractor
│   │   ├── express_parser.py  # Express Python parser wrapper
│   │   └── manager.py         # Parser auto-detection manager
│   ├── generator/
│   │   ├── template_gen.py    # Deterministic Markdown generator
│   │   ├── ai_gen.py          # Anthropic Claude API async generator
│   │   └── exporter.py        # TOC builder & Markdown/HTML exporter
│   ├── main.py                # FastAPI REST server & static SPA server
│   └── cli.py                 # Command line interface
├── frontend/                  # React + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/        # Header, KeyDrawer, UploadSection, Sidebar, DocViewer
│   │   ├── utils/             # API client & sample code loaders
│   │   └── App.jsx
│   └── dist/                  # Built production assets
├── samples/                   # Demo sample projects (FastAPI, Flask, Express)
├── tests/                     # Comprehensive pytest unit test suite
└── requirements.txt
```

---

## Quick Start & Running Locally

### 1. Requirements
- **Python 3.10+**
- **Node.js 18+**

### 2. Install Dependencies

```bash
# Install Python dependencies
py -m pip install -r requirements.txt

# Install Express AST parser dependencies
cd backend/parsers
npm install
cd ../..

# Install frontend dependencies & build SPA
cd frontend
npm install
npm run build
cd ..
```

### 3. Run Web Application

Launch the unified FastAPI server (serves REST API + React SPA):

```bash
py -m backend.main
```

Open your browser to: **`http://localhost:8000`**

---

## Running CLI Mode

You can run the documentation agent directly from your terminal:

```bash
# Parse source code and print detected endpoints JSON
py -m backend.cli parse samples/fastapi_app.py

# Generate Markdown documentation to file
py -m backend.cli generate samples/fastapi_app.py -o API_DOCS.md

# Generate HTML documentation using AI mode (requires ANTHROPIC_API_KEY)
py -m backend.cli generate samples/express_app.js -o API_DOCS.html --format html --ai
```

---

## Setting `ANTHROPIC_API_KEY` for AI Mode

To use Claude for AI-written descriptions and realistic sample payloads:

1. **Environment Variable**:
   ```bash
   # Windows PowerShell
   $env:ANTHROPIC_API_KEY="sk-ant-api03-..."

   # Command Prompt / Bash
   export ANTHROPIC_API_KEY="sk-ant-api03-..."
   ```
2. **In Web UI**:
   Click the **"API Key"** button in the header bar of the web app to paste your key for the current session.

If no key is configured, the application automatically operates in **Template Mode**.

---

## Running Unit Tests

Run the full pytest suite:

```bash
py -m pytest
```

---

## Adding Support for a New Framework

To add a new framework parser (e.g., `DjangoParser`):

1. Create `backend/parsers/django_parser.py` inheriting from `BaseParser` in `backend/parsers/base.py`:
   ```python
   from backend.parsers.base import BaseParser, EndpointInfo

   class DjangoParser(BaseParser):
       @property
       def framework_name(self) -> str:
           return "django"

       def can_parse(self, filename: str, content: str) -> bool:
           return "urlpatterns" in content or "path(" in content

       def parse(self, filename: str, content: str) -> List[EndpointInfo]:
           # Implement route extraction logic
           return endpoints
   ```
2. Register your new parser in `backend/parsers/manager.py`:
   ```python
   from backend.parsers.django_parser import DjangoParser

   class ParserManager:
       def __init__(self):
           self.parsers = [
               FastAPIParser(),
               FlaskParser(),
               ExpressParser(),
               DjangoParser(),
           ]
   ```
