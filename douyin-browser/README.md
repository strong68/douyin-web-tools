# douyin-browser

抖音推荐页自动浏览工具，逐条获取视频 id，支持回调和人工交互。

## 功能

- 自动进入推荐页
- 实时提取当前视频 id
- 回调模式（自动化）/ 人工交互模式
- 自动重连，断点恢复

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行

```bash
python douyin_browser.py

# 指定数量
python douyin_browser.py --max-count 10
```

运行后按 **Enter** 继续，**q** 退出。

## 代码调用

```python
from douyin_browser import DouyinBrowser
from douyin_downloader import DouyinDownloader

downloader = DouyinDownloader()

def handle_video(video_id: str) -> bool:
    print(f'视频: {video_id}')
    result = downloader.download_video(video_id)
    return result['success']

browser = DouyinBrowser()
browser.browse_loop(callback=handle_video, max_count=20)
browser.close()
downloader.close()
```
