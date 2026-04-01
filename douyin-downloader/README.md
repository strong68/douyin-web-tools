# Douyin Downloader

通过视频 ID 或视频链接下载抖音视频，也支持批量下载。

## Highlights

- 下载单个视频
- 支持链接提取 ID 后下载
- 支持批量下载
- 支持 JSON 输出

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --video-id 7622566333720617819 --output-dir D:\Videos
python cli.py --url "https://www.douyin.com/video/7622566333720617819" --output-dir D:\Videos
python cli.py --video-ids 7622566333720617819,7622625510317482874 --output-dir D:\Videos
python cli.py --video-id-file video_ids.txt --output-dir D:\Videos
python cli.py --video-ids 7622566333720617819,7622625510317482874 --json
```

## Arguments

| Argument | Description |
| --- | --- |
| `--video-id` | 单个视频 ID |
| `--url` | 单个视频链接 |
| `--video-ids` | 逗号分隔的多个视频 ID |
| `--ids` | `--video-ids` 的兼容别名 |
| `--video-id-file` | 文本文件，每行一个视频 ID |
| `--file` | `--video-id-file` 的兼容别名 |
| `--output-dir` / `--output` | 输出目录 |
| `--retry-count` | 批量下载失败时的重试次数 |
| `--json` | 输出 JSON |
| `--wait-for-login` | 先打开抖音首页，等待手动登录 |

## Python

```python
from douyin_downloader import DouyinDownloader

downloader = DouyinDownloader(output_dir="D:\\Videos")
print(downloader.download_video("7622566333720617819"))
```

## Notes

- 依赖 `DrissionPage` 和 `requests`
- 私密、删除或受限视频可能无法下载

## License

MIT
