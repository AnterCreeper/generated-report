#!/usr/bin/env python3
"""
Generate static site for published papers from ../published/ metadata.
Run this script after adding new papers to regenerate the site.
"""

import json
import shutil
import os
import zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
PUBLISHED_DIR = ROOT.parent / "published"
SITE_DIR = ROOT
ASSETS_PAPERS = SITE_DIR / "assets" / "papers"

def slugify(text):
    """Create URL-safe slug from text."""
    return "".join(c if c.isalnum() or c == "-" else "-" for c in text).strip("-").lower()

def load_papers():
    papers = []
    if not PUBLISHED_DIR.exists():
        print(f"Error: {PUBLISHED_DIR} does not exist")
        return papers
    for folder in sorted(PUBLISHED_DIR.iterdir(), key=lambda x: x.name, reverse=True):
        if not folder.is_dir():
            continue
        meta_path = folder / "metadata.json"
        if not meta_path.exists():
            continue
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        meta["_source_dir"] = folder.name
        meta["_slug"] = slugify(folder.name)
        papers.append(meta)
    return papers

def copy_pdfs(papers):
    """Copy PDFs into assets/papers/ for self-contained deployment."""
    if ASSETS_PAPERS.exists():
        shutil.rmtree(ASSETS_PAPERS)
    ASSETS_PAPERS.mkdir(parents=True)
    for p in papers:
        src_dir = PUBLISHED_DIR / p["_source_dir"]
        pdf_name = p.get("pdf_filename", "")
        if not pdf_name:
            continue
        src_pdf = src_dir / pdf_name
        if src_pdf.exists():
            dest_dir = ASSETS_PAPERS / p["_slug"]
            dest_dir.mkdir(exist_ok=True)
            shutil.copy2(src_pdf, dest_dir / pdf_name)
            p["_pdf_url"] = f"assets/papers/{p['_slug']}/{pdf_name}"
        else:
            p["_pdf_url"] = ""

