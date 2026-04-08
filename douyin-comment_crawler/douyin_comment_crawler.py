# -*- coding: utf-8 -*-

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from DrissionPage import Chromium


class DouyinCommentCrawler:
    """Crawl Douyin video comments and save a JSON report."""

    COMMENT_COUNT_THRESHOLD = 100
    COMMENT_LIST_XPATH = 'x://*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[5]/div/div/div[3]/div'
    COMMENT_SCROLL_XPATH = 'x://div[contains(@class, "parent-route-container route-scroll-container IhmVuo1S")]'
    COMMENT_END_XPATH = (
        'x://*[@id="douyin-right-container"]/div[2]/div/div/div[1]/div[5]/div/div/div[3]/div[{index}]'
    )
    COMMENT_EXPAND_CLASSES = {'FgYRerj2', 'J_mtqkIZ comment-reply-expand-btn'}
    COMMENT_REPLY_PANEL_XPATH = 'x://div[contains(@class, "eBcBNgnP NfyOpHiT")]'
    NO_MORE_COMMENT_TEXT = '暂时没有更多评论'
    DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent)

    EMOJI_PATTERN = re.compile(
        '['
        '\U0001F300-\U0001F5FF'
        '\U0001F600-\U0001F64F'
        '\U0001F680-\U0001F6FF'
        '\U0001F700-\U0001F77F'
        '\U0001F780-\U0001F7FF'
        '\U0001F800-\U0001F8FF'
        '\U0001F900-\U0001F9FF'
        '\U0001FA70-\U0001FAFF'
        '\u2600-\u26FF'
        '\u2700-\u27BF'
        ']+',
        flags=re.UNICODE,
    )
    MEANINGFUL_TEXT_PATTERN = re.compile(r'[\u4e00-\u9fffA-Za-z0-9]')

    def __init__(self, output_dir: Optional[str] = None, browser: Optional[Chromium] = None):
        self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._owns_browser = browser is None
        self.browser = browser or Chromium()

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Douyin comment crawler')
        parser.add_argument('--video-id', required=True, help='Douyin video id')
        parser.add_argument('--max-comments', type=int, default=100, help='maximum number of comments to collect')
        parser.add_argument(
            '--output-dir',
            default=DouyinCommentCrawler.DEFAULT_OUTPUT_DIR,
            help='directory to store crawler outputs, default is the subproject root',
        )
        return parser

    @staticmethod
    def _safe_close_tab(tab: Any) -> None:
        if tab is None:
            return
        try:
            tab.close()
        except Exception:
            pass

    @classmethod
    def _should_skip_comment_crawl(cls, total_count: Optional[int], threshold: int = COMMENT_COUNT_THRESHOLD) -> bool:
        return total_count is not None and total_count > threshold

    @staticmethod
    def _response_body_to_dict(response: Any) -> Dict[str, Any]:
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

    @classmethod
    def _is_expand_button(cls, button: Any) -> bool:
        if not button:
            return False
        return button.attr('class') in cls.COMMENT_EXPAND_CLASSES

    @classmethod
    def _clean_comment_text(cls, text: str) -> str:
        cleaned = cls.EMOJI_PATTERN.sub('', str(text or ''))
        cleaned = re.sub(r'\[[^\]]+\]', '', cleaned)
        cleaned = cleaned.replace('[', '').replace(']', '')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if cls.MEANINGFUL_TEXT_PATTERN.search(cleaned) else ''

    @staticmethod
    def _save_json(path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=4), encoding='utf-8')

    @staticmethod
    def _count_comments(comments_dict: Dict[str, Any]) -> int:
        comment_ids = set()
        for comment in comments_dict.get('comments', {}).values():
            comment_id = comment.get('comment_id')
            if comment_id and (comment.get('text') or comment.get('comment_time')):
                comment_ids.add(comment_id)
            for reply in comment.get('reply_comments', []):
                reply_id = reply.get('comment_id')
                if reply_id:
                    comment_ids.add(reply_id)
        return len(comment_ids)

    def _organize_comments(
        self,
        comments_dict: Dict[str, Any],
        new_comments_list: List[Dict[str, Any]],
        max_comments: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            for comment in new_comments_list:
                if max_comments is not None and self._count_comments(comments_dict) >= max_comments:
                    break

                comment_text = self._clean_comment_text(comment.get('text', ''))
                if not comment_text:
                    continue

                comment_time = comment.get('create_time', 0)
                dt_local = datetime.fromtimestamp(comment_time) if comment_time else datetime.fromtimestamp(0)
                comment_id = comment.get('cid', '')
                single_comment_dict = {
                    'comment_id': comment_id,
                    'text': comment_text,
                    'comment_time': dt_local.strftime('%Y-%m-%d %H:%M:%S'),
                    'comment_ip': comment.get('ip_label', ''),
                    'like_count': comment.get('digg_count', 0),
                    'reply_comments': [],
                }

                reply_id = comment.get('reply_id', '')
                if reply_id == '0':
                    comments_dict['comments'][comment_id] = single_comment_dict
                else:
                    if max_comments is not None and self._count_comments(comments_dict) >= max_comments:
                        break
                    parent_comment = comments_dict['comments'].setdefault(
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
                    existing_ids = {item.get('comment_id') for item in parent_comment['reply_comments']}
                    if single_comment_dict['comment_id'] not in existing_ids:
                        parent_comment['reply_comments'].append(single_comment_dict)

                reply_comments = comment.get('reply_comment', [])
                if reply_comments:
                    comments_dict = self._organize_comments(comments_dict, reply_comments, max_comments=max_comments)
                    if max_comments is not None and self._count_comments(comments_dict) >= max_comments:
                        break
        except Exception as exc:
            print(f'整理评论时出错: {exc}')
        return comments_dict

    def _persist_result(self, video_id: str, comments_data: Dict[str, Any]) -> str:
        json_path = self.output_dir / f'{video_id}_comments.json'
        self._save_json(json_path, comments_data)
        return str(json_path)

    def crawl_video_comments(
        self,
        video_id: str,
        max_comments: int = 100,
        comment_threshold: Optional[int] = None,
    ) -> Dict[str, Any]:
        base_url = f'https://www.douyin.com/video/{video_id}'

        tab = self.browser.new_tab()
        tab.listen.start('aweme/detail/?device_platform')
        tab.get(base_url)
        res = tab.listen.wait(timeout=15)
        video_data = self._response_body_to_dict(res.response) if res else {}
        aweme_detail = video_data.get('aweme_detail')
        self._safe_close_tab(tab)
        if not aweme_detail:
            raise ValueError(f'未获取到视频详情数据: {video_id}')

        dt_local = datetime.fromtimestamp(aweme_detail['create_time']).strftime('%Y-%m-%d %H:%M:%S')
        author_uid = aweme_detail.get('author_user_id', '')
        video_tags = aweme_detail.get('video_tag', [])
        caption = aweme_detail.get('desc', '')
        author_sec_uid = aweme_detail.get('author', {}).get('sec_uid', '')
        total_comment_count = aweme_detail.get('statistics', {}).get('comment_count')

        author_info: Dict[str, Any] = {}
        if author_sec_uid:
            tab = self.browser.new_tab()
            tab.listen.start('web/user/profile/other/?device_platform')
            tab.get(f'https://www.douyin.com/user/{author_sec_uid}')
            author_res = tab.listen.wait(timeout=15)
            author_data = self._response_body_to_dict(author_res.response) if author_res else {}
            author_info = author_data.get('user', {}) if isinstance(author_data, dict) else {}
            self._safe_close_tab(tab)

        comments_data: Dict[str, Any] = {
            'video_id': video_id,
            'create_time': dt_local,
            'platform': 'douyin',
            'video': {
                'caption': caption,
                'tags': video_tags,
                'video_link': f'https://www.douyin.com/video/{video_id}',
            },
            'author': {
                'uid': author_uid,
                'nickname': author_info.get('nickname', ''),
                'homepage_link': f'https://www.douyin.com/user/{author_sec_uid}' if author_sec_uid else '',
                'ip': author_info.get('ip_location', ''),
                'city': author_info.get('city', ''),
                'district': author_info.get('district', ''),
            },
            'comments': {},
        }

        tab = self.browser.new_tab()
        tab.listen.start(['comment/list/?device_platform', 'comment/list/reply/?device_platform'])
        tab.get(base_url)

        comments_data['comment_summary'] = {
            'total_count': total_comment_count,
            'collection_limit': max_comments,
            'collected_count': 0,
        }

        if total_comment_count == 0:
            self._safe_close_tab(tab)
            self._persist_result(video_id, comments_data)
            return comments_data

        if comment_threshold is not None and self._should_skip_comment_crawl(total_comment_count, threshold=comment_threshold):
            self._safe_close_tab(tab)
            comments_data['comment_summary']['collected_count'] = self._count_comments(comments_data)
            self._persist_result(video_id, comments_data)
            return comments_data

        div_start = 0
        scroll_ele = tab.ele(self.COMMENT_SCROLL_XPATH)

        while True:
            comment_resp = tab.listen.wait(timeout=0.5)
            if comment_resp:
                comment_text = self._response_body_to_dict(comment_resp.response)
                if comment_text.get('comments'):
                    comments_data = self._organize_comments(
                        comments_data,
                        comment_text.get('comments', []),
                        max_comments=max_comments,
                    )
                    comments_data['comment_summary']['collected_count'] = self._count_comments(comments_data)
                    if comments_data['comment_summary']['collected_count'] >= max_comments:
                        break

            comment_list = tab.eles(self.COMMENT_LIST_XPATH)
            div_end = len(comment_list)
            while True:
                expanded = False
                for index in range(div_start, div_end):
                    current_list = tab.eles(self.COMMENT_LIST_XPATH)
                    if index >= len(current_list):
                        break

                    comment_ele = current_list[index]
                    while True:
                        try:
                            button = comment_ele.ele('tag:button', timeout=0.1)
                        except Exception:
                            break

                        if not self._is_expand_button(button):
                            break

                        button.click()
                        time.sleep(0.2)
                        if scroll_ele:
                            tab.actions.scroll(delta_y=100, on_ele=scroll_ele)

                        if tab.wait.ele_displayed(self.COMMENT_REPLY_PANEL_XPATH, timeout=0.1):
                            break

                        comment_resp = tab.listen.wait(timeout=0.5)
                        if comment_resp:
                            comment_text = self._response_body_to_dict(comment_resp.response)
                            comments_data = self._organize_comments(
                                comments_data,
                                comment_text.get('comments', []),
                                max_comments=max_comments,
                            )
                            comments_data['comment_summary']['collected_count'] = self._count_comments(comments_data)
                            expanded = True
                            if comments_data['comment_summary']['collected_count'] >= max_comments:
                                break

                    if comments_data['comment_summary']['collected_count'] >= max_comments:
                        break

                if not expanded or comments_data['comment_summary']['collected_count'] >= max_comments:
                    break

            div_start = div_end
            if comments_data['comment_summary']['collected_count'] >= max_comments:
                break

            end_ele = tab.ele(self.COMMENT_END_XPATH.format(index=div_start))
            if end_ele and end_ele.text == self.NO_MORE_COMMENT_TEXT:
                break

            if scroll_ele:
                tab.actions.scroll(delta_y=500, on_ele=scroll_ele)
            time.sleep(0.2)

        self._safe_close_tab(tab)
        comments_data['comment_summary']['collected_count'] = self._count_comments(comments_data)
        self._persist_result(video_id, comments_data)
        return comments_data

    def close(self) -> None:
        if self.browser is None or not self._owns_browser:
            self.browser = None
            return

        for method_name in ('quit', 'close'):
            method = getattr(self.browser, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:
                    pass
                break
        self.browser = None

    @classmethod
    def main(cls) -> None:
        args = cls._parser().parse_args()
        crawler = cls(output_dir=args.output_dir)
        try:
            crawler.crawl_video_comments(video_id=args.video_id, max_comments=args.max_comments)
            json_path = crawler.output_dir / f'{args.video_id}_comments.json'
        finally:
            crawler.close()

        print(str(json_path))


if __name__ == '__main__':
    DouyinCommentCrawler.main()
