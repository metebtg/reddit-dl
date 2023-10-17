# -*- coding: utf-8 -*-

"""reddit_dl.downloader: downloader module"""

import os
import re
import subprocess
from random import choice
from urllib.parse import urlparse, unquote, urljoin, urlunparse
from pathlib import PurePosixPath
from typing import Optional

import requests
import m3u8

from .utils import url_to_filename
from .constants import USERAGENTS, TIMEOUT


HEADERS = {
    'User-Agent': choice(USERAGENTS),
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept': '*/*',
}

def hls_extractor(url: str) -> list:
    """Download hls videos."""
    playlist = m3u8.load(url)
    parsed = urlparse(url)._replace(query='', params='', fragment='')

    # Create base url
    path = [_ for _ in parsed.path.split('/') if _][0]
    base_url = urlunparse(parsed._replace(path=path))
    if not base_url.endswith('/'):
        base_url += '/'

    url_list = [{"url": playlist.data['playlists'][0]['uri'], "type": "video"}]
    if playlist.data['media']:
        audio_url = urljoin(base_url, playlist.data['media'][0]['uri'])
        url_list.append({"url": audio_url, "type": "audio"})

    # Find best quality
    best_quality = 0
    uri = ''
    for playlist in playlist.data['playlists']:
        if best_quality < playlist['stream_info']['bandwidth']:
            best_quality = playlist['stream_info']['bandwidth']
            uri = playlist['uri']

            for url_ in url_list:
                if url_['type'] == 'video':
                    url_['url'] = urljoin(base_url, uri)

    hls_data = []

    # Extract segments.
    for _url in url_list:
        res = requests.get(_url["url"], timeout=TIMEOUT)
        m3u8_master = m3u8.loads(res.text)
        segment_urls = [urljoin(base_url, seg['uri'])  for seg in m3u8_master.data['segments']]

        if segment_urls:
            hls_data.append(
                {
                    "type": _url['type'],
                    "segment_urls": segment_urls
                }
            )

    return hls_data

def merge_hls(
        output: str,
        video: str,
        audio: Optional[str] = None,
        ):
    """Merge audio and video file.

    :param output: Output file full path. exp. /home/sky/funny_video.mp4
    :param video: Video file full path. exp. /home/sky/video.webm
    :param audio: Audio file full path. exp. /home/sky/audio.mp3"""

    if audio and video:
        cmd = f'ffmpeg -loglevel panic -i "{video}" -i "{audio}" -c:v copy -c:a aac "{output}"'
        subprocess.call(cmd, shell=True)
        if os.path.exists(output):
            os.remove(video)
            os.remove(audio)
    elif video:
        cmd = f'ffmpeg -loglevel panic -i "{video}" {output}'
        subprocess.call(cmd, shell=True)
        if os.path.exists(output):
            os.remove(video)

class Downloader:
    """Simple downloader"""
    def __init__(
            self, update_mode: bool = False, request_timeout: int = TIMEOUT,
            raise_exception: bool = True, headers: Optional[dict] = None,):
        self.update_mode = update_mode
        self.request_timeout = request_timeout
        self.raise_exception = raise_exception
        self.headers = headers if headers else HEADERS

    def download(
            self, url: str, path: Optional[str] = None,
            headers: Optional[dict] = None, output_format: str='mp4'):
        """Public method for Downloader Class. Detects given
        url type (hls or not) and downloads it."""

        if headers:
            self.headers = headers

        path = path if path else os.getcwd()

        # Check is hls
        if re.search(r'.m3u8(\?+|$)', url):
            return self._hls_downloader(url, path, output_format)
        return self._downloader(url, path)

    def _downloader(
            self, url, path: str):
        """Download video, image or gif."""

        file_name = url_to_filename(url)
        full_path = os.path.join(path, file_name)

        with requests.get(
            url, stream=True, headers=self.headers, timeout=self.request_timeout) as res:
            if not res.status_code == 404 and self.raise_exception:
                res.raise_for_status()

            # If last part of url has changed, than return
            res_url = PurePosixPath(unquote(urlparse(res.url).path)).parts[-1]
            req_url = PurePosixPath(unquote(urlparse(url).path)).parts[-1]

            if res_url == req_url:
                with open(full_path, 'wb') as file:
                    for chunk in res.iter_content(chunk_size=8192):
                        file.write(chunk)

    def _hls_downloader(
            self, url: str, path: str, output_format: str='mp4'):
        """Downloads hls media."""

        file_name = url_to_filename(url)
        media_path = os.path.join(path, file_name)
        output_full_path = f"{media_path}.{output_format}"
        to_merged = {"output": output_full_path}
        hls_data = hls_extractor(url)

        for data in hls_data:
            to_merged.update({data['type']: f"{media_path}.{data['type']}"})

            if os.path.exists(f"{media_path}.{data['type']}"):
                break

            with open(f"{media_path}.{data['type']}", "wb") as file:
                for url_ in data['segment_urls']:
                    res =  requests.get(url_, timeout=self.request_timeout, headers=self.headers)

                    if res.ok:
                        file.write(res.content)
                    elif self.raise_exception:
                        res.raise_for_status()

        # Finally merge or convert to .mp4
        merge_hls(**to_merged)
