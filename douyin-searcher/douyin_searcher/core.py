# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
from typing import Any, Dict, List, Optional

from DrissionPage import Chromium


class DouyinSearcher:
    PLATFORM_DEFAULT_FILTERS = {
        'sort': 'comprehensive',
        'publish_time': 'any',
        'duration': 'any',
        'scope': 'any',
        'content_type': 'any',
    }

    FILTER_OPTIONS = {
        'sort': {
            'comprehensive': ('0', '0'),
            'latest': ('0', '1'),
            'most_liked': ('0', '2'),
        },
        'publish_time': {
            'any': ('1', '0'),
            'day': ('1', '1'),
            'week': ('1', '2'),
            'half_year': ('1', '3'),
        },
        'duration': {
            'any': ('2', '0'),
            'under_1_minute': ('2', '1'),
            '1_to_5_minutes': ('2', '2'),
            'over_5_minutes': ('2', '3'),
        },
        'scope': {
            'any': ('3', '0'),
            'following': ('3', '1'),
            'recently_watched': ('3', '2'),
            'unwatched': ('3', '3'),
        },
        'content_type': {
            'any': ('4', '0'),
            'video': ('4', '1'),
            'image_text': ('4', '2'),
        },
    }

    def __init__(
        self,
        max_count: int = 10,
        browser: Optional[Chromium] = None,
        wait_for_login: bool = False,
        sort: str = 'latest',
        publish_time: str = 'any',
        duration: str = 'any',
        scope: str = 'unwatched',
        content_type: str = 'video',
    ):
        self._configure_console()
        self.max_count = max_count
        self.base_url = 'https://www.douyin.com/'
        self.browser = browser
        self.wait_for_login = wait_for_login
        self._login_checked = False
        self.filter_config = self._normalize_filter_config(
            sort=sort,
            publish_time=publish_time,
            duration=duration,
            scope=scope,
            content_type=content_type,
        )

    @staticmethod
    def _configure_console() -> None:
        if sys.platform != 'win32':
            return
        for stream_name in ('stdout', 'stderr'):
            stream = getattr(sys, stream_name, None)
            if stream is not None and hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')

    @staticmethod
    def _parse_first_page(raw_text: str) -> List[Dict[str, Any]]:
        videos: List[Dict[str, Any]] = []
        for block in re.findall(r'"aweme_info":\s*{.*?"cover":', raw_text or '', re.DOTALL):
            aweme_id_match = re.search(r'"aweme_id":\s*"(\d+)"', block)
            create_time_match = re.search(r'"create_time":\s*(\d+)', block)
            if not aweme_id_match:
                continue
            videos.append(
                {
                    'aweme_id': aweme_id_match.group(1),
                    'create_time': create_time_match.group(1) if create_time_match else None,
                    'platform': 'douyin',
                }
            )
        return videos

    @staticmethod
    def _parse_more_pages(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        videos: List[Dict[str, Any]] = []
        for item in data or []:
            aweme_info = item.get('aweme_info', {})
            aweme_id = aweme_info.get('aweme_id')
            if not aweme_id:
                continue
            videos.append(
                {
                    'aweme_id': aweme_id,
                    'create_time': aweme_info.get('create_time'),
                    'platform': 'douyin',
                }
            )
        return videos

    @classmethod
    def _normalize_filter_value(cls, group: str, value: str) -> str:
        normalized = (value or '').strip().lower().replace('-', '_')
        if normalized not in cls.FILTER_OPTIONS[group]:
            available = ', '.join(cls.FILTER_OPTIONS[group].keys())
            raise ValueError(f'invalid {group}: {value!r}. available: {available}')
        return normalized

    @classmethod
    def _normalize_filter_config(cls, **kwargs: str) -> Dict[str, str]:
        return {group: cls._normalize_filter_value(group, value) for group, value in kwargs.items()}

    @staticmethod
    def _filter_option_xpath(index1: str, index2: str) -> str:
        return f'x://span[@data-index1="{index1}" and @data-index2="{index2}"]'

    def _open_filter_panel(self, tab: Any) -> None:
        filter_button_xpath = 'x://span[contains(normalize-space(), "筛选")]'
        attempts = 0

        while not tab.wait.ele_displayed(self._filter_option_xpath('0', '0'), timeout=0.3):
            if tab.wait.ele_displayed(filter_button_xpath, timeout=0.3):
                tab.actions.move_to(filter_button_xpath)
            else:
                tab.actions.move_to('x://body')
            attempts += 1
            if attempts > 50:
                raise RuntimeError('filter panel did not appear')

    def _apply_single_filter(self, tab: Any, group: str, value: str) -> Optional[Any]:
        index1, index2 = self.FILTER_OPTIONS[group][value]
        option = tab.ele(self._filter_option_xpath(index1, index2))
        classes = (option.attr('class') or '').split()
        if 'u39cEW99' in classes:
            return None
        tab.listen.start('general/search/stream/')
        option.click()
        response = tab.listen.wait(timeout=5)
        if not response:
            raise RuntimeError(f'failed to apply filter {group}={value}')
        tab.wait(0.3)
        return response

    def _apply_filters(self, tab: Any) -> Optional[Any]:
        self._open_filter_panel(tab)
        last_response = None
        for group in ('sort', 'publish_time', 'duration', 'scope', 'content_type'):
            response = self._apply_single_filter(tab, group, self.filter_config[group])
            if response is not None:
                last_response = response
        return last_response

    def _open_browser(self) -> Chromium:
        if self.browser is None:
            self.browser = Chromium()
        return self.browser

    def ensure_login(self, browser: Chromium) -> None:
        if not self.wait_for_login or self._login_checked:
            return
        login_tab = browser.new_tab()
        login_tab.get(self.base_url)
        input('Please complete Douyin login in the browser, then press Enter to continue: ')
        try:
            login_tab.close()
        except Exception:
            pass
        self._login_checked = True

    def close(self) -> None:
        if self.browser:
            try:
                self.browser.quit()
            except Exception:
                pass
            self.browser = None

    def search(self, keyword: str) -> Dict[str, Any]:
        if not keyword or not keyword.strip():
            raise ValueError('keyword must not be empty')

        result: Dict[str, Any] = {
            'keyword': keyword,
            'total': 0,
            'videos': [],
            'filters': dict(self.filter_config),
        }
        browser = self._open_browser()
        self.ensure_login(browser)
        tab = browser.new_tab()

        try:
            tab.get(self.base_url)
            search_input = tab.ele('x://input[contains(@class, "YEhxqQNi jUqDCyab")]').wait(3)
            search_input.input(f'{keyword}\n')
            tab.wait(1)

            filtered_response = self._apply_filters(tab)
            if filtered_response is not None:
                all_videos = self._parse_first_page(filtered_response.response.raw_body)
            elif self.filter_config == self.PLATFORM_DEFAULT_FILTERS:
                tab.listen.start('general/search/stream/')
                search_input = tab.ele('x://input[contains(@class, "YEhxqQNi jUqDCyab")]').wait(3)
                search_input.input(f'{keyword}\n')
                initial_response = tab.listen.wait(timeout=5)
                if not initial_response:
                    raise RuntimeError('failed to get initial search result page')
                all_videos = self._parse_first_page(initial_response.response.raw_body)
            else:
                raise RuntimeError('failed to get filtered search result page')

            seen_ids = {item['aweme_id'] for item in all_videos}

            if len(all_videos) < self.max_count:
                tab.listen.start('general/search/single/')
                while len(all_videos) < self.max_count:
                    scroll_ele = tab.ele(
                        'x://div[contains(@class, "child-route-container route-scroll-container IhmVuo1S")]'
                    )
                    tab.actions.scroll(500, on_ele=scroll_ele)
                    next_response = tab.listen.wait(timeout=1)
                    if next_response:
                        for item in self._parse_more_pages(next_response.response.body.get('data', [])):
                            if item['aweme_id'] in seen_ids:
                                continue
                            seen_ids.add(item['aweme_id'])
                            all_videos.append(item)
                            if len(all_videos) >= self.max_count:
                                break
                    if tab.wait.ele_displayed('x://div[contains(@class, "Q3VKLvv7")]', timeout=0.2):
                        break

            result['videos'] = all_videos[:self.max_count]
            result['total'] = len(result['videos'])
            return result
        finally:
            try:
                tab.close()
            except Exception:
                pass
            self.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Douyin video search tool')
    parser.add_argument('--keyword', required=True, help='search keyword')
    parser.add_argument('--max-count', '--max-results', '--max', dest='max_count', type=int, default=10)
    parser.add_argument(
        '--sort',
        choices=['comprehensive', 'latest', 'most_liked'],
        default='latest',
        help='search sort order',
    )
    parser.add_argument(
        '--publish-time',
        choices=['any', 'day', 'week', 'half_year'],
        default='any',
        help='publish time filter',
    )
    parser.add_argument(
        '--duration',
        choices=['any', 'under_1_minute', '1_to_5_minutes', 'over_5_minutes'],
        default='any',
        help='video duration filter',
    )
    parser.add_argument(
        '--scope',
        choices=['any', 'following', 'recently_watched', 'unwatched'],
        default='unwatched',
        help='search scope filter',
    )
    parser.add_argument(
        '--content-type',
        choices=['any', 'video', 'image_text'],
        default='video',
        help='content type filter',
    )
    parser.add_argument('--json', action='store_true', help='print JSON result')
    parser.add_argument('--wait-for-login', action='store_true', help='open Douyin first and wait for manual login')
    return parser


def main() -> None:
    args = build_parser().parse_args()
    searcher = DouyinSearcher(
        max_count=args.max_count,
        wait_for_login=args.wait_for_login,
        sort=args.sort,
        publish_time=args.publish_time,
        duration=args.duration,
        scope=args.scope,
        content_type=args.content_type,
    )
    result = searcher.search(args.keyword)

    print(f"total={result['total']}")
    for index, video in enumerate(result['videos'], start=1):
        print(f"{index}. {video['aweme_id']}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result['total'] else 1)


if __name__ == '__main__':
    main()
