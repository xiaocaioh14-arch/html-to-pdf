#!/usr/bin/env python3
"""
inject_print_css.py — Inject print-optimized CSS into an existing HTML file.

Usage:
    python3 inject_print_css.py --input page.html --output page_print.html

Only injects if the HTML doesn't already have @media print styles.
The injected CSS:
- Switches to white background
- Sets CJK-safe font stack
- Tightens margins for A4
- Forces color printing for backgrounds/badges
- Adds borders to tables/cards that rely on background color
"""

import argparse
import re
import sys

PRINT_CSS = """
<style id="injected-print-css">
  @media print {
    * { box-sizing: border-box; }
    body {
      background: #fff !important;
      color: #111827 !important;
      font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;
      font-size: 9pt;
      line-height: 1.5;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    @page { size: A4; margin: 12mm 14mm; }

    /* Force color printing for key elements */
    th, .badge, blockquote, pre, code,
    [style*="background"] {
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    /* Tables: ensure borders visible */
    table { border: 1px solid #d1d5db; font-size: 8pt; }
    th { padding: 5px 8px; }
    td { padding: 4px 8px; border-bottom: 1px solid #e5e7eb; }

    /* Remove decorative elements that waste ink */
    *:not(th):not(.badge):not(blockquote):not(pre) {
      box-shadow: none !important;
    }

    /* Compact spacing */
    h1 { font-size: 1.5em; margin-top: 12px; }
    h2 { font-size: 1.2em; margin-top: 10px; }
    h3 { font-size: 1em; margin-top: 8px; }
    p { margin-bottom: 6px; }

    /* Links: don't show URL */
    a { color: #2d5f8a; text-decoration: none; }
    a::after { content: none !important; }
  }
</style>
"""


def main():
    parser = argparse.ArgumentParser(description='Inject print CSS into HTML')
    parser.add_argument('--input', '-i', required=True, help='Input HTML file')
    parser.add_argument('--output', '-o', required=True, help='Output HTML file')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html = f.read()

    # Check if @media print already exists
    if '@media print' in html and 'injected-print-css' not in html:
        print(f'SKIP: {args.input} already has @media print styles')
        # Still copy to output
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html)
        return

    # Inject before </head> or before </html> or at end
    if '</head>' in html:
        html = html.replace('</head>', PRINT_CSS + '\n</head>')
    elif '</html>' in html:
        html = html.replace('</html>', PRINT_CSS + '\n</html>')
    else:
        html = html + PRINT_CSS

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'OK: injected print CSS into {args.output}')


if __name__ == '__main__':
    main()
