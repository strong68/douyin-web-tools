# Douyin Searcher

根据关键词搜索抖音视频，并返回视频 ID 与基础元数据。

## Highlights

- 根据关键词执行网页搜索
- 支持限制结果数量
- 支持筛选项自由组合
- 支持 JSON 输出

默认筛选为：`latest + unwatched + video`

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --keyword "测试" --max-count 10
python cli.py --keyword "测试" --max-count 10 --wait-for-login
python cli.py --keyword "测试" --sort latest --scope unwatched --content-type video
python cli.py --keyword "测试" --max-count 10 --json
```

## Arguments

| Argument | Description |
| --- | --- |
| `--keyword` | 搜索关键词 |
| `--max-count` | 最多返回多少条结果 |
| `--max-results` / `--max` | `--max-count` 的兼容别名 |
| `--sort` | `comprehensive` / `latest` / `most_liked` |
| `--publish-time` | `any` / `day` / `week` / `half_year` |
| `--duration` | `any` / `under_1_minute` / `1_to_5_minutes` / `over_5_minutes` |
| `--scope` | `any` / `following` / `recently_watched` / `unwatched` |
| `--content-type` | `any` / `video` / `image_text` |
| `--json` | 输出 JSON |
| `--wait-for-login` | 先打开抖音首页，等待手动登录 |

## Python

```python
from douyin_searcher import DouyinSearcher

searcher = DouyinSearcher(max_count=10, sort="latest", scope="unwatched", content_type="video")
result = searcher.search("测试")
print(result["videos"])
```

## Notes

- 依赖 `DrissionPage`
- 只负责搜索，不负责下载

## License

MIT
