# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, Iterable, List, Optional

import requests
from DrissionPage import Chromium


class DouyinDownloader:
    def __init__(
        self,
        output_dir: Optional[str] = None,
        browser: Optional[Chromium] = None,
        wait_for_login: bool = False,
    ):
        self._configure_console()
        self.output_dir = output_dir or os.path.join(os.path.expanduser('~'), 'Desktop')
        self.browser = browser
        self.wait_for_login = wait_for_login
        self._login_checked = False
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ),
                'referer': 'https://www.douyin.com/',
            }
        )
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _configure_console() -> None:
        if sys.platform != 'win32':
            return
        for stream_name in ('stdout', 'stderr'):
            stream = getattr(sys, stream_name, None)
            if stream is not None and hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')

    @staticmethod
    def extract_video_id(url_or_id: str) -> str:
        if url_or_id.isdigit():
            return url_or_id
        for pattern in (r'douyin\.com/video/(\d+)', r'www\.douyin\.com/video/(\d+)', r'/video/(\d+)'):
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id.strip()

    def _open_browser(self) -> Chromium:
        if self.browser is None:
            self.browser = Chromium()
        return self.browser

    def ensure_login(self, browser: Chromium) -> None:
        if not self.wait_for_login or self._login_checked:
            return
        login_tab = browser.new_tab()
        login_tab.get('https://www.douyin.com/')
        input('Please complete Douyin login in the browser, then press Enter to continue: ')
        try:
            login_tab.close()
        except Exception:
            pass
        self._login_checked = True

    def _get_video_detail(self, browser: Chromium, video_id: str) -> Dict[str, Any]:
        tab = browser.new_tab()
        try:
            tab.get('https://www.douyin.com/')
            tab.listen.start('aweme/detail/?device_platform')
            tab.get(f'https://www.douyin.com/video/{video_id}')
            response = tab.listen.wait(timeout=15)
            if not response or not response.response:
                return {}
            body = response.response.body
            return body if isinstance(body, dict) else {}
        finally:
            try:
                tab.close()
            except Exception:
                pass

    def _download_binary(self, urls: Iterable[str], base_path: str) -> Dict[str, Any]:
        for url in urls:
            try:
                clean_url = url.split('?')[0]
                response = self.session.get(clean_url, timeout=30)
                response.raise_for_status()
                content = response.content
                extension = '.mp4' if len(content) > 8 and content[4:8] == b'ftyp' else '.mp3'
                file_path = f'{base_path}{extension}'
                with open(file_path, 'wb') as handle:
                    handle.write(content)
                return {'success': True, 'file_path': file_path, 'message': 'download succeeded'}
            except Exception:
                continue
        return {'success': False, 'file_path': None, 'message': 'all download urls failed'}

    def download_video(self, url_or_id: str) -> Dict[str, Any]:
        video_id = self.extract_video_id(url_or_id)
        result: Dict[str, Any] = {'success': False, 'video_id': video_id, 'file_path': None, 'message': ''}

        if not video_id or not video_id.isdigit():
            result['message'] = 'invalid video id'
            return result

        for extension in ('.mp4', '.mp3'):
            file_path = os.path.join(self.output_dir, f'{video_id}{extension}')
            if os.path.exists(file_path):
                return {
                    'success': True,
                    'video_id': video_id,
                    'file_path': file_path,
                    'message': 'file already exists',
                }

        browser = self._open_browser()
        self.ensure_login(browser)
        detail = self._get_video_detail(browser, video_id)
        aweme_detail = detail.get('aweme_detail', {})
        if not aweme_detail:
            result['message'] = 'failed to get video detail'
            return result

        urls = aweme_detail.get('video', {}).get('play_addr', {}).get('url_list', [])
        if not urls:
            result['message'] = 'download url not found'
            return result

        result.update(self._download_binary(urls, os.path.join(self.output_dir, video_id)))
        return result

    def download_many(self, video_ids: Iterable[str], retry_count: int = 2) -> Dict[str, Any]:
        normalized_ids = [self.extract_video_id(item.strip()) for item in video_ids if item and item.strip()]
        results: Dict[str, Any] = {'total': len(normalized_ids), 'success': 0, 'failed': 0, 'videos': []}

        for video_id in normalized_ids:
            attempt = 0
            result = self.download_video(video_id)
            while not result['success'] and attempt < retry_count - 1:
                attempt += 1
                time.sleep(1)
                result = self.download_video(video_id)

            results['videos'].append(result)
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1

        return results

    def close(self) -> None:
        if self.browser:
            try:
                self.browser.quit()
            except Exception:
                pass
            self.browser = None
        self.session.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Douyin video download tool')
    parser.add_argument('--video-id', help='single video id')
    parser.add_argument('--url', help='single video url')
    parser.add_argument('--video-ids', '--ids', dest='video_ids', help='comma-separated video ids')
    parser.add_argument('--video-id-file', '--file', dest='video_id_file', help='text file with one id per line')
    parser.add_argument('--output-dir', '--output', dest='output_dir', default=None, help='output directory')
    parser.add_argument('--retry-count', type=int, default=2, help='retry count for batch mode')
    parser.add_argument('--json', action='store_true', help='print JSON result')
    parser.add_argument('--wait-for-login', action='store_true', help='open Douyin first and wait for manual login')
    return parser


def main() -> None:
    args = build_parser().parse_args()
    downloader = DouyinDownloader(output_dir=args.output_dir, wait_for_login=args.wait_for_login)

    try:
        if args.video_id or args.url:
            result = downloader.download_video(args.video_id or args.url)
        else:
            video_ids: List[str] = []
            if args.video_ids:
                video_ids = [item.strip() for item in args.video_ids.split(',') if item.strip()]
            elif args.video_id_file:
                with open(args.video_id_file, 'r', encoding='utf-8') as handle:
                    video_ids = [line.strip() for line in handle if line.strip()]
            else:
                build_parser().error('provide --video-id / --url, or --video-ids / --video-id-file')

            result = downloader.download_many(video_ids, retry_count=args.retry_count)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif 'videos' in result:
            print(f"total={result['total']}")
            print(f"success={result['success']}")
            print(f"failed={result['failed']}")
        else:
            print(result['message'])
            if result.get('file_path'):
                print(result['file_path'])

        success = result['success'] if isinstance(result.get('success'), bool) else result.get('failed', 1) == 0
        sys.exit(0 if success else 1)
    finally:
        downloader.close()


if __name__ == '__main__':
    main()
