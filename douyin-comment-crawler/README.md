# douyin-comment-crawler

抖音视频评论爬虫，自动抓取评论和回复，去除 emoji 噪音，保存为结构化 JSON。

## 功能

- 抓取主评论和嵌套回复
- 自动展开"查看更多回复"
- 去除 emoji、表情符号
- 自动翻页，直到到达数量上限或翻到底
- 保存视频信息 + 作者信息 + 评论数据
- 评论超过 1000 条时自动跳过（可自定义阈值）

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
# 默认抓取 100 条
python douyin_comment_crawler.py --video-id 7321234567890123456

# 指定数量和保存目录
python douyin_comment_crawler.py --video-id 7321234567890123456 --max-comments 200 --output-dir D:\comments
```

结果保存为 `{video_id}_comments.json`。

## JSON 输出格式

```json
{
  "video_id": "7321234567890123456",
  "create_time": "2025-04-08 16:00:00",
  "platform": "douyin",
  "video": {
    "caption": "视频标题",
    "tags": ["标签1"],
    "video_link": "https://www.douyin.com/video/7321234567890123456"
  },
  "author": {
    "uid": "12345678",
    "nickname": "作者昵称",
    "homepage_link": "https://www.douyin.com/user/MS4..."
  },
  "comment_summary": {
    "total_count": 5000,
    "collection_limit": 200,
    "collected_count": 200
  },
  "comments": {
    "cid_001": {
      "comment_id": "cid_001",
      "text": "评论正文（已清洗）",
      "comment_time": "2025-04-08 14:30:00",
      "comment_ip": "北京",
      "like_count": 1234,
      "reply_comments": [...]
    }
  }
}
```

## 代码调用

```python
from douyin_comment_crawler import DouyinCommentCrawler

crawler = DouyinCommentCrawler()
result = crawler.crawl_video_comments(
    video_id='7321234567890123456',
    max_comments=200,
)
print(f"共抓取 {result['comment_summary']['collected_count']} 条评论")
crawler.close()
```

详细 API 文档见 [详细说明.md](./详细说明.md)。
