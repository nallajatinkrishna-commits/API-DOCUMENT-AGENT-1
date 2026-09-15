import pytest
from backend.parsers.base import EndpointInfo, EndpointParameter, RequestBodyInfo, ResponseInfo
from backend.generator.template_gen import TemplateDocGenerator
from backend.generator.exporter import DocExporter


def test_template_generator():
    ep = EndpointInfo(
        id="test_ep_1",
        file_path="main.py",
        framework="fastapi",
        method="GET",
        path="/users/{user_id}",
        handler_name="get_user",
        docstring="Retrieve user details by ID.",
        parameters=[
            EndpointParameter(name="user_id", type="int", location="path", required=True),
            EndpointParameter(name="verbose", type="bool", location="query", required=False),
        ],
        response_info=ResponseInfo(status_code=200, type_annotation="UserResponse"),
    )

    gen = TemplateDocGenerator()
    result = gen.generate_endpoint_doc(ep)

    assert result["endpoint_id"] == "test_ep_1"
    assert result["ai_generated"] is False
    md = result["markdown"]
    assert "### `GET` /users/{user_id}" in md
    assert "Retrieve user details by ID." in md
    assert "| `user_id` | `int` | `path` | Yes |" in md
    assert "curl -X GET" in md


def test_doc_exporter():
    ep = EndpointInfo(
        id="test_ep_1",
        file_path="main.py",
        framework="fastapi",
        method="GET",
        path="/users/{user_id}",
        handler_name="get_user",
        docstring="Retrieve user details by ID.",
    )

    gen = TemplateDocGenerator()
    doc = gen.generate_endpoint_doc(ep)

    exporter = DocExporter()
    combined_md = exporter.combine_markdown([doc], [ep])

    assert "# API Reference Documentation" in combined_md
    assert "## Table of Contents" in combined_md
    assert "[GET `/users/{user_id}`]" in combined_md

    html_out = exporter.render_html(combined_md)
    assert "<!DOCTYPE html>" in html_out
    assert "badge-get" in html_out
    assert "Copy" in html_out
