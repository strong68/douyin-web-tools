# -*- coding: utf-8 -*-

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from DrissionPage import Chromium

COMMENT_COUNT_XPATH = (
    'x://*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div[2]/span'
)
COMMENT_LIST_XPATH = 'x://*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[5]/div/div/div[3]/div'
COMMENT_SCROLL_XPATH = 'x://div[contains(@class, "parent-route-container route-scroll-container IhmVuo1S")]'
COMMENT_END_XPATH = (
    'x://*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[5]/div/div/div[3]/div[{index}]'
)
COMMENT_REPLY_PANEL_XPATH = 'x://div[contains(@class, "eBcBNgnP NfyOpHiT")]'
COMMENT_EXPAND_CLASSES = {'FgYRerj2', 'J_mtqkIZ comment-reply-expand-btn'}
NO_MORE_COMMENT_TEXT = '暂时没有更多评论'
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
MEANINGFUL_TEXT_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')


class DouyinCommentCrawler:
    def __init__(
        self,
        output_dir: str = 'output',
        browser: Optional[Chromium] = None,
        wait_for_login: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.browser = browser or Chromium()
        self.wait_for_login = wait_for_login
        self._login_checked = False

    def ensure_login(self) -> None:
        if not self.wait_for_login or self._login_checked:
            return
        login_tab = self.browser.new_tab()
        login_tab.get('https://www.douyin.com/')
        input('Please complete Douyin login in the browser, then press Enter to continue: ')
        self._safe_close_tab(login_tab)
        self._login_checked = True

    @staticmethod
    def _safe_close_tab(tab: Any) -> None:
        if tab is None:
            return
        try:
            tab.close()
        except Exception:
            pass

    @staticmethod
    def _response_to_dict(response: Any) -> Dict[str, Any]:
        body = getattr(response, 'body', None)
        if isinstance(body, dict):
            return body
        if isinstance(body, str):
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    @staticmethod
    def _clean_comment_text(text: str) -> str:
        cleaned = EMOJI_PATTERN.sub('', str(text or ''))
        cleaned = re.sub(r'\[[^\]]+\]', '', cleaned)
        cleaned = cleaned.replace('[', '').replace(']', '')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if MEANINGFUL_TEXT_PATTERN.search(cleaned) else ''

    @staticmethod
    def _parse_count(raw_text: str) -> Optional[int]:
        text = str(raw_text or '').strip().replace(',', '').replace('+', '')
        if not text or '抢' in text:
            return None
        multiplier = 10000 if text.endswith('万') else 1
        if multiplier == 10000:
            text = text[:-1]
        try:
            return int(float(text) * multiplier)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _count_comments(result: Dict[str, Any]) -> int:
        seen_ids = set()
        for comment in result.get('comments', {}).values():
            comment_id = comment.get('comment_id')
            if comment_id and (comment.get('text') or comment.get('comment_time')):
                seen_ids.add(comment_id)
            for reply in comment.get('reply_comments', []):
                reply_id = reply.get('comment_id')
                if reply_id:
                    seen_ids.add(reply_id)
        return len(seen_ids)

    def _merge_comments(self, result: Dict[str, Any], comments: Iterable[Dict[str, Any]], max_comments: int) -> None:
        for item in comments:
            if self._count_comments(result) >= max_comments:
                return

            comment_id = item.get('cid', '')
            cleaned_text = self._clean_comment_text(item.get('text', ''))
            if not cleaned_text:
                continue

            created_at = datetime.fromtimestamp(item.get('create_time', 0) or 0)
            comment_data = {
                'comment_id': comment_id,
                'text': cleaned_text,
                'comment_time': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'comment_ip': item.get('ip_label', ''),
                'like_count': item.get('digg_count', 0),
                'reply_comments': [],
            }

            reply_id = item.get('reply_id', '')
            if reply_id == '0':
                result['comments'][comment_id] = comment_data
            else:
                parent = result['comments'].setdefault(
                    reply_id,
                    {
                        'comment_id': reply_id,
                        'text': '',
                        'comment_time': '',
                        'comment_ip': '',
                        'like_count': 0,
                        'reply_comments': [],
                    },
                )
                parent['reply_comments'].append(comment_data)

            reply_comments = item.get('reply_comment', [])
            if reply_comments:
                self._merge_comments(result, reply_comments, max_comments)

    @staticmethod
    def _build_text_line(index: int, label: str, item: Dict[str, Any]) -> List[str]:
        return [
            (
                f"{index}. [{label}] id={item.get('comment_id', '')} "
                f"time={item.get('comment_time', '')} "
                f"ip={item.get('comment_ip', '')} "
                f"likes={item.get('like_count', 0)}"
            ),
            item.get('text', ''),
            '',
        ]

    def _build_text_report(self, video_id: str, result: Dict[str, Any]) -> str:
        lines: List[str] = [f'video_id={video_id}', '']
        index = 1
        for root in result.get('comments', {}).values():
            if root.get('text'):
                lines.extend(self._build_text_line(index, '主评论', root))
                index += 1
            for reply in root.get('reply_comments', []):
                lines.extend(self._build_text_line(index, '回复', reply))
                index += 1
        if index == 1:
            lines.append('未抓取到评论内容。')
        return '\n'.join(lines)

    def _save_json(self, name: str, payload: Any) -> Path:
        path = self.output_dir / f'{name}.json'
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=4), encoding='utf-8')
        return path

    def crawl_video_comments(self, video_id: str, max_comments: int = 50) -> Dict[str, Any]:
        self.ensure_login()
        base_url = f'https://www.douyin.com/video/{video_id}'

        detail_tab = self.browser.new_tab()
        detail_tab.listen.start('aweme/detail/?device_platform')
        detail_tab.get(base_url)
        detail_result = self._response_to_dict(detail_tab.listen.wait().response)
        self._safe_close_tab(detail_tab)

        aweme_detail = detail_result.get('aweme_detail')
        if not aweme_detail:
            raise ValueError(f'未获取到视频详情数据: {video_id}')

        result: Dict[str, Any] = {
            'video_id': video_id,
            'create_time': datetime.fromtimestamp(aweme_detail['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'platform': 'douyin',
            'video': {
                'caption': aweme_detail.get('desc', ''),
                'tags': aweme_detail.get('video_tag', []),
                'share_link': aweme_detail.get('share_info', {}).get('share_url', ''),
            },
            'author': {'uid': aweme_detail.get('author_user_id', '')},
            'comments': {},
            'comment_summary': {
                'display_count': '',
                'total_count': None,
                'collection_limit': max_comments,
                'collected_count': 0,
            },
        }

        author_tab = self.browser.new_tab()
        author_tab.listen.start('web/user/profile/other/?device_platform')
        author_tab.get(f"https://www.douyin.com/user/{aweme_detail['author']['sec_uid']}")
        author_result = self._response_to_dict(author_tab.listen.wait().response)
        self._safe_close_tab(author_tab)

        user = author_result.get('user', {})
        result['author'].update(
            {
                'nickname': user.get('nickname', ''),
                'ip': user.get('ip_location', ''),
                'city': user.get('city', ''),
                'district': user.get('district', ''),
            }
        )

        comment_tab = self.browser.new_tab()
        comment_tab.listen.start(['comment/list/?device_platform', 'comment/list/reply/?device_platform'])
        comment_tab.get(base_url)

        count_ele = comment_tab.ele(COMMENT_COUNT_XPATH)
        count_text = count_ele.text if count_ele else ''
        result['comment_summary']['display_count'] = count_text
        result['comment_summary']['total_count'] = self._parse_count(count_text)

        scroll_ele = comment_tab.ele(COMMENT_SCROLL_XPATH)
        start_index = 0

        while self._count_comments(result) < max_comments:
            response = comment_tab.listen.wait(timeout=0.3)
            if response:
                payload = self._response_to_dict(response.response)
                comments = payload.get('comments', [])
                if not comments:
                    break
                self._merge_comments(result, comments, max_comments)

            comment_items = comment_tab.eles(COMMENT_LIST_XPATH)
            end_index = len(comment_items)

            for index in range(start_index, end_index):
                if self._count_comments(result) >= max_comments:
                    break
                items = comment_tab.eles(COMMENT_LIST_XPATH)
                if index >= len(items):
                    break

                while True:
                    try:
                        button = items[index].ele('tag:button', timeout=0.1)
                    except Exception:
                        break

                    if not button or button.attr('class') not in COMMENT_EXPAND_CLASSES:
                        break

                    button.click()
                    time.sleep(0.2)
                    comment_tab.actions.scroll(delta_y=100, on_ele=scroll_ele)
                    if comment_tab.wait.ele_displayed(COMMENT_REPLY_PANEL_XPATH, timeout=0.1):
                        break

                    reply_response = comment_tab.listen.wait(timeout=0.3)
                    if not reply_response:
                        continue
                    reply_payload = self._response_to_dict(reply_response.response)
                    self._merge_comments(result, reply_payload.get('comments', []), max_comments)
                    if self._count_comments(result) >= max_comments:
                        break

            start_index = end_index
            if self._count_comments(result) >= max_comments:
                break

            end_ele = comment_tab.ele(COMMENT_END_XPATH.format(index=start_index))
            if end_ele and end_ele.text == NO_MORE_COMMENT_TEXT:
                break

            comment_tab.actions.scroll(delta_y=500, on_ele=scroll_ele)

        self._safe_close_tab(comment_tab)
        result['comment_summary']['collected_count'] = self._count_comments(result)
        self._save_json(f'{video_id}_comments', result)
        text_path = self.output_dir / f'{video_id}_comments.txt'
        text_path.write_text(self._build_text_report(video_id, result), encoding='utf-8')
        return result

    def crawl_many(self, video_ids: Iterable[str], max_comments: int = 50) -> List[Dict[str, Any]]:
        summary: List[Dict[str, Any]] = []
        for video_id in video_ids:
            result = self.crawl_video_comments(video_id, max_comments=max_comments)
            comment_summary = result.get('comment_summary', {})
            summary.append(
                {
                    'video_id': video_id,
                    'display_count': comment_summary.get('display_count', ''),
                    'total_count': comment_summary.get('total_count'),
                    'collected_count': comment_summary.get('collected_count', 0),
                    'collection_limit': comment_summary.get('collection_limit', max_comments),
                    'json_file': str(self.output_dir / f'{video_id}_comments.json'),
                    'text_file': str(self.output_dir / f'{video_id}_comments.txt'),
                }
            )
        self._save_json('summary', summary)
        return summary

    def close(self) -> None:
        for method_name in ('quit', 'close'):
            method = getattr(self.browser, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass
                break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='抖音评论抓取工具')
    parser.add_argument('--video-ids', nargs='+', required=True, help='一个或多个抖音视频 ID')
    parser.add_argument('--max-comments', type=int, default=50, help='每个视频最多抓取的评论数量')
    parser.add_argument('--output-dir', default='output', help='输出目录')
    parser.add_argument('--wait-for-login', action='store_true', help='open Douyin first and wait for manual login')
    return parser


def main() -> None:
    args = build_parser().parse_args()
    crawler = DouyinCommentCrawler(output_dir=args.output_dir, wait_for_login=args.wait_for_login)
    try:
        summary = crawler.crawl_many(args.video_ids, max_comments=args.max_comments)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"summary_path={Path(args.output_dir) / 'summary.json'}")
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
