import pytest
from backend.parsers.fastapi_parser import FastAPIParser


def test_fastapi_parser_can_parse():
    parser = FastAPIParser()
    assert parser.can_parse("main.py", "from fastapi import FastAPI\napp = FastAPI()") is True
    assert parser.can_parse("index.js", "const express = require('express');") is False


def test_fastapi_endpoint_extraction():
    code = """
from fastapi import FastAPI, APIRouter, Depends, Query
from pydantic import BaseModel

app = FastAPI()
router = APIRouter(prefix="/items", tags=["Catalog"])

class Item(BaseModel):
    title: str
    price: float

@app.get("/health")
def health():
    \"\"\"Check system health status.\"\"\"
    return {"status": "ok"}

@router.get("/{item_id}")
def get_item(item_id: int, q: str = Query(None)):
    \"\"\"Fetch item by ID.\"\"\"
    return {"item_id": item_id, "q": q}

@router.post("/", status_code=201)
def create_item(item: Item):
    \"\"\"Create new item in catalog.\"\"\"
    return item

app.include_router(router)
"""
    parser = FastAPIParser()
    endpoints = parser.parse("app.py", code)

    assert len(endpoints) == 3

    # 1. Health endpoint
    health_ep = next(ep for ep in endpoints if ep.path == "/health")
    assert health_ep.method == "GET"
    assert health_ep.docstring == "Check system health status."

    # 2. Get item endpoint
    get_item_ep = next(ep for ep in endpoints if ep.path == "/items/{item_id}")
    assert get_item_ep.method == "GET"
    assert get_item_ep.docstring == "Fetch item by ID."
    path_param = next(p for p in get_item_ep.parameters if p.name == "item_id")
    assert path_param.location == "path"
    assert "int" in path_param.type

    # 3. Create item endpoint
    create_ep = next(ep for ep in endpoints if ep.path == "/items")
    assert create_ep.method == "POST"
    assert create_ep.request_body is not None
    assert len(create_ep.request_body.fields) == 2
