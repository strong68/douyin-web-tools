# douyin-web-tools

抖音网页自动化工具集，基于 [DrissionPage](https://github.com/g1879/DrissionPage) 实现，无需抖音 APP，无需浏览器驱动，一个 Python 环境即可运行。

---

## 工具一览

| 工具 | 功能 | 依赖 |
|---|---|---|
| [douyin-searcher](douyin-searcher/) | 关键词搜索，支持 5 种筛选条件，自动翻页获取视频 id | DrissionPage |
| [douyin-browser](douyin-browser/) | 自动浏览推荐页，逐条提取视频 id，支持回调和人工交互 | DrissionPage |
| [douyin-downloader](douyin-downloader/) | 下载视频/音频，支持单个/批量，续传不重复下载 | DrissionPage + requests |
| [douyin-comment-crawler](douyin-comment-crawler/) | 抓取视频评论和回复，去除 emoji，支持翻页和展开回复 | DrissionPage |

---

## 安装

### 环境要求

- Python 3.8+
- Chrome / Chromium（DrissionPage 内置驱动会自动处理）

### 步骤

```bash
# 克隆项目
git clone https://github.com/<your-name>/douyin-web-tools.git
cd douyin-web-tools

# 安装依赖
pip install -r requirements.txt
```

> `DrissionPage` 会自动下载内置 Chromium 浏览器，首次运行时会提示安装。

---

## 快速开始

### 搜索视频

```bash
python douyin-searcher/douyin_searcher.py --keyword "搞笑视频" --max-count 20
```

### 浏览推荐页（回调模式）

```bash
python douyin-browser/douyin_browser.py --max-count 10
```

### 下载视频

```bash
# 单个
python douyin-downloader/douyin_downloader.py --video-id 7321234567890123456

# 批量
python douyin-downloader/douyin_downloader.py --video-ids 7321...,7322...,7323...
```

### 抓取评论

```bash
python douyin-comment-crawler/douyin_comment_crawler.py --video-id 7321234567890123456 --max-comments 100
```

---

## 工具组合使用

```python
from douyin_searcher import DouyinSearcher
from douyin_downloader import DouyinDownloader
from douyin_comment_crawler import DouyinCommentCrawler

# 搜索 → 下载
searcher = DouyinSearcher(max_count=5, sort='most_liked')
downloader = DouyinDownloader()

result = searcher.search('美食')
video_ids = [v['aweme_id'] for v in result['videos']]
batch = downloader.download_many(video_ids)
print(f"下载完成：{batch['success']}/{batch['total']}")

searcher.close()
downloader.close()
```

---

## 项目结构

```
douyin-web-tools/
├── README.md                        # 本文件
├── LICENSE                          # MIT 开源协议
├── requirements.txt                  # Python 依赖
├── .gitignore                       # Git 忽略文件
│
├── douyin-searcher/                 # 关键词搜索工具
│   ├── douyin_searcher.py            # 源码
│   ├── README.md                     # 使用说明
│   └── 详细说明.md                    # 详细 API 文档
│
├── douyin-browser/                  # 推荐页浏览工具
│   ├── douyin_browser.py             # 源码
│   ├── README.md                     # 使用说明
│   └── 详细说明.md                    # 详细 API 文档
│
├── douyin-downloader/               # 视频下载工具
│   ├── douyin_downloader.py         # 源码
│   ├── README.md                     # 使用说明
│   └── 详细说明.md                    # 详细 API 文档
│
└── douyin-comment-crawler/          # 评论爬虫工具
    ├── douyin_comment_crawler.py     # 源码
    ├── README.md                     # 使用说明
    └── 详细说明.md                    # 详细 API 文档
```

---

## 开源协议

本项目采用 [MIT License](LICENSE) 开源，欢迎 fork、star 和 Pull Request。
