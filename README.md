# douyin-web-tools

抖音网页自动化工具集，基于 [DrissionPage](https://github.com/g1879/DrissionPage) 实现，无需抖音 APP，一个 Python 环境即可运行。

---

## 工具一览

| 工具 | 功能 |
|---|---|
| [douyin-searcher](douyin-searcher/) | 关键词搜索，支持 5 种筛选，自动翻页获取视频 id |
| [douyin-browser](douyin-browser/) | 自动浏览推荐页，提取视频 id，支持回调和人工交互 |
| [douyin-downloader](douyin-downloader/) | 视频/音频下载，单个/批量，自动跳过超长视频 |
| [douyin-comment-crawler](douyin-comment-crawler/) | 评论爬虫，去除 emoji，保存 JSON |

---

## 安装

```bash
git clone https://github.com/<your-name>/douyin-web-tools.git
cd douyin-web-tools
pip install -r requirements.txt
```

> 首次运行时会自动下载 DrissionPage 内置的 Chromium 浏览器。

---

## 快速开始

### 搜索视频
```bash
python douyin-searcher/douyin_searcher.py --keyword "搞笑视频"
```

### 浏览推荐页
```bash
python douyin-browser/douyin_browser.py
```

### 下载视频
```bash
python douyin-downloader/douyin_downloader.py --video-id 7321234567890123456
```

### 抓取评论
```bash
python douyin-comment-crawler/douyin_comment_crawler.py --video-id 7321234567890123456
```

---

## 组合使用

```python
from douyin_searcher import DouyinSearcher
from douyin_downloader import DouyinDownloader

searcher = DouyinSearcher(max_count=5)
downloader = DouyinDownloader()

result = searcher.search('美食')
ids = [v['aweme_id'] for v in result['videos']]
batch = downloader.download_many(ids)
print(f"下载完成: {batch['success']}/{batch['total']}")

searcher.close()
downloader.close()
```

---

## 项目结构

```
douyin-web-tools/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
│
├── douyin-searcher/
│   ├── douyin_searcher.py
│   └── README.md
│
├── douyin-browser/
│   ├── douyin_browser.py
│   └── README.md
│
├── douyin-downloader/
│   ├── douyin_downloader.py
│   └── README.md
│
└── douyin-comment-crawler/
    ├── douyin_comment_crawler.py
    └── README.md
```

---

## 开源协议

[MIT License](LICENSE)
