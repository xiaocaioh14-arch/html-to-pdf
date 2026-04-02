---
name: html-to-pdf
description: >
  将 HTML 文件或 Markdown 内容转换为高质量 PDF。通过 Chrome headless 渲染，
  完美支持中文、表格、代码块、拓扑图等复杂内容——解决 ReportLab/wkhtmltopdf
  等工具的中文乱码问题。当用户说"转PDF"、"导出PDF"、"生成PDF"、"打印成PDF"、
  "Markdown转PDF"、"HTML转PDF"、"导出报告"、"生成报告PDF"，或者有一个HTML文件
  想变成PDF时，使用此skill。也适用于用户写完Markdown文档后说"输出一下"、"导出一下"。
---

# HTML to PDF

将 HTML 或 Markdown 转为高质量 PDF。核心是用 Chrome headless 做渲染引擎，
天然支持中文和所有现代 CSS，输出所见即所得。

## 工作流

```
输入 (HTML 或 Markdown)
  │
  ├─ HTML 文件 → 直接走 Step 2
  │
  └─ Markdown 内容/文件 → Step 1: 转成 HTML
                              │
                              ▼
                         Step 2: 注入打印优化 CSS（如果 HTML 没有 @media print）
                              │
                              ▼
                         Step 3: Chrome headless --print-to-pdf
                              │
                              ▼
                         输出 PDF 文件
```

## Step 1: Markdown → HTML

如果输入是 Markdown 文件或 Markdown 文本，用 `scripts/md2html.py` 转换：

```bash
python3 scripts/md2html.py --input <input.md> --output <output.html> [--title "文档标题"]
```

这个脚本会：
- 解析 Markdown（表格、代码块、列表、引用、标题等）
- 套入一个打印友好的 HTML 模板（浅色主题，中文字体，紧凑排版）
- 自带 `@media print` CSS，不需要额外处理

如果用户没提供 Markdown 文件而是在对话中给了内容，先把内容写到临时 .md 文件再调脚本。

## Step 2: 确保 HTML 有打印优化 CSS

如果输入是用户自己的 HTML 文件，检查是否已有 `@media print` 样式。
如果没有，用 `scripts/inject_print_css.py` 注入一套默认的打印优化样式：

```bash
python3 scripts/inject_print_css.py --input <input.html> --output <output.html>
```

注入的样式做这几件事：
- 背景改白色（省墨水，避免深色背景打印问题）
- 字体回退到 PingFang SC / Microsoft YaHei（中文支持）
- 页边距收紧（A4 纸 12mm）
- 去掉不必要的装饰（阴影、圆角、动画）
- 表格和卡片加边框（屏幕上靠背景色区分的元素，打印时需要边框）

如果 HTML 已有完善的 `@media print`，跳过这步。

## Step 2.5: 注入去页眉页脚的 CSS（必做）

Chrome 的 `--print-to-pdf-no-header` 在 `--headless=new` 模式下不可靠，经常仍然会打印日期、标题、URL 等页眉页脚。

**可靠方案**：用 CSS `@page { margin: 0 }` 把页边距设为 0，这样 Chrome 没有空间渲染页眉页脚。然后用 `body` 的 `padding` 来控制实际内容边距。

在 Step 2 的打印优化 CSS 中（或直接在 HTML 的 `<style>` 里），确保包含：

```css
@page { margin: 0; }
@media print {
  body { padding: 2cm; }
}
```

如果 HTML 已有 `@page` 规则，**必须将其 margin 改为 0**，把原来的 margin 值转移到 `@media print` 下的 `body { padding }` 中。

例如，原来是 `@page { size: A4; margin: 2cm; }`，改为：
```css
@page { size: A4; margin: 0; }
@media print { body { padding: 2cm; } }
```

## Step 3: Chrome headless 转 PDF

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --run-all-compositor-stages-before-draw \
  --print-to-pdf="<output.pdf>" \
  --print-to-pdf-no-header \
  "file://<absolute-path-to-html>"
```

关键参数：
- `--headless=new`：新版 headless 模式，渲染更准确
- `--print-to-pdf-no-header`：去掉 Chrome 默认的日期/URL 页眉页脚（作为备选，主要靠 Step 2.5 的 CSS 方案）
- `--run-all-compositor-stages-before-draw`：确保所有内容渲染完再截图

注意：HTML 路径必须是 `file://` 协议的绝对路径，中文/空格需要 URL 编码。

## Chrome 路径检测

macOS 上 Chrome 通常在：
```
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

如果不存在，尝试：
```bash
# Chromium
/Applications/Chromium.app/Contents/MacOS/Chromium
# 或通过 which 查找
which chromium || which google-chrome
```

## 验证

生成 PDF 后，用 Read 工具读取 PDF 的前几页，确认：
1. 中文是否正确显示（不是黑块/豆腐字）
2. 表格是否完整（没有被截断）
3. 排版是否紧凑（没有大片空白）

如果有问题，调整 HTML 的 CSS 后重新生成。

## 常见问题处理

| 问题 | 原因 | 解决 |
|------|------|------|
| 中文变黑块 | 字体缺失 | 在 CSS 中指定 `font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif` |
| 页眉有日期/URL | `--print-to-pdf-no-header` 在 `--headless=new` 下不可靠 | 用 CSS `@page { margin: 0 }` + `body { padding: 2cm }` 消除页眉页脚区域（见 Step 2.5） |
| 大片空白 | `page-break-inside: avoid` 过多 | 减少该属性的使用，收紧 padding/margin |
| 深色背景不显示 | 浏览器默认不打印背景色 | CSS 加 `-webkit-print-color-adjust: exact; print-color-adjust: exact` |
| 文件路径有中文/空格 | URL 编码问题 | 用 Python `urllib.parse.quote` 编码路径 |
