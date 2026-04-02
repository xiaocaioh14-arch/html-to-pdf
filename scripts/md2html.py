#!/usr/bin/env python3
"""
md2html.py — Convert Markdown to print-friendly HTML with CJK support.

Usage:
    python3 md2html.py --input doc.md --output doc.html [--title "Title"]

The output HTML includes:
- Full Markdown rendering (tables, code, lists, blockquotes, headings)
- Print-optimized CSS (@media print with tight margins, white background)
- CJK font stack (PingFang SC, Microsoft YaHei, Noto Sans CJK)
- Responsive tables that don't overflow on A4
"""

import argparse
import html
import re
import sys
import os


def markdown_to_html_blocks(md_text: str) -> str:
    """Simple but robust Markdown → HTML converter.
    Handles: headings, tables, code blocks, blockquotes, lists, bold, italic, links, hr.
    """
    lines = md_text.split('\n')
    out = []
    i = 0
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        r = []
        if in_ul:
            r.append('</ul>')
            in_ul = False
        if in_ol:
            r.append('</ol>')
            in_ol = False
        return r

    def inline(text):
        """Process inline markdown: bold, italic, code, links."""
        # Code spans first (so they don't get processed by bold/italic)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Bold + italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line
        if not stripped:
            out.extend(close_lists())
            i += 1
            continue

        # Fenced code block
        if stripped.startswith('```'):
            out.extend(close_lists())
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(html.escape(lines[i]))
                i += 1
            i += 1  # skip closing ```
            lang_attr = f' class="language-{lang}"' if lang else ''
            out.append(f'<pre><code{lang_attr}>{chr(10).join(code_lines)}</code></pre>')
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            out.extend(close_lists())
            level = len(m.group(1))
            text = inline(m.group(2))
            out.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            out.extend(close_lists())
            out.append('<hr>')
            i += 1
            continue

        # Blockquote
        if stripped.startswith('>'):
            out.extend(close_lists())
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(inline(lines[i].strip().lstrip('>').strip()))
                i += 1
            out.append(f'<blockquote><p>{"<br>".join(quote_lines)}</p></blockquote>')
            continue

        # Table
        if '|' in stripped and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i+1].strip()):
            out.extend(close_lists())
            # Parse header
            headers = [c.strip() for c in stripped.strip('|').split('|')]
            i += 1  # skip separator line
            i += 1
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells)
                i += 1
            # Build table HTML
            out.append('<div class="table-wrap"><table>')
            out.append('<thead><tr>')
            for h in headers:
                out.append(f'<th>{inline(h)}</th>')
            out.append('</tr></thead><tbody>')
            for row in rows:
                out.append('<tr>')
                for ci, cell in enumerate(row):
                    out.append(f'<td>{inline(cell)}</td>')
                out.append('</tr>')
            out.append('</tbody></table></div>')
            continue

        # Unordered list
        m = re.match(r'^[\s]*[-*+]\s+(.+)$', stripped)
        if m:
            if in_ol:
                out.extend(close_lists())
            if not in_ul:
                out.append('<ul>')
                in_ul = True
            out.append(f'<li>{inline(m.group(1))}</li>')
            i += 1
            continue

        # Ordered list
        m = re.match(r'^[\s]*\d+[.)]\s+(.+)$', stripped)
        if m:
            if in_ul:
                out.extend(close_lists())
            if not in_ol:
                out.append('<ol>')
                in_ol = True
            out.append(f'<li>{inline(m.group(1))}</li>')
            i += 1
            continue

        # Regular paragraph
        out.extend(close_lists())
        para_lines = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#', '```', '|', '>', '-', '*', '---')):
            para_lines.append(inline(lines[i].strip()))
            i += 1
            # Check if next line is a table separator (means current line was a table header)
            if i < len(lines) and re.match(r'^[\s|:-]+$', lines[i].strip()) and '|' in lines[i]:
                # Backtrack — this was a table header, not a paragraph
                i -= 1
                break
        if para_lines:
            out.append(f'<p>{"<br>".join(para_lines)}</p>')
        else:
            i += 1

    out.extend(close_lists())
    return '\n'.join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC',
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1a1a2e;
    background: #fff;
    padding: 24px;
    max-width: 900px;
    margin: 0 auto;
  }}

  /* Headings */
  h1 {{ font-size: 1.8em; font-weight: 700; margin: 24px 0 12px; padding-bottom: 6px; border-bottom: 2px solid #2d5f8a; color: #1a1a2e; }}
  h2 {{ font-size: 1.35em; font-weight: 700; margin: 20px 0 8px; color: #2d5f8a; }}
  h3 {{ font-size: 1.1em; font-weight: 600; margin: 16px 0 6px; color: #333; }}
  h4, h5, h6 {{ font-size: 1em; font-weight: 600; margin: 12px 0 4px; color: #444; }}

  /* Body text */
  p {{ margin: 0 0 8px; text-align: justify; }}
  a {{ color: #2d5f8a; text-decoration: none; }}

  /* Lists */
  ul, ol {{ margin: 4px 0 8px 20px; }}
  li {{ margin-bottom: 3px; }}

  /* Blockquote */
  blockquote {{
    margin: 8px 0;
    padding: 8px 14px;
    border-left: 3px solid #2d5f8a;
    background: #f0f4f8;
    color: #374151;
    font-size: 0.95em;
  }}

  /* Tables */
  .table-wrap {{ overflow-x: auto; margin: 8px 0; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9em;
  }}
  th {{
    background: #2d5f8a;
    color: #fff;
    text-align: left;
    padding: 6px 10px;
    font-weight: 600;
    white-space: nowrap;
  }}
  td {{
    padding: 5px 10px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f9fafb; }}

  /* Code */
  code {{
    font-family: 'SF Mono', 'Fira Code', 'Menlo', monospace;
    font-size: 0.88em;
    background: #f3f4f6;
    padding: 1px 4px;
    border-radius: 3px;
  }}
  pre {{
    margin: 8px 0;
    padding: 12px 14px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 0.85em;
    line-height: 1.4;
  }}
  pre code {{ background: none; padding: 0; }}

  /* Horizontal rule */
  hr {{ border: none; border-top: 1px solid #d1d5db; margin: 16px 0; }}

  /* Print styles */
  @media print {{
    body {{
      padding: 0;
      font-size: 9pt;
      line-height: 1.5;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    @page {{ size: A4; margin: 12mm 14mm; }}
    h1 {{ font-size: 1.6em; margin-top: 0; }}
    h2 {{ font-size: 1.2em; }}
    th {{
      background: #2d5f8a !important;
      color: #fff !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    tr:nth-child(even) td {{
      background: #f9fafb !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    blockquote {{
      background: #f0f4f8 !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    pre {{
      background: #f3f4f6 !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    a {{ color: #2d5f8a; text-decoration: none; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
{content}
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to print-friendly HTML')
    parser.add_argument('--input', '-i', required=True, help='Input Markdown file')
    parser.add_argument('--output', '-o', required=True, help='Output HTML file')
    parser.add_argument('--title', '-t', default='', help='Document title')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Auto-detect title from first heading if not provided
    title = args.title
    if not title:
        m = re.match(r'^#\s+(.+)$', md_text, re.MULTILINE)
        title = m.group(1) if m else os.path.splitext(os.path.basename(args.input))[0]

    body_html = markdown_to_html_blocks(md_text)
    full_html = TEMPLATE.format(title=html.escape(title), content=body_html)

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f'OK: {args.output} ({len(full_html)} bytes)')


if __name__ == '__main__':
    main()