def build_source_zips(papers):
    """Create ZIP archives containing TeX sources and images for each paper."""
    for p in papers:
        src_dir = PUBLISHED_DIR / p["_source_dir"]
        dest_dir = ASSETS_PAPERS / p["_slug"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        zip_name = f"{p['_slug']}-source.zip"
        zip_path = dest_dir / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Include all TeX files listed in metadata
            for tex_file in p.get("tex_files", []):
                tex_path = src_dir / tex_file
                if tex_path.exists():
                    zf.write(tex_path, arcname=tex_file)

            # Include images directory
            images_dir_name = p.get("images_dir", "images")
            images_dir = src_dir / images_dir_name
            if images_dir.exists() and images_dir.is_dir():
                for img_path in images_dir.rglob("*"):
                    if img_path.is_file():
                        arcname = f"{images_dir_name}/{img_path.relative_to(images_dir)}"
                        zf.write(img_path, arcname=arcname)

            # Include misc directory (supplementary materials like .bib, outlines, etc.)
            misc_dir_name = p.get("misc_dir", "misc")
            misc_dir = src_dir / misc_dir_name
            if misc_dir.exists() and misc_dir.is_dir():
                for misc_path in misc_dir.rglob("*"):
                    if misc_path.is_file():
                        arcname = f"{misc_dir_name}/{misc_path.relative_to(misc_dir)}"
                        zf.write(misc_path, arcname=arcname)

            # Include metadata.json for completeness
            meta_path = src_dir / "metadata.json"
            if meta_path.exists():
                zf.write(meta_path, arcname="metadata.json")

        p["_source_zip_url"] = f"assets/papers/{p['_slug']}/{zip_name}"
        print(f"Created source ZIP: {zip_path}")

def generate_html(papers):
    subjects = sorted(set(p.get("subject", "其他") for p in papers))
    years = sorted(set(p.get("date", "")[:4] for p in papers if p.get("date")), reverse=True)

    cards_html = []
    for p in papers:
        title = p.get("title", "Untitled")
        date = p.get("date", "")
        subject = p.get("subject", "其他")
        keywords = p.get("keywords", [])
        authors = p.get("authors", [])
        pdf_url = p.get("_pdf_url", "")
        note = p.get("note", "")
        slug = p["_slug"]

        kw_tags = "".join(f'<span class="tag">{k}</span>' for k in keywords[:6])
        author_str = ", ".join(authors) if authors else ""

        pdf_btn = f'<a class="btn btn-primary" href="{pdf_url}" target="_blank">📄 PDF</a>' if pdf_url else ""
        source_zip_url = p.get("_source_zip_url", "")
        source_btn = f'<a class="btn btn-secondary" href="{source_zip_url}" download>📦 原文获取</a>' if source_zip_url else ""

        cards_html.append(f'''
        <article class="paper-card" data-subject="{subject}" data-year="{date[:4] if date else ''}" data-keywords="{' '.join(keywords)}">
          <div class="paper-header">
            <div class="paper-meta">
              <span class="paper-date">{date}</span>
              <span class="paper-subject">{subject}</span>
            </div>
            <h2 class="paper-title">{title}</h2>
            <p class="paper-authors">{author_str}</p>
          </div>
          <div class="paper-body">
            <div class="paper-keywords">{kw_tags}</div>
            <p class="paper-note">{note}</p>
          </div>
          <div class="paper-footer">
            {pdf_btn}
            {source_btn}
            <button class="btn btn-secondary" onclick="toggleAbstract(this, '{slug}')">ℹ️ 详情</button>
          </div>
          <div class="paper-abstract" id="abs-{slug}" style="display:none;">
            <p><strong>关键词：</strong>{', '.join(keywords)}</p>
            <p><strong>归档说明：</strong>{note}</p>
            <p><strong>原始目录：</strong>{p['_source_dir']}</p>
          </div>
        </article>
        ''')

    subject_options = '\n'.join(f'<option value="{s}">{s}</option>' for s in subjects)
    year_options = '\n'.join(f'<option value="{y}">{y}</option>' for y in years)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Published Papers | ScholarAIO</title>
  <meta name="description" content="学术综述与技术调研报告归档库 - ScholarAIO Published Papers">
  <meta property="og:title" content="Published Papers | ScholarAIO">
  <meta property="og:description" content="学术综述与技术调研报告归档库">
  <meta property="og:type" content="website">
  <link rel="stylesheet" href="css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:wght@400;700&display=swap" rel="stylesheet">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <div class="brand">
        <h1>ScholarAIO</h1>
        <span class="tagline">Published Papers</span>
      </div>
      <button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">🌙</button>
    </div>
  </header>

  <main class="container">
    <section class="intro">
      <p>这是一个学术综述与技术调研报告的归档展示页面，涵盖 AI 加速器架构、硬件综合、专利分析等领域的研究成果。</p>
    </section>

    <section class="controls">
      <div class="search-box">
        <input type="text" id="search-input" placeholder="搜索标题、关键词、作者..." aria-label="Search papers">
      </div>
      <div class="filters">
        <select id="filter-year" aria-label="Filter by year">
          <option value="">全部年份</option>
          {year_options}
        </select>
        <select id="filter-subject" aria-label="Filter by subject">
          <option value="">全部主题</option>
          {subject_options}
        </select>
      </div>
      <div class="stats">
        <span id="paper-count">共 {len(papers)} 篇论文</span>
      </div>
    </section>

    <section id="papers-list" class="papers-list">
      {''.join(cards_html)}
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <p>Generated by ScholarAIO · {datetime.now().strftime("%Y-%m-%d")}</p>
    </div>
  </footer>

  <script src="js/main.js"></script>
</body>
</html>
'''

    index_path = SITE_DIR / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {index_path}")

def generate_css():
    css = '''/* ===== CSS Variables ===== */
:root {
  --bg-body: #f8f9fa;
  --bg-card: #ffffff;
  --bg-header: #ffffff;
  --text-primary: #1a1a1a;
  --text-secondary: #5a5a5a;
  --text-muted: #888888;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --border: #e5e7eb;
  --shadow: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.12);
  --radius: 10px;
  --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-serif: "Noto Serif SC", Georgia, serif;
}

