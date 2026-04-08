# douyin-downloader

抖音视频 / 音频下载工具，支持单个和批量下载，自动跳过超长视频，已下载文件不重复下载。

## 功能

- 单个视频下载
- 逗号分隔批量下载
- 自动识别视频（.mp4）和音频（.mp3）
- 超长视频自动跳过
- 断点续传，已存在文件不重复下载
- 返回退出码，支持 CI/CD 集成

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
# 单个
python douyin_downloader.py --video-id 7321234567890123456

# 批量（逗号分隔）
python douyin_downloader.py --video-ids 7321...,7322...,7323...

# 指定目录
python douyin_downloader.py --video-ids 7321... --output-dir D:\downloads

# 跳过超过 60 秒的视频
python douyin_downloader.py --video-ids 7321... --max-duration-seconds 60

# 输出 JSON
python douyin_downloader.py --video-ids 7321... --json
```

## 代码调用

```python
from douyin_downloader import DouyinDownloader

downloader = DouyinDownloader(max_duration_seconds=120)

# 单个
result = downloader.download_video('7321234567890123456')
print(f"{result['video_id']}: {result['message']}")

# 批量
batch = downloader.download_many(['7321...', '7322...'])
print(f"成功 {batch['success']}/{batch['total']}")

downloader.close()
```

详细 API 文档见 [详细说明.md](./详细说明.md)。
