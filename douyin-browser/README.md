# douyin-browser

抖音推荐页自动浏览工具，逐条读取视频 id，支持回调函数处理和人工交互模式。

## 功能

- 自动进入抖音推荐页
- 监听推荐接口，实时提取当前视频 id
- 支持回调函数（自动化场景）
- 支持人工按键交互（手动确认）
- 自动重连，断点恢复

## 安装

```bash
pip install -r ../requirements.txt
```

## 命令行（人工交互）

```bash
python douyin_browser.py

# 指定浏览数量
python douyin_browser.py --max-count 10
```

运行后每遇到一条视频会暂停，按 **Enter** 继续浏览，按 **q** 退出。

## 代码调用（回调模式）

```python
from douyin_browser import DouyinBrowser
from douyin_downloader import DouyinDownloader

downloader = DouyinDownloader()

def handle_video(video_id: str) -> bool:
    print(f'获取到视频 id: {video_id}')
    result = downloader.download_video(video_id)
    print(f"下载结果: {result['message']}")
    return True  # 返回 False 可停止循环

browser = DouyinBrowser()
browser.browse_loop(callback=handle_video, max_count=20)
browser.close()
downloader.close()
```

详细 API 文档见 [详细说明.md](./详细说明.md)。
