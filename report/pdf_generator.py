from pathlib import Path


CSS = """
@page {
    margin: 2cm 2.5cm;
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: #888;
    }
}

body {
    font-family: -apple-system, "Segoe UI", Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #1a1a2e;
    background: #ffffff;
}

h1 {
    font-size: 22pt;
    color: #0f3460;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 8px;
    margin-bottom: 4px;
}

h1 + blockquote {
    margin-top: 4px;
    color: #666;
    font-style: italic;
    border-left: none;
    padding: 0;
}

h2 {
    font-size: 14pt;
    color: #16213e;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 4px;
    margin-top: 24px;
}

h3 {
    font-size: 11.5pt;
    color: #0f3460;
    margin-top: 16px;
}

blockquote {
    border-left: 4px solid #0f3460;
    margin: 12px 0;
    padding: 8px 16px;
    background: #f0f4ff;
    border-radius: 0 6px 6px 0;
    color: #333;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    margin: 12px 0;
}

thead tr {
    background: #0f3460;
    color: #ffffff;
}

thead th {
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}

tbody tr:nth-child(even) {
    background: #f8f9fa;
}

tbody tr:nth-child(odd) {
    background: #ffffff;
}

tbody td {
    padding: 6px 10px;
    border-bottom: 1px solid #e9ecef;
}

tbody tr:first-child td[colspan],
tbody td strong {
    background: #e8edf5;
    font-weight: 700;
    color: #0f3460;
}

code {
    background: #f0f0f0;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 9pt;
    font-family: "Courier New", monospace;
}

hr {
    border: none;
    border-top: 1px solid #dee2e6;
    margin: 20px 0;
}

ul {
    padding-left: 20px;
}

li {
    margin: 4px 0;
}

em {
    color: #555;
}
"""


def markdown_to_pdf(md_text: str, output_path: str) -> bool:
    """
    Convert a Markdown string to a styled PDF.
    Returns True on success, False if WeasyPrint is unavailable.
    """
    try:
        import markdown as md_lib
        from weasyprint import HTML, CSS as WeasyprintCSS
    except ImportError as e:
        print(f"[pdf] WeasyPrint not available: {e}")
        return False

    try:
        # Convert Markdown → HTML
        html_body = md_lib.markdown(
            md_text,
            extensions=["tables", "fenced_code", "nl2br"],
        )

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>MacroLens Daily Brief</title>
</head>
<body>
{html_body}
</body>
</html>"""

        # Convert HTML → PDF
        HTML(string=full_html).write_pdf(
            output_path,
            stylesheets=[WeasyprintCSS(string=CSS)],
        )
        print(f"[pdf] Saved → {output_path}")
        return True

    except Exception as e:
        print(f"[pdf] Generation failed: {e}")
        return False
