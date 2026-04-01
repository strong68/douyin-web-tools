# Douyin Tools Monorepo

一个围绕抖音网页自动化整理的 Python 工具仓库，面向学习、研究、测试和持续改进。

这个仓库把常见需求拆成 4 个独立子项目，而不是把所有逻辑堆在同一个脚本里。这样更容易阅读、验证、维护，也更适合在 GitHub 上持续协作。

## Overview

| Project | What It Does | Entry |
| --- | --- | --- |
| `douyin_comment_crawler` | 抓取评论并导出结果 | `python run_crawler.py ...` |
| `douyin-browser` | 浏览推荐页并提取视频 ID | `python cli.py ...` |
| `douyin-searcher` | 根据关键词搜索视频 | `python cli.py ...` |
| `douyin-downloader` | 下载视频或音频 | `python cli.py ...` |

## Why This Repo

- 结构更清楚：每个功能都是独立子项目，职责单一
- 更容易检查：代码量已做过收敛，参数风格尽量统一
- 更接近真实使用：默认复用本机浏览器登录态
- 更适合协作：已经补齐开源仓库常用的文档和 issue 模板

## Quick Start

进入目标子项目后安装依赖并运行：

```bash
cd douyin-searcher
pip install -r requirements.txt
python cli.py --keyword "测试" --max-count 5 --wait-for-login
```

`--wait-for-login` 会先打开抖音首页，等待手动登录，再继续执行后续流程。

## Projects

### `douyin_comment_crawler`

- 用途：抓取一个或多个视频的评论
- 输出：`json`、`txt`、`summary.json`
- 文档：[douyin_comment_crawler/README.md](C:\Users\chenhj\Desktop\douyin\douyin_comment_crawler\README.md)

### `douyin-browser`

- 用途：浏览推荐页并提取当前视频 ID
- 模式：交互浏览 / 边浏览边下载
- 文档：[douyin-browser/README.md](C:\Users\chenhj\Desktop\douyin\douyin-browser\README.md)

### `douyin-searcher`

- 用途：按关键词搜索视频
- 特点：支持筛选组合与 JSON 输出
- 文档：[douyin-searcher/README.md](C:\Users\chenhj\Desktop\douyin\douyin-searcher\README.md)

### `douyin-downloader`

- 用途：按视频 ID 或链接下载内容
- 特点：支持单个下载和批量下载
- 文档：[douyin-downloader/README.md](C:\Users\chenhj\Desktop\douyin\douyin-downloader\README.md)

## Dependencies

本仓库的网页自动化能力主要建立在 [`DrissionPage`](https://www.drissionpage.cn/) 之上。它承担了浏览器控制、监听请求和页面交互等关键工作，是这个项目能够保持简洁实现的重要原因。

如果你觉得这个仓库对你有帮助，也建议关注和支持 [`DrissionPage`](https://www.drissionpage.cn/) 项目。

下载器额外依赖：

- `requests`

## Repository Layout

```text
.
├─ .github/
├─ douyin_comment_crawler/
├─ douyin-browser/
├─ douyin-searcher/
├─ douyin-downloader/
├─ README.md
├─ CONTRIBUTING.md
├─ LICENSE
└─ .gitignore
```

## Notes

- 默认复用本机浏览器登录态，不使用自定义浏览器端口
- 页面结构、登录状态、权限和地区限制都可能影响结果
- 本仓库基于网页自动化，页面改版后可能需要同步调整
- 使用时请遵守抖音平台规则、服务条款以及当地法律法规
- 建议仅用于学习、研究和自动化测试

## Contributing

欢迎继续交流和改进：

- 协作说明：[CONTRIBUTING.md](C:\Users\chenhj\Desktop\douyin\CONTRIBUTING.md)
- Issue 模板：`.github/ISSUE_TEMPLATE/`

## License

MIT
