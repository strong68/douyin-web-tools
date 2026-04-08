# Douyin Comment Crawler

抓取一个或多个抖音视频的评论，并导出结构化结果。

## Highlights

- 抓取主评论和回复
- 导出 `JSON`、`TXT` 和 `summary.json`
- 自动清洗 emoji / 表情标签
- 清洗后为空的评论会自动丢弃

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run_crawler.py --video-ids 7601489034279456034 --max-comments 50 --output-dir output
python run_crawler.py --video-ids 7601489034279456034 7621855404343064434 --max-comments 50
python run_crawler.py --video-ids 7601489034279456034 --wait-for-login
```

## Arguments

| Argument | Description |
| --- | --- |
| `--video-ids` | 一个或多个视频 ID |
| `--max-comments` | 每个视频最多抓取多少条评论 |
| `--output-dir` | 输出目录 |
| `--wait-for-login` | 先打开抖音首页，等待手动登录 |

## Notes

- 依赖 `DrissionPage`
- 依赖抖音网页结构和接口行为

## License

MIT
