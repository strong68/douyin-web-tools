# Douyin Browser

浏览抖音推荐页，并提取当前视频的 `video_id`。

## Highlights

- 自动进入推荐页
- 逐个读取当前视频 ID
- 支持交互式浏览
- 支持边浏览边下载

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python cli.py --mode interactive --max-count 10
python cli.py --mode interactive --wait-for-login
python cli.py --mode download --max-count 10 --output-dir D:\Videos
```

## Arguments

| Argument | Description |
| --- | --- |
| `--mode` | `interactive` 或 `download` |
| `--max-count` | 最多浏览多少个视频 |
| `--output-dir` | 下载模式输出目录 |
| `--wait-for-login` | 先打开抖音首页，等待手动登录 |

## Python

```python
from douyin_browser import DouyinBrowser

browser = DouyinBrowser()
browser.browse_loop(max_count=10)
```

## Notes

- 依赖 `DrissionPage`
- `download` 模式要求可导入 `douyin_downloader`

## License

MIT
