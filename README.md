# html-to-pdf
用途：把 HTML 或 Markdown 转成高质量 PDF，核心解决的问题是中文渲染——传统工具（ReportLab、wkhtmltopdf）中文容易乱码。

  技术栈：
  - Markdown → HTML：Python 脚本（md2html.py）
  - HTML → PDF：Chrome headless 的 --print-to-pdf，等于用完整的 Chrome 渲染引擎做打印，所以中文、表格、代码块、CSS 都不会有问题
  - 打印优化：注入 @page { margin: 0 } + @media print CSS，去掉页眉页脚，适配 A4 纸

  本质就是拿 Chrome 当 PDF 渲染器用，所见即所得。
