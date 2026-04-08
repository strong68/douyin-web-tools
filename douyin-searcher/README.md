# douyin-searcher

抖音关键词搜索工具，输入关键词 + 筛选条件，自动翻页获取视频 id 列表。

## 功能

- 关键词搜索
- 5 种筛选条件：排序 / 发布时间 / 视频时长 / 搜索范围 / 内容类型
- 自动滚动翻页，支持深度抓取
- 支持单独运行和代码调用

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
python douyin_searcher.py --keyword "搞笑视频"

# 指定数量和筛选
python douyin_searcher.py --keyword "美食" --max-count 20 --sort latest --publish-time week

# 输出 JSON
python douyin_searcher.py --keyword "教程" --json
```

## 代码调用

```python
from douyin_searcher import DouyinSearcher

searcher = DouyinSearcher(
    max_count=20,
    sort='latest',
    publish_time='week',
    content_type='video',
)
result = searcher.search('搞笑视频')
for video in result['videos']:
    print(video['aweme_id'])
searcher.close()
```

## 筛选参数

| 参数 | 可选值 |
|---|---|
| `--sort` | `comprehensive` / `latest` / `most_liked` |
| `--publish-time` | `any` / `day` / `week` / `half_year` |
| `--duration` | `any` / `under_1_minute` / `1_to_5_minutes` / `over_5_minutes` |
| `--scope` | `any` / `following` / `recently_watched` / `unwatched` |
| `--content-type` | `any` / `video` / `image_text` |

详细 API 文档见 [详细说明.md](./详细说明.md)。
