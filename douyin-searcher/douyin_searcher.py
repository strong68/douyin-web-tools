# -*- coding: utf-8 -*-

import argparse
import json
import re
from typing import Any, Dict, List, Optional

from DrissionPage import Chromium


FILTER_OPTIONS: Dict[str, Dict[str, tuple]] = {
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

PLATFORM_DEFAULT_FILTERS: Dict[str, str] = {
    'sort': 'comprehensive',
    'publish_time': 'any',
    'duration': 'any',
    'scope': 'any',
    'content_type': 'any',
}


class DouyinSearcher:
    """Search Douyin videos by keyword with filter support."""

    HOME_URL = 'https://www.douyin.com/'

    def __init__(
        self,
        max_count: int = 10,
        browser: Optional[Chromium] = None,
        sort: str = 'latest',
        publish_time: str = 'any',
        duration: str = 'any',
        scope: str = 'unwatched',
        content_type: str = 'video',
    ):
        self._owns_browser = browser is None
        self.browser = browser or Chromium()
        self.max_count = max_count
        self.filter_config = self._normalize_filter_config(
            sort=sort,
            publish_time=publish_time,
            duration=duration,
            scope=scope,
            content_type=content_type,
        )

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Douyin keyword searcher')
        parser.add_argument('--keyword', required=True, help='search keyword')
        parser.add_argument('--max-count', type=int, default=10, help='maximum number of results')
        parser.add_argument('--json', action='store_true', help='print results as JSON')
        parser.add_argument('--sort', default='latest',
                            choices=['comprehensive', 'latest', 'most_liked'], help='sort filter')
        parser.add_argument('--publish-time', default='any',
                            choices=['any', 'day', 'week', 'half_year'], help='publish time filter')
        parser.add_argument('--duration', default='any',
                            choices=['any', 'under_1_minute', '1_to_5_minutes', 'over_5_minutes'], help='duration filter')
        parser.add_argument('--scope', default='unwatched',
                            choices=['any', 'following', 'recently_watched', 'unwatched'], help='scope filter')
        parser.add_argument('--content-type', default='video',
                            choices=['any', 'video', 'image_text'], help='content type filter')
        return parser

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
        if normalized not in FILTER_OPTIONS[group]:
            available = ', '.join(FILTER_OPTIONS[group].keys())
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
        index1, index2 = FILTER_OPTIONS[group][value]
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
        return self.browser

    def close(self) -> None:
        if self._owns_browser and self.browser:
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
        tab = browser.new_tab()

        try:
            tab.get(self.HOME_URL)
            search_input = tab.ele('x://input[contains(@class, "YEhxqQNi jUqDCyab")]').wait(3)
            search_input.input(f'{keyword}\n')
            tab.wait(1)

            filtered_response = self._apply_filters(tab)

            if filtered_response is not None:
                all_videos = self._parse_first_page(filtered_response.response.raw_body)
            elif self.filter_config == PLATFORM_DEFAULT_FILTERS:
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

    @classmethod
    def main(cls) -> None:
        args = cls._parser().parse_args()
        searcher = cls(
            max_count=args.max_count,
            sort=args.sort,
            publish_time=args.publish_time,
            duration=args.duration,
            scope=args.scope,
            content_type=args.content_type,
        )
        try:
            result = searcher.search(keyword=args.keyword)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for item in result.get('videos', []):
                    print(item.get('aweme_id', ''))
        finally:
            searcher.close()


if __name__ == '__main__':
    DouyinSearcher.main()
