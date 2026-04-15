# ScholarAIO Published Papers Site

这是一个纯静态的 GitHub Pages 站点，用于展示 `published/` 目录下的学术综述与技术调研报告。

## 特性

- **自动生成**：从 `published/*/metadata.json` 读取元数据并生成页面
- **现代设计**：响应式布局、暗色模式、卡片式论文列表
- **实时筛选**：支持按年份、主题过滤，以及关键词搜索
- **PDF 直链**：每篇论文的 PDF 均可直接在线预览或下载

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