[data-theme="dark"] {
  --bg-body: #0f1115;
  --bg-card: #181b21;
  --bg-header: #181b21;
  --text-primary: #f1f3f6;
  --text-secondary: #b8bdc4;
  --text-muted: #7d8592;
  --accent: #3b82f6;
  --accent-hover: #60a5fa;
  --border: #2a2f38;
  --shadow: 0 1px 3px rgba(0,0,0,0.35);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.45);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-sans);
  background: var(--bg-body);
  color: var(--text-primary);
  line-height: 1.6;
  transition: background 0.25s ease, color 0.25s ease;
}

.container {
  max-width: 920px;
  margin: 0 auto;
  padding: 0 20px;
}

/* ===== Header ===== */
.site-header {
  background: var(--bg-header);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: saturate(180%) blur(8px);
}
.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}
.brand h1 {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.tagline {
  display: inline-block;
  margin-left: 10px;
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 500;
  border-left: 1px solid var(--border);
  padding-left: 10px;
}
.theme-toggle {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
  font-size: 1.1rem;
  cursor: pointer;
  color: var(--text-secondary);
  transition: transform 0.15s ease;
}
.theme-toggle:hover { transform: scale(1.05); }

/* ===== Intro ===== */
.intro {
  margin: 28px 0 18px;
  color: var(--text-secondary);
  font-size: 1.05rem;
}

/* ===== Controls ===== */
.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 22px;
}
.search-box { flex: 1 1 260px; }
.search-box input {
  width: 100%;
  padding: 10px 14px;
  font-size: 0.95rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  color: var(--text-primary);
  outline: none;
}
.search-box input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.12); }

.filters { display: flex; gap: 10px; flex: 1 1 220px; }
.filters select {
  flex: 1;
  padding: 10px 12px;
  font-size: 0.92rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg-card);
  color: var(--text-primary);
  cursor: pointer;
}

.stats {
  flex: 0 0 auto;
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* ===== Papers List ===== */
.papers-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18px;
  padding-bottom: 40px;
}

.paper-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px;
  box-shadow: var(--shadow);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.paper-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}
