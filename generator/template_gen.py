"""
Deterministic, zero-dependency Template Documentation Generator.
Renders clean Markdown per endpoint with HTTP methods, parameter tables, curl examples, and status codes.
"""

import json
from typing import Dict, Any, List
from backend.parsers.base import EndpointInfo, EndpointParameter


class TemplateDocGenerator:
    def generate_endpoint_doc(self, ep: EndpointInfo) -> Dict[str, Any]:
        """
        Generates markdown documentation for a single endpoint.
        Returns dict with keys: 'markdown', 'ai_generated', 'endpoint_id'.
        """
        md_lines = []

        # Header
        md_lines.append(f"### `{ep.method}` {ep.path}")
        md_lines.append("")

        # Description
        if ep.docstring:
            md_lines.append(f"**Description:**  \n{ep.docstring.strip()}")
        else:
            default_desc = self._generate_default_description(ep.method, ep.path, ep.handler_name)
            md_lines.append(f"**Description:**  \n{default_desc}")

        md_lines.append("")
        md_lines.append(f"- **Handler:** `{ep.handler_name}()` in `{ep.file_path}` (Line {ep.line_number})")
        if ep.auth_middleware:
            auth_str = ", ".join([f"`{a}`" for a in ep.auth_middleware])
            md_lines.append(f"- **Authentication / Middleware:** {auth_str}")

        md_lines.append("")

        # Parameters Table
        if ep.parameters:
            md_lines.append("#### Parameters")
            md_lines.append("")
            md_lines.append("| Name | Type | In | Required | Default | Description |")
            md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for p in ep.parameters:
                req_str = "Yes" if p.required else "No"
                def_str = f"`{p.default_value}`" if p.default_value else "-"
                desc_str = p.description or f"{p.location.capitalize()} parameter `{p.name}`"
                md_lines.append(
                    f"| `{p.name}` | `{p.type}` | `{p.location}` | {req_str} | {def_str} | {desc_str} |"
                )
            md_lines.append("")

        # Request Body
        if ep.request_body:
            md_lines.append("#### Request Body")
            md_lines.append(f"Content-Type: `{ep.request_body.content_type}`")
            md_lines.append("")

            if ep.request_body.fields:
                md_lines.append("| Field | Type | Required | Description |")
                md_lines.append("| :--- | :--- | :--- | :--- |")
                for f in ep.request_body.fields:
                    req_str = "Yes" if f.required else "No"
                    desc_str = f.description or f"Field `{f.name}`"
                    md_lines.append(f"| `{f.name}` | `{f.type}` | {req_str} | {desc_str} |")
                md_lines.append("")

            sample_body = self._generate_sample_body(ep.request_body.fields)
            md_lines.append("```json")
            md_lines.append(json.dumps(sample_body, indent=2))
            md_lines.append("```")
            md_lines.append("")

        # Example Request (Curl)
        md_lines.append("#### Example Request")
        md_lines.append("```bash")
        curl_cmd = self._generate_curl_command(ep)
        md_lines.append(curl_cmd)
        md_lines.append("```")
        md_lines.append("")

        # Example Response
        md_lines.append("#### Example Response")
        md_lines.append(f"Status: `{ep.response_info.status_code if ep.response_info else 200} OK`")
        md_lines.append("```json")
        sample_res = self._generate_sample_response(ep)
        md_lines.append(json.dumps(sample_res, indent=2))
        md_lines.append("```")
        md_lines.append("")

        # Status Codes
        md_lines.append("#### Response Status Codes")
        md_lines.append("| Status Code | Description |")
        md_lines.append("| :--- | :--- |")
        md_lines.append(f"| `200 OK` | Successful request execution |")
        if ep.parameters or ep.request_body:
            md_lines.append("| `400 Bad Request` | Invalid input parameters or payload |")
        if ep.auth_middleware:
            md_lines.append("| `401 Unauthorized` | Missing or invalid authentication token |")
        md_lines.append("| `500 Internal Error` | Unexpected server error |")
        md_lines.append("")

        return {
            "endpoint_id": ep.id,
            "markdown": "\n".join(md_lines),
            "ai_generated": False,
        }

    def _generate_default_description(self, method: str, path: str, handler: str) -> str:
        clean_path = path.replace("{", "").replace("}", "")
        resource = clean_path.strip("/").split("/")[-1] or "resource"
        actions = {
            "GET": f"Retrieves `{resource}` information from the system.",
            "POST": f"Creates a new `{resource}` record in the system.",
            "PUT": f"Updates an existing `{resource}` record.",
            "PATCH": f"Partially updates `{resource}` attributes.",
            "DELETE": f"Deletes a `{resource}` record by identifier.",
        }
        return actions.get(method, f"Handles HTTP {method} requests for `{path}`.")

    def _generate_sample_body(self, fields: List[EndpointParameter]) -> Dict[str, Any]:
        if not fields:
            return {"key": "value"}
        sample = {}
        for f in fields:
            t = f.type.lower()
            if "int" in t:
                sample[f.name] = 1
            elif "bool" in t:
                sample[f.name] = True
            elif "float" in t or "number" in t:
                sample[f.name] = 99.99
            elif "list" in t or "array" in t:
                sample[f.name] = ["sample_item"]
            else:
                sample[f.name] = f"example_{f.name}"
        return sample

    def _generate_curl_command(self, ep: EndpointInfo) -> str:
        sample_path = ep.path
        for p in ep.parameters:
            if p.location == "path":
                val = "123" if "int" in p.type.lower() else "sample_id"
                sample_path = sample_path.replace(f"{{{p.name}}}", val)

        query_parts = []
        for p in ep.parameters:
            if p.location == "query":
                val = "10" if "int" in p.type.lower() else "test"
                query_parts.append(f"{p.name}={val}")

        if query_parts:
            sample_path += "?" + "&".join(query_parts)

        cmd_lines = [f'curl -X {ep.method} "http://localhost:8000{sample_path}" \\']
        cmd_lines.append('  -H "Content-Type: application/json" \\')
        if ep.auth_middleware:
            cmd_lines.append('  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\')

        if ep.request_body:
            sample_b = self._generate_sample_body(ep.request_body.fields)
            json_str = json.dumps(sample_b)
            cmd_lines.append(f"  -d '{json_str}'")

        return "\n".join(cmd_lines).rstrip(" \\")

    def _generate_sample_response(self, ep: EndpointInfo) -> Dict[str, Any]:
        if ep.method == "DELETE":
            return {"success": True, "message": "Record successfully deleted"}
        elif ep.method in ["POST", "PUT", "PATCH"]:
            return {
                "id": "12345",
                "status": "success",
                "created_at": "2026-09-15T12:00:00Z",
                "message": "Resource processed successfully",
            }
        else:
            return {
                "status": "success",
                "data": {"id": "12345", "name": "Sample Record", "active": True},
            }
