# -*- coding: utf-8 -*-

import argparse
import traceback
from typing import Callable, Optional

from DrissionPage import Chromium


class DouyinBrowser:
    """Browse the Douyin recommend page and yield video ids one by one."""

    HOME_URL = 'https://www.douyin.com/'
    RECOMMEND_ENTRY_XPATH = (
        'x://*[@id="douyin-navigation"]/div/div[2]/div/div[1]/div[1]/div/div[2]/div/div/a/div[1]/div[1]'
    )
    NEXT_VIDEO_XPATH = 'x://div[@data-e2e="video-switch-next-arrow"]'
    RECOMMEND_API_PATTERN = 'get_v2/?device_platform=webapp'

    def __init__(self, browser: Optional[Chromium] = None):
        self._owns_browser = browser is None
        self.browser = browser or Chromium()
        self.recommend_tab = None
        self._last_video_id: Optional[str] = None
        self._duplicate_hits = 0

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Douyin recommend page browser')
        parser.add_argument('--max-count', type=int, default=None, help='maximum number of videos to browse')
        return parser

    def enter_recommend_page(self) -> None:
        """Open Douyin and enter the recommend page."""
        self.recommend_tab = self.browser.new_tab()

        attempts = 0
        while True:
            if attempts % 10 == 0:
                print('[browser] refreshing Douyin home page...')
                self.recommend_tab.get(self.HOME_URL)

            if self.recommend_tab.wait.ele_displayed(self.RECOMMEND_ENTRY_XPATH, timeout=0.5):
                self.recommend_tab.wait(0.5)
                break
            attempts += 1

        self.recommend_tab.ele(self.RECOMMEND_ENTRY_XPATH).click()
        self.recommend_tab.listen.start(self.RECOMMEND_API_PATTERN)
        print('[browser] entered recommend page')

    def get_current_video_id(self) -> Optional[str]:
        """Read the current video id from the recommend API request."""
        result = self.recommend_tab.listen.wait(timeout=5)
        if not result or not hasattr(result, 'url'):
            return None

        url = result.url or ''
        marker = 'group_id='
        start = url.find(marker)
        if start < 0:
            return None

        start += len(marker)
        end = url.find('&', start)
        return url[start:] if end < 0 else url[start:end]

    def next_video(self) -> None:
        """Move to the next recommended video by clicking the next button."""
        next_ele = self.recommend_tab.ele(self.NEXT_VIDEO_XPATH, timeout=2)
        if not next_ele:
            raise RuntimeError('next video button not found on recommend page')

        next_ele.click()
        self.recommend_tab.wait(0.8)

    def _tab_is_alive(self) -> bool:
        if self.recommend_tab is None:
            return False
        try:
            _ = self.recommend_tab.url
            return True
        except Exception:
            return False

    def _is_on_recommend_page(self) -> bool:
        if not self._tab_is_alive():
            return False
        try:
            return 'recommend=1' in (self.recommend_tab.url or '')
        except Exception:
            return False

    def _recreate_browser(self) -> None:
        if not self._owns_browser:
            raise RuntimeError('browser instance is externally managed')
        try:
            self.browser.quit()
        except Exception:
            pass
        self.browser = Chromium()

    def reopen_recommend_page(self) -> None:
        """Recover from a stale page by reopening the recommend page."""
        self.close()
        self.recommend_tab = None
        try:
            self.enter_recommend_page()
        except Exception:
            self._recreate_browser()
            self.enter_recommend_page()

    def browse_one(self, callback: Optional[Callable[[str], bool]] = None) -> bool:
        """Handle one recommended video and optionally pass its id to a callback."""
        if not self._is_on_recommend_page():
            print('[browser] recommend page is no longer active')
            return False

        video_id = self.get_current_video_id()
        if not video_id:
            print('[browser] video id not found, trying next video')
            self.next_video()
            return self.browse_one(callback=callback)

        if video_id == self._last_video_id:
            self._duplicate_hits += 1
            print(f'[browser] duplicate video_id={video_id}, trying next video ({self._duplicate_hits})')
            if self._duplicate_hits >= 2:
                self.next_video()
            else:
                self.recommend_tab.wait(0.8)
            return self.browse_one(callback=callback)

        self._last_video_id = video_id
        self._duplicate_hits = 0
        print(f'[browser] video_id={video_id}')

        if callback:
            try:
                if callback(video_id) is False:
                    print('[browser] callback requested stop')
                    return False
            except Exception as exc:
                print(f'[browser] callback failed: {exc}')
                traceback.print_exc()
                return False
        else:
            while True:
                command = input('Press Enter to continue, or q to quit: ').strip().lower()
                if command == '':
                    break
                if command == 'q':
                    return False
                print('Invalid input. Press Enter or q.')

        self.next_video()
        return True

    def browse_loop(self, callback: Optional[Callable[[str], bool]] = None, max_count: Optional[int] = None) -> None:
        """Keep browsing recommended videos until stopped."""
        count = 0
        reconnect_attempts = 0

        try:
            self.enter_recommend_page()
            while True:
                if max_count is not None and count >= max_count:
                    print(f'[browser] reached max_count={max_count}')
                    break

                try:
                    if not self.browse_one(callback=callback):
                        break
                    count += 1
                    reconnect_attempts = 0
                except Exception as exc:
                    reconnect_attempts += 1
                    print(f'[browser] browse loop error: {exc}')
                    traceback.print_exc()
                    if reconnect_attempts > 3:
                        print('[browser] reconnect attempts exceeded, stopping browse loop')
                        break
                    print(f'[browser] reconnecting recommend page ({reconnect_attempts}/3)...')
                    self.reopen_recommend_page()
        finally:
            self.close()

    def close(self) -> None:
        if self.recommend_tab is not None:
            try:
                self.recommend_tab.close()
            except Exception:
                pass
            self.recommend_tab = None

        if self._owns_browser and self.browser is not None:
            try:
                self.browser.quit()
            except Exception:
                pass
            self.browser = None

    @classmethod
    def main(cls) -> None:
        args = cls._parser().parse_args()
        cls().browse_loop(max_count=args.max_count)


if __name__ == '__main__':
    DouyinBrowser.main()
