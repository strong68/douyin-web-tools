# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from DrissionPage import Chromium


class DouyinDownloader:
    """Download Douyin videos by video id."""

    HOME_URL = 'https://www.douyin.com/'
    DETAIL_API_PATTERN = 'aweme/detail/?device_platform'
    DEFAULT_OUTPUT_DIR = str(Path(__file__).resolve().parent)
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_MAX_DURATION_SECONDS = 300

    def __init__(
        self,
        output_dir: Optional[str] = None,
        browser: Optional[Chromium] = None,
        max_duration_seconds: Optional[int] = DEFAULT_MAX_DURATION_SECONDS,
    ):
        self.output_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        self._owns_browser = browser is None
        self.browser = browser
        self.max_duration_seconds = max_duration_seconds

        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ),
                'referer': self.HOME_URL,
            }
        )

        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Douyin video download tool')
        parser.add_argument('--video-id', help='single video id')
        parser.add_argument('--video-ids', help='comma-separated video ids')
        parser.add_argument('--output-dir', default=None, help='output directory')
        parser.add_argument(
            '--max-duration-seconds',
            type=int,
            default=300,
            help='skip videos longer than this, default is 300 seconds',
        )
        parser.add_argument('--json', action='store_true', help='print JSON result')
        return parser

    @staticmethod
    def extract_video_id(video_id: str) -> str:
        return (video_id or '').strip()

    def _open_browser(self) -> Chromium:
        if self.browser is None:
            self.browser = Chromium()
        return self.browser

    def _get_video_detail(self, browser: Chromium, video_id: str) -> Dict[str, Any]:
        tab = browser.new_tab()
        try:
            tab.get(self.HOME_URL)
            tab.listen.start(self.DETAIL_API_PATTERN)
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

    @staticmethod
    def _extract_duration_seconds(aweme_detail: Dict[str, Any]) -> Optional[float]:
        video_info = aweme_detail.get('video', {}) if isinstance(aweme_detail, dict) else {}
        raw_duration = video_info.get('duration')
        if raw_duration in (None, ''):
            raw_duration = aweme_detail.get('duration') if isinstance(aweme_detail, dict) else None

        try:
            duration_value = float(raw_duration)
        except (TypeError, ValueError):
            return None

        if duration_value > 1000:
            duration_value = duration_value / 1000.0
        return round(duration_value, 2)

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
                return {
                    'success': True,
                    'file_path': file_path,
                    'message': 'download succeeded',
                }
            except Exception:
                continue

        return {'success': False, 'file_path': None, 'message': 'all download urls failed'}

    def download_video(self, video_id: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            'success': False,
            'video_id': self.extract_video_id(video_id),
            'file_path': None,
            'message': '',
        }
        video_id = result['video_id']

        if not video_id or not video_id.isdigit():
            result['message'] = 'invalid video id'
            return result

        existing_file_path = None
        for extension in ('.mp4', '.mp3'):
            file_path = os.path.join(self.output_dir, f'{video_id}{extension}')
            if os.path.exists(file_path):
                existing_file_path = file_path
                break

        if existing_file_path:
            result.update(
                {
                    'success': True,
                    'file_path': existing_file_path,
                    'message': 'file already exists',
                }
            )
            return result

        browser = self._open_browser()
        detail = self._get_video_detail(browser, video_id)
        aweme_detail = detail.get('aweme_detail', {})
        if not aweme_detail:
            result['message'] = 'failed to get video detail'
            return result

        duration_seconds = self._extract_duration_seconds(aweme_detail)
        result['duration_seconds'] = duration_seconds

        if (
            self.max_duration_seconds is not None
            and duration_seconds is not None
            and duration_seconds > float(self.max_duration_seconds)
        ):
            result['skipped'] = True
            result['message'] = f'skipped video longer than {self.max_duration_seconds} seconds'
            return result

        urls = aweme_detail.get('video', {}).get('play_addr', {}).get('url_list', [])
        if not urls:
            result['message'] = 'download url not found'
            return result

        result.update(self._download_binary(urls, os.path.join(self.output_dir, video_id)))
        return result

    def download_many(self, video_ids: Iterable[str]) -> Dict[str, Any]:
        normalized_ids = [self.extract_video_id(item) for item in video_ids if item and str(item).strip()]
        results: Dict[str, Any] = {'total': len(normalized_ids), 'success': 0, 'failed': 0, 'videos': []}

        for video_id in normalized_ids:
            attempt = 0
            result = self.download_video(video_id)
            while not result['success'] and attempt < self.DEFAULT_RETRY_COUNT - 1:
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
        if self.browser and self._owns_browser:
            try:
                self.browser.quit()
            except Exception:
                pass
        self.browser = None
        self.session.close()

    @classmethod
    def main(cls) -> None:
        args = cls._parser().parse_args()
        downloader = cls(
            output_dir=args.output_dir,
            max_duration_seconds=args.max_duration_seconds,
        )

        try:
            if args.video_id:
                result = downloader.download_video(args.video_id)
            else:
                video_ids: List[str] = []
                if args.video_ids:
                    video_ids = [item.strip() for item in args.video_ids.split(',') if item.strip()]
                else:
                    cls._parser().error('provide --video-id or --video-ids')

                result = downloader.download_many(video_ids)

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
    DouyinDownloader.main()
