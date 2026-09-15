"""
Exporter module for combining endpoint documentation into full Markdown documents and rendering standalone HTML pages with themes and copy buttons.
"""

import datetime
import re
from typing import List, Dict, Any
import markdown
from backend.parsers.base import EndpointInfo


class DocExporter:
    def combine_markdown(
        self,
        endpoint_docs: List[Dict[str, Any]],
        endpoints_info: List[EndpointInfo],
        title: str = "API Reference Documentation",
    ) -> str:
        """
        Combines endpoint markdown docs into a single document with Table of Contents.
        """
        ep_map = {ep.id: ep for ep in endpoints_info}
        lines = []

        # Document Header
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")

        # Summary Metrics
        total_eps = len(endpoints_info)
        frameworks = sorted(list({ep.framework.upper() for ep in endpoints_info}))
        methods = sorted(list({ep.method for ep in endpoints_info}))

        lines.append("## Overview")
        lines.append(f"- **Total Endpoints:** {total_eps}")
        lines.append(f"- **Frameworks Detected:** {', '.join(frameworks) if frameworks else 'N/A'}")
        lines.append(f"- **HTTP Methods:** {', '.join(methods) if methods else 'N/A'}")
        lines.append("")

        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("")

        # Group by tag or file
        grouped: Dict[str, List[tuple[EndpointInfo, str]]] = {}
        for doc in endpoint_docs:
            ep = ep_map.get(doc["endpoint_id"])
            if not ep:
                continue
            group_key = ep.tags[0] if ep.tags else ep.file_path
            grouped.setdefault(group_key, []).append((ep, doc["markdown"]))

        for group_name, items in grouped.items():
            lines.append(f"### {group_name.capitalize()}")
            for ep, _ in items:
                anchor = self._create_anchor(ep.method, ep.path)
                lines.append(f"- [{ep.method} `{ep.path}`](#{anchor})")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Endpoint Sections
        for group_name, items in grouped.items():
            lines.append(f"## Resource: {group_name.capitalize()}")
            lines.append("")
            for ep, md in items:
                lines.append(md)
                lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    def render_html(self, markdown_text: str, title: str = "API Reference Documentation") -> str:
        """
        Converts Markdown text into a styled, standalone HTML document.
        """
        # Convert MD to HTML using python-markdown extensions
        html_body = markdown.markdown(
            markdown_text,
            extensions=[
                "tables",
                "fenced_code",
                "codehilite",
                "toc",
            ],
        )

        # Style method badges inside rendered HTML
        html_body = self._style_method_badges(html_body)

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --accent-color: #38bdf8;
            --code-bg: #090d16;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: var(--bg-secondary);
            border-radius: 12px;
            padding: 2.5rem;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 1px solid var(--border-color);
        }}
        h1, h2, h3, h4 {{ color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 0.75rem; font-weight: 600; }}
        h1 {{ font-size: 2.25rem; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem; }}
        h2 {{ font-size: 1.5rem; color: var(--accent-color); border-bottom: 1px solid var(--border-color); padding-bottom: 0.3rem; margin-top: 2rem; }}
        h3 {{ font-size: 1.25rem; }}
        h4 {{ font-size: 1rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }}
        p, li {{ color: var(--text-secondary); margin-bottom: 0.75rem; }}
        a {{ color: var(--accent-color); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        code {{
            font-family: 'Fira Code', monospace;
            background-color: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
            color: #38bdf8;
        }}
        pre {{
            position: relative;
            background-color: var(--code-bg);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid var(--border-color);
        }}
        pre code {{ background: none; padding: 0; color: #e2e8f0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background-color: var(--bg-primary);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border-color); }}
        th {{ background-color: #0f172a; color: var(--text-primary); font-weight: 600; }}
        tr:hover {{ background-color: #1a2332; }}
        hr {{ border: 0; height: 1px; background: var(--border-color); margin: 2rem 0; }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.85rem;
            font-family: 'Fira Code', monospace;
            margin-right: 0.5rem;
        }}
        .badge-get {{ background-color: #064e3b; color: #34d399; border: 1px solid #059669; }}
        .badge-post {{ background-color: #1e3a8a; color: #60a5fa; border: 1px solid #2563eb; }}
        .badge-put {{ background-color: #78350f; color: #fbbf24; border: 1px solid #d97706; }}
        .badge-delete {{ background-color: #881337; color: #f87171; border: 1px solid #e11d48; }}
        .badge-patch {{ background-color: #581c87; color: #c084fc; border: 1px solid #9333ea; }}
        .copy-btn {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            cursor: pointer;
        }}
        .copy-btn:hover {{ color: var(--text-primary); background: var(--border-color); }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
    <script>
        document.querySelectorAll('pre').forEach(block => {{
            const button = document.createElement('button');
            button.className = 'copy-btn';
            button.innerText = 'Copy';
            button.addEventListener('click', async () => {{
                const code = block.querySelector('code').innerText;
                await navigator.clipboard.writeText(code);
                button.innerText = 'Copied!';
                setTimeout(() => {{ button.innerText = 'Copy'; }}, 2000);
            }});
            block.appendChild(button);
        }});
    </script>
</body>
</html>"""
        return full_html

    def _create_anchor(self, method: str, path: str) -> str:
        raw = f"{method.lower()}-{path.lower()}"
        return re.sub(r"[^a-z0-9\-]", "", raw.replace("/", "-").replace("{", "").replace("}", ""))

    def _style_method_badges(self, html: str) -> str:
        def replace_badge(match):
            method = match.group(1).upper()
            cls_map = {
                "GET": "badge-get",
                "POST": "badge-post",
                "PUT": "badge-put",
                "DELETE": "badge-delete",
                "PATCH": "badge-patch",
            }
            badge_cls = cls_map.get(method, "badge-get")
            return f'<code><span class="badge {badge_cls}">{method}</span>'

        return re.sub(r"<code>`(GET|POST|PUT|DELETE|PATCH)`", replace_badge, html)
