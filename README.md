# FastMoss Weekly Pages

这是可直接上传到公网静态托管的 FastMoss 每周视频复刻报告站点。

## Codex Skill

- 可安装压缩包：`skill-packages/fastmoss-daily-video-analysis.zip`
- 展开源码：`skills/fastmoss-daily-video-analysis/`

安装方式：把压缩包解压到对方电脑的 `$CODEX_HOME/skills/` 目录，最终目录应为 `$CODEX_HOME/skills/fastmoss-daily-video-analysis/SKILL.md`。

## 上传方式

- GitHub Pages：上传本目录全部文件，Pages 来源选择 `main` 分支根目录。
- Vercel / Netlify：导入本目录作为静态站点，无需构建命令。
- 任意静态服务器：把本目录作为网站根目录。

## 每周更新

1. 生成新的可视化报告目录。
2. 复制到 `reports/YYYY-MM-DD/`，该目录需要包含 `index.html`、`data.csv`、`visual-report-manifest.json` 和 `assets/`。
3. 在 `reports.json` 顶部新增本周报告记录。
4. 运行 `python scripts/render-premium-site.py` 重新生成首页和报告页的高级版静态页面。
