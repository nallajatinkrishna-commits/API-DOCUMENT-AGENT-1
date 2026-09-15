"""
AI-enhanced Documentation Generator using Anthropic's Claude API.
Parallelizes endpoint generation using asyncio with rate-limiting semaphore.
Includes per-endpoint graceful fallback to TemplateDocGenerator upon API failure or missing API key.
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
import anthropic
from backend.parsers.base import EndpointInfo
from backend.generator.template_gen import TemplateDocGenerator


class AIDocGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.template_gen = TemplateDocGenerator()
        self.model = "claude-3-haiku-20240307"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def generate_endpoint_doc(
        self, ep: EndpointInfo, client: Optional[anthropic.AsyncAnthropic] = None
    ) -> Dict[str, Any]:
        if not self.is_available:
            doc = self.template_gen.generate_endpoint_doc(ep)
            doc["ai_error"] = "No ANTHROPIC_API_KEY provided"
            return doc

        own_client = False
        if client is None:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            own_client = True

        prompt = f"""You are an expert technical writer and API architect.
Generate comprehensive, professional Markdown API documentation for the following endpoint:

- **Framework:** {ep.framework}
- **Method:** {ep.method}
- **Path:** {ep.path}
- **Handler Name:** {ep.handler_name}
- **File:** {ep.file_path} (line {ep.line_number})
- **Docstring / Comment:** {ep.docstring or 'None'}
- **Parameters:** {json.dumps([p.model_dump() for p in ep.parameters])}
- **Request Body Info:** {json.dumps(ep.request_body.model_dump() if ep.request_body else None)}
- **Response Info:** {json.dumps(ep.response_info.model_dump() if ep.response_info else None)}
- **Auth / Middleware:** {json.dumps(ep.auth_middleware)}

Format requirements:
1. Start with title header `### \`{ep.method}\` {ep.path}`
2. Write a clear, professional 2-3 sentence description explaining what this endpoint does and real-world use cases.
3. List parameters table (Name, Type, Location, Required, Description, Default).
4. If POST/PUT/PATCH, provide realistic domain-specific sample JSON request payload.
5. Provide a copy-pasteable curl example.
6. Provide a realistic domain-specific JSON response sample with realistic data values.
7. Include Response Status Codes table with explanations.
8. Add a "Edge Cases & Notes" section highlighting potential pitfalls or security considerations.
Do NOT include top-level title `# API Docs`, only output the Markdown section for this specific endpoint.
"""

        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    system="You generate clean, professional GitHub-flavored Markdown API documentation.",
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=15.0,
            )

            md_content = response.content[0].text.strip()
            return {
                "endpoint_id": ep.id,
                "markdown": md_content,
                "ai_generated": True,
            }

        except Exception as e:
            # Fallback per-endpoint to template mode if AI call fails
            fallback = self.template_gen.generate_endpoint_doc(ep)
            fallback["ai_error"] = f"AI Generation error: {str(e)}"
            return fallback
        finally:
            if own_client:
                await client.close()

    async def generate_batch_docs(
        self, endpoints: List[EndpointInfo], concurrency_limit: int = 5
    ) -> List[Dict[str, Any]]:
        if not self.is_available:
            return [self.template_gen.generate_endpoint_doc(ep) for ep in endpoints]

        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def worker(ep: EndpointInfo):
            async with semaphore:
                return await self.generate_endpoint_doc(ep, client=client)

        try:
            tasks = [worker(ep) for ep in endpoints]
            results = await asyncio.gather(*tasks)
            return list(results)
        finally:
            await client.close()