.paper-header { margin-bottom: 12px; }
.paper-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.paper-subject {
  background: rgba(37,99,235,0.08);
  color: var(--accent);
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 500;
}
[data-theme="dark"] .paper-subject {
  background: rgba(59,130,246,0.12);
}
.paper-title {
  font-family: var(--font-serif);
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.45;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.paper-authors {
  font-size: 0.88rem;
  color: var(--text-secondary);
}
.paper-body { margin-bottom: 14px; }
.paper-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag {
  font-size: 0.78rem;
  background: var(--bg-body);
  color: var(--text-secondary);
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid var(--border);
}
.paper-note {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.55;
}
.paper-footer {
  display: flex;
  gap: 10px;
  align-items: center;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 0.88rem;
  font-weight: 500;
  border-radius: 8px;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: background 0.15s ease;
}
.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-secondary:hover { background: var(--bg-body); color: var(--text-primary); }

.paper-abstract {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed var(--border);
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.6;
}
.paper-abstract p { margin-bottom: 6px; }

/* ===== Footer ===== */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 24px 0;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* ===== Responsive ===== */
@media (max-width: 600px) {
  .header-inner { height: 58px; }
  .brand h1 { font-size: 1.1rem; }
  .tagline { display: none; }
  .controls { flex-direction: column; align-items: stretch; }
  .filters { width: 100%; }
  .paper-title { font-size: 1.05rem; }
  .paper-card { padding: 16px; }
}
'''
    css_path = SITE_DIR / "css" / "style.css"
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"Generated {css_path}")

def generate_js():
    js = '''(function() {
  const searchInput = document.getElementById('search-input');
  const filterYear = document.getElementById('filter-year');
  const filterSubject = document.getElementById('filter-subject');
  const papersList = document.getElementById('papers-list');
  const countLabel = document.getElementById('paper-count');
  const themeToggle = document.getElementById('theme-toggle');
  const cards = Array.from(document.querySelectorAll('.paper-card'));

  function updateCount(n) {
    countLabel.textContent = '共 ' + n + ' 篇论文';
  }

  function filterPapers() {
    const term = searchInput.value.trim().toLowerCase();
    const year = filterYear.value;
    const subject = filterSubject.value;
    let visible = 0;

    cards.forEach(card => {
      const text = card.innerText.toLowerCase();
      const cardYear = card.dataset.year || '';
      const cardSubject = card.dataset.subject || '';
      const matchText = !term || text.includes(term);
      const matchYear = !year || cardYear === year;
      const matchSubject = !subject || cardSubject === subject;
      const show = matchText && matchYear && matchSubject;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    updateCount(visible);
  }

  searchInput.addEventListener('input', filterPapers);
  filterYear.addEventListener('change', filterPapers);
  filterSubject.addEventListener('change', filterPapers);

  window.toggleAbstract = function(btn, slug) {
    const el = document.getElementById('abs-' + slug);
    if (!el) return;
    const isHidden = el.style.display === 'none';
    el.style.display = isHidden ? 'block' : 'none';
    btn.textContent = isHidden ? '🔼 收起' : 'ℹ️ 详情';
  };

  /* Theme toggle */
  const storedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  function applyTheme(dark) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    themeToggle.textContent = dark ? '☀️' : '🌙';
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }
  applyTheme(storedTheme ? storedTheme === 'dark' : prefersDark);
  themeToggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    applyTheme(!isDark);
  });
})();
'''
    js_path = SITE_DIR / "js" / "main.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"Generated {js_path}")

def generate_readme():
    readme = '''# ScholarAIO Published Papers Site

这是一个纯静态的 GitHub Pages 站点，用于展示 `published/` 目录下的学术综述与技术调研报告。

## 特性

- **自动生成**：从 `published/*/metadata.json` 读取元数据并生成页面
- **现代设计**：响应式布局、暗色模式、卡片式论文列表
- **实时筛选**：支持按年份、主题过滤，以及关键词搜索
- **PDF 直链**：每篇论文的 PDF 均可直接在线预览或下载
- **原文获取**：每篇论文提供 ZIP 压缩包下载，包含完整 TeX 源文件与插图
- **原文获取**：每篇论文提供 ZIP 压缩包下载，包含完整 TeX 源文件与插图

## 本地预览

```bash
cd published-site
python -m http.server 8000
# 打开 http://localhost:8000
```

## 重新生成站点

当 `published/` 中新增或修改论文后，运行：

```bash
cd published-site
python generate.py
```

## 部署到 GitHub Pages

### 方式一：作为独立仓库（推荐）

1. 在 GitHub 上创建新仓库（例如 `yourname/published-papers`）
2. 将 `published-site/` 目录初始化为 git 仓库并推送：

```bash
cd published-site
git init
git add .
git commit -m "Initial site"
git branch -M main
git remote add origin https://github.com/yourname/published-papers.git
git push -u origin main
```

3. 进入仓库 Settings → Pages → Source，选择 **Deploy from a branch**，分支选 `main`，文件夹选 `/ (root)`
4. 等待几分钟后，访问 `https://yourname.github.io/published-papers/`

### 方式二：作为项目子目录（若需挂载到子路径）

如果站点需要部署在 `https://yourname.github.io/scholaraio/published-site/`，请修改 `generate.py` 中的 `BASE_URL` 变量，然后重新生成。
'''
    readme_path = SITE_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"Generated {readme_path}")

def main():
    papers = load_papers()
    if not papers:
        print("No papers found.")
        return
    print(f"Found {len(papers)} papers.")
    copy_pdfs(papers)
    build_source_zips(papers)
    generate_html(papers)
    generate_css()
    generate_js()
    generate_readme()
    print("Done.")

if __name__ == "__main__":
    main()
