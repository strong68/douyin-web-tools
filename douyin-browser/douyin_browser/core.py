# -*- coding: utf-8 -*-

import argparse
import traceback
from typing import Callable, Optional

from DrissionPage import Chromium
from DrissionPage.common import Keys


class DouyinBrowser:
    def __init__(self, browser: Optional[Chromium] = None, wait_for_login: bool = False):
        self.browser = browser or Chromium()
        self.base_url = 'https://www.douyin.com/'
        self.recommend_tab = None
        self.wait_for_login = wait_for_login
        self._login_checked = False

    def ensure_login(self) -> None:
        if not self.wait_for_login or self._login_checked:
            return
        login_tab = self.browser.new_tab()
        login_tab.get(self.base_url)
        input('Please complete Douyin login in the browser, then press Enter to continue: ')
        try:
            login_tab.close()
        except Exception:
            pass
        self._login_checked = True

    def enter_recommend_page(self):
        self.ensure_login()
        self.recommend_tab = self.browser.new_tab()
        recommend_ele = (
            'x://*[@id="douyin-navigation"]/div/div[2]/div/div[1]/div[1]/div/div[2]/div/div/a/div[1]/div[1]'
        )
        attempts = 0

        while True:
            if attempts % 10 == 0:
                print('[browser] refreshing Douyin home page...')
                self.recommend_tab.get(self.base_url)
            if self.recommend_tab.wait.ele_displayed(recommend_ele, timeout=0.5):
                self.recommend_tab.wait(0.5)
                break
            attempts += 1

        self.recommend_tab.ele(recommend_ele).click().wait(0.5)
        self.recommend_tab.listen.start('get_v2/?device_platform=webapp')
        print('[browser] entered recommend page')
        return self.recommend_tab

    def get_current_video_id(self) -> Optional[str]:
        result = self.recommend_tab.listen.wait(timeout=3)
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
        self.recommend_tab.actions.key_down(Keys.DOWN)
        self.recommend_tab.actions.key_up(Keys.DOWN)
        self.recommend_tab.wait(0.8)

    def is_on_recommend_page(self) -> bool:
        return 'recommend=1' in (self.recommend_tab.url or '')

    def browse_one(self, callback: Optional[Callable[[str], bool]] = None) -> bool:
        if not self.is_on_recommend_page():
            print('[browser] recommend page is no longer active')
            return False

        video_id = self.get_current_video_id()
        if not video_id:
            print('[browser] video id not found, trying next video')
            self.next_video()
            return self.browse_one(callback=callback)

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
        count = 0
        try:
            self.enter_recommend_page()
            while True:
                if max_count is not None and count >= max_count:
                    print(f'[browser] reached max_count={max_count}')
                    break
                if not self.browse_one(callback=callback):
                    break
                count += 1
        finally:
            self.close()

    @staticmethod
    def build_download_callback(output_dir: Optional[str] = None) -> Callable[[str], bool]:
        try:
            from douyin_downloader import DouyinDownloader
        except ImportError:
            def missing_dependency(_: str) -> bool:
                print('[browser] douyin_downloader is not available')
                return False

            return missing_dependency

        downloader = DouyinDownloader(output_dir=output_dir)

        def callback(video_id: str) -> bool:
            result = downloader.download_video(video_id)
            print(f"[browser] download result: {result['message']}")
            return input('Press Enter to continue, or q to quit: ').strip().lower() != 'q'

        return callback

    def close(self) -> None:
        if self.recommend_tab:
            try:
                self.recommend_tab.close()
            except Exception:
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Douyin recommend page browser')
    parser.add_argument(
        '--mode',
        choices=['interactive', 'download'],
        default='interactive',
        help='interactive: only browse; download: browse and download',
    )
    parser.add_argument('--max-count', type=int, default=None, help='maximum number of videos to browse')
    parser.add_argument('--output-dir', default=None, help='download output directory for download mode')
    parser.add_argument('--wait-for-login', action='store_true', help='open Douyin first and wait for manual login')
    return parser


def main() -> None:
    args = build_parser().parse_args()
    browser = DouyinBrowser(wait_for_login=args.wait_for_login)
    callback = browser.build_download_callback(output_dir=args.output_dir) if args.mode == 'download' else None
    browser.browse_loop(callback=callback, max_count=args.max_count)


if __name__ == '__main__':
    main()
