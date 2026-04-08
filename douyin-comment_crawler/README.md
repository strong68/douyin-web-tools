# douyin-comment-crawler

抖音视频评论爬虫，抓取评论和回复，去除 emoji，保存为 JSON。

## 功能

- 主评论 + 嵌套回复
- 自动展开"查看更多回复"
- 去除 emoji / 表情符号
- 自动翻页
- 保存视频信息 + 作者信息 + 评论数据
- 评论 > 1000 条自动跳过

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
# 默认 100 条
python douyin_comment_crawler.py --video-id 7321234567890123456

# 指定数量和目录
python douyin_comment_crawler.py --video-id 7321234567890123456 --max-comments 200 --output-dir D:\comments
```

结果保存为 `{video_id}_comments.json`。

## JSON 输出

```json
{
  "video_id": "7321234567890123456",
  "video": {"caption": "标题", "tags": [], "video_link": "..."},
  "author": {"uid": "...", "nickname": "...", "homepage_link": "..."},
  "comment_summary": {"total_count": 5000, "collection_limit": 200, "collected_count": 200},
  "comments": {
    "cid_001": {
      "text": "评论正文",
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
result = crawler.crawl_video_comments(video_id='7321234567890123456', max_comments=200)
print(f"抓取 {result['comment_summary']['collected_count']} 条评论")
crawler.close()
```
