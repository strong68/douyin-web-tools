# douyin-downloader

抖音视频 / 音频下载工具，单个 / 批量下载，自动跳过超长视频。

## 功能

- 单个 / 批量下载
- 自动识别视频(.mp4)/音频(.mp3)
- 超长视频自动跳过
- 断点续传，不重复下载
- 退出码支持 CI/CD

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
# 单个
python douyin_downloader.py --video-id 7321234567890123456

# 批量
python douyin_downloader.py --video-ids 7321...,7322...,7323...

# 指定目录
python douyin_downloader.py --video-ids 7321... --output-dir D:\downloads

# 跳过超长视频
python douyin_downloader.py --video-ids 7321... --max-duration-seconds 60

# JSON 输出
python douyin_downloader.py --video-ids 7321... --json
```

## 代码调用

```python
from douyin_downloader import DouyinDownloader

downloader = DouyinDownloader()

# 单个
result = downloader.download_video('7321234567890123456')
print(result['message'])

# 批量
batch = downloader.download_many(['7321...', '7322...'])
print(f"成功 {batch['success']}/{batch['total']}")

downloader.close()
```
