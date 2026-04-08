# 🎵 douyin-web-tools

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <b>抖音网页自动化工具集</b><br>
  无需 APP · 无需逆向 · 开箱即用
</p>

---

## ✨ 特性

- 🚀 **零配置** - 基于 DrissionPage，自动管理浏览器
- 🔧 **模块化** - 4 个独立工具，按需使用
- 🐍 **纯 Python** - 代码简洁，易于二次开发
- 📦 **无侵入** - 不修改系统，不注入进程

---

## 📦 工具一览

| 工具 | 功能 | 场景 |
|:---|:---|:---|
| 🔍 [douyin-searcher](douyin-searcher/) | 关键词搜索 + 5 种筛选 | 批量获取视频 id |
| 🌐 [douyin-browser](douyin-browser/) | 自动浏览推荐页 | 实时监控热门内容 |
| ⬇️ [douyin-downloader](douyin-downloader/) | 视频/音频下载 | 素材采集、备份 |
| 💬 [douyin-comment-crawler](douyin-comment-crawler/) | 评论爬虫 | 舆情分析、数据挖掘 |

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/<your-name>/douyin-web-tools.git
cd douyin-web-tools
pip install -r requirements.txt
```

> 💡 首次运行会自动下载 Chromium 浏览器（DrissionPage 内置）

### 1. 搜索视频

```bash
python douyin-searcher/douyin_searcher.py --keyword "美食教程" --max-count 20
```

### 2. 下载视频

```bash
python douyin-downloader/douyin_downloader.py --video-id 7321234567890123456
```

### 3. 抓取评论

```bash
python douyin-comment-crawler/douyin_comment_crawler.py \
  --video-id 7321234567890123456 \
  --max-comments 200
```

### 4. 浏览推荐页

```bash
python douyin-browser/douyin_browser.py --max-count 10
```

---

## 🔗 组合使用示例

```python
from douyin_searcher import DouyinSearcher
from douyin_downloader import DouyinDownloader
from douyin_comment_crawler import DouyinCommentCrawler

# 搜索 → 下载 → 抓评论
searcher = DouyinSearcher(max_count=5, sort='most_liked')
downloader = DouyinDownloader()
crawler = DouyinCommentCrawler()

result = searcher.search('美食探店')
for video in result['videos']:
    vid = video['aweme_id']
    
    # 下载视频
    dl_result = downloader.download_video(vid)
    if dl_result['success']:
        print(f"✓ 下载成功: {vid}")
    
    # 抓取评论
    crawler.crawl_video_comments(vid, max_comments=100)

searcher.close()
downloader.close()
crawler.close()
```

---

## 📁 项目结构

```
douyin-web-tools/
├── 📄 README.md                 # 本文件
├── 📄 LICENSE                   # MIT 开源协议
├── 📄 requirements.txt          # 依赖清单
├── 📄 .gitignore               # Git 忽略规则
│
├── 🔍 douyin-searcher/         # 关键词搜索
│   ├── douyin_searcher.py
│   └── README.md
│
├── 🌐 douyin-browser/          # 推荐页浏览
│   ├── douyin_browser.py
│   └── README.md
│
├── ⬇️ douyin-downloader/       # 视频下载
│   ├── douyin_downloader.py
│   └── README.md
│
└── 💬 douyin-comment-crawler/  # 评论爬虫
    ├── douyin_comment_crawler.py
    └── README.md
```

---

## 🛠️ 环境要求

| 项目 | 版本 |
|:---|:---|
| Python | 3.8+ |
| DrissionPage | 4.0+ |
| 操作系统 | Windows / macOS / Linux |

---

## 🤝 贡献指南

欢迎 Issue 和 PR！

1. Fork 本仓库
2. 创建分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -am 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

---

## ⚠️ 免责声明

本工具仅供学习研究使用，请勿用于：
- 大规模爬取他人数据
- 侵犯用户隐私
- 违反抖音平台规则的行为

使用本工具产生的任何法律责任由使用者自行承担。

---

## 📜 开源协议

[MIT License](LICENSE) © 2025 douyin-web-tools

---

<p align="center">
  如果这个项目对你有帮助，请给个 ⭐ Star！
</p>
