# -*- coding: utf-8 -*-

"""bootstrap.bootstrap: provides entry point main()."""

import os
import re
import time
from functools import wraps
from typing import Callable, Optional
from urllib.parse import urlparse, unquote, urlunparse, parse_qsl, urlencode
from pathlib import PurePosixPath
from random import expovariate, choice

from requests import Response
import requests
from bs4 import BeautifulSoup

from .downloader import Downloader
from .utils import url_to_filename
from .exceptions import ConnectionException, ExistFileOnUpdateModeException
from .constants import USERAGENTS
from .redgifs import get_redgifs_token, get_redgifs_video


__version__ = "0.0.1"

HEADERS = {
    'Cookie': 'over18=1',
    'User-Agent': choice(USERAGENTS),
    'Accept': '*/*',
}

REDDIT_HEADERS = {'Cookie': 'over18=1'}
REDDIT_HEADERS.update(HEADERS)

def print_download_message(o_str: Optional[str] = None, post_data: Optional[dict] = None):
    if not o_str and post_data:
        o_str = f'Downloading post: {post_data["title"]}'
    if len(o_str) > 55:
        o_str = o_str[:52] + '...'
    elif len(o_str) < 55:
        o_str += ''.ljust(55 - len(o_str))

    print(o_str, end='\r', flush=True)

def is_download_url(url, type_):
    """Check is url have file extension."""
    rgx_img_cmp = re.compile(r'.(jpeg|jpg|png|tiff)(\?+|$)')
    rgx_gif_cmp = re.compile(r'.(gif)(\?+|$)')
    rgx_vd_cmp = re.compile(r'.(mp4|gifv|m3u8)(\?+|$)')

    if type_ == 'image':
        return re.search(rgx_img_cmp, url)

    if type_ == 'gif':
        return re.search(rgx_gif_cmp, url)

    if type_ == 'video':
        return re.search(rgx_vd_cmp, url)

    return None

def _retry_on_connection_error(func: Callable) -> Callable:
    """Decorator to retry the function max_connection_attemps number of times.

    Herewith-decorated functions need an ``_attempt`` keyword argument.

    This is to decorate functions that do network requests that may fail.
    Functions that only use these for network access must not be decorated with this  decorator."""
    @wraps(func)
    def call(redl, *args, **kwargs):
        try:
            return func(redl, *args, **kwargs)
        except (requests.exceptions.HTTPError, requests.exceptions.SSLError) as err:
            print(err)
            error_string = f"{func.__name__}({', '.join([repr(arg) for arg in args])}): {err}"
            if (kwargs.get('_attempt') or 1) == redl.max_connection_attempts:
                raise ConnectionException(error_string) from None
            try:
                if kwargs.get('_attempt'):
                    kwargs['_attempt'] += 1
                else:
                    kwargs['_attempt'] = 2
                redl._do_sleep()
                return call(redl, *args, **kwargs)
            except ConnectionException:
                raise ConnectionException(error_string) from None
    return call

def _update_exist_error_handler(func: Callable) -> Callable:
    """Decorator to retry the function max_connection_attemps number of times.

    Herewith-decorated functions need an ``_attempt`` keyword argument.

    This is to decorate functions that do network requests that may fail.
    Functions that only use these for network access must not be decorated with this  decorator."""
    @wraps(func)
    def call(redl, *args, **kwargs):
        try:
            return func(redl, *args, **kwargs)
        except (requests.exceptions.HTTPError, requests.exceptions.SSLError) as err:
            print(err)
            error_string = f"{func.__name__}({', '.join([repr(arg) for arg in args])}): {err}"
            if (kwargs.get('_attempt') or 1) == redl.max_connection_attempts:
                raise ConnectionException(error_string) from None
            try:
                if kwargs.get('_attempt'):
                    kwargs['_attempt'] += 1
                else:
                    kwargs['_attempt'] = 2
                redl._do_sleep()
                return call(redl, *args, **kwargs)
            except ConnectionException:
                raise ConnectionException(error_string) from None
    return call

class RedditDownloader:
    """RedditDownload Class.

       The associated :class:`RedditDownloader` with low-level communication functions.
    """

    def __init__(
            self,
            sleep: bool = True,
            user_agent: Optional[str] = None,
            download_pictures=True,
            download_videos: bool = True,
            download_gifs: bool = True,
            download_nsfw: bool = True,
            save_metadata: bool = False,
            max_connection_attempts: int = 3,
            request_timeout: float = 300.0,
            search_string: Optional[str] = None,
            update_mode: bool = False,
            raise_exception: bool = False):

        self.sleep = sleep
        self.user_agent = user_agent
        self.download_pictures = download_pictures
        self.download_videos = download_videos
        self.download_gifs = download_gifs
        self.download_nsfw = download_nsfw
        self.save_metadata = save_metadata
        self.max_connection_attempts = max_connection_attempts
        self.request_timeout = request_timeout
        self.search_string = search_string
        self.update_mode = update_mode
        self.raise_exception = raise_exception

        self.downloader = Downloader(
            self.update_mode, self.request_timeout, self.raise_exception)

    def _do_sleep(self):
        """Sleep when network error occurs."""
        if self.sleep:
            time.sleep(min(expovariate(0.6), 15.0))

    def download(self, target: str):
        """Public download method for RedditDL."""
        self._downloader(target)

    def _create_folder(self, url: str) -> str:
        """If not exist create folder, for given url.
        Exp. reddit.com/r/python creates folder with name
        r-python. Finally return folder path."""

        folder_name = '-'.join(PurePosixPath(
            unquote(urlparse(url).path)
        ).parts[1:3])

        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        return os.path.join(os.getcwd(), folder_name)

    @_retry_on_connection_error
    def _request_page(self, url, _attempt: int = 1) -> Response:
        """Error wrapper for simple page request."""

        res = requests.get(url, headers=REDDIT_HEADERS, timeout=self.request_timeout)
        if res.status_code == 403 and 'suspended' in res.text:
            print('Is suspended.')
            return res

        if self.raise_exception:
            res.raise_for_status()
        return res

    def _downloader(self, url: str, ):
        """Find new pages and call `self._download_page`."""

        if not re.search(r'/(r|reddit|u|user)+/[a-zA-Z_0-9-]+/comments', urlparse(url).path):
            path = self._create_folder(url)
        else:
            path = os.getcwd()

        has_next_page = True
        page_url = url

        while has_next_page:
            res = self._request_page(page_url)
            soup = BeautifulSoup(res.text, 'html.parser')

            # Download page
            self._download_page(soup, path)

            has_next_page = soup.find('span', class_='next-button')
            if  not has_next_page:
                break

            # Build `page_url`
            dummy_url = has_next_page.find('a').get('href')
            parsed =  urlparse(dummy_url)
            query_params = {'sort': 'new'}
            query_params.update(dict(parse_qsl(parsed.query)))

            page_url = urlunparse(
                urlparse(dummy_url)._replace(query=urlencode(query_params)))

    def _download_page(self, soup: BeautifulSoup, d_path: str):
        """Extract data and download from given page."""

        main_div = soup.find('div', id='siteTable')
        posts = main_div.find_all('div', class_='thing', recursive=False) if main_div else []

        # If not posts check if it's direct post link
        if not posts and main_div:
            post = main_div.find('div', class_='thing')
            posts = [post] if post else []

        for post in posts:
            # Extract post data
            post_data = self._get_post_data(post)

            if not post_data or not post_data['url']:
                continue

            # Extract down data
            down_data = self._get_download_info(post_data, d_path)
            if not down_data:
                continue

            # Filter urls
            down_urls = self._filter_urls(down_data['down_urls'], post_data['nsfw'])

            if not down_urls:
                continue

            for url in down_urls:
                filename = url_to_filename(url)
                file_full_path = os.path.join(d_path, filename)

                if not os.path.exists(file_full_path):
                    print_download_message(post_data=post_data)
                    self._download_post(url, d_path, down_data['headers'])

                elif self.update_mode:
                    raise ExistFileOnUpdateModeException(f'File exist {file_full_path}')

                else:
                    print_download_message(o_str=f'File exist {file_full_path}')

    def _filter_urls(self, urls, nsfw):
        """Filter given urls by user choices."""

        filtered = []
        if nsfw and not self.download_nsfw:
            return filtered

        for url in urls:
            if is_download_url(url, 'image') and self.download_pictures:
                filtered.append(url)

            elif is_download_url(url, 'gif') and self.download_gifs:
                filtered.append(url)

            elif is_download_url(url, 'video') and self.download_videos:
                filtered.append(url)

        return filtered

    @_retry_on_connection_error
    def _download_post(
            self, url: str, d_path: str, headers: dict, _attempt : int = 1):
        """Error wrapper for Downloader().download()"""
        self.downloader.download(url, d_path, headers=headers)

    def _get_post_data(self, post: BeautifulSoup) -> dict:
        """Returns post data."""

        # Set post title
        a_tag = post.find('a', class_='title')
        post_title = a_tag.getText() if a_tag else None

        # Set cached_html
        expando_uninit = post.find('div', class_='expando-uninitialized')
        cached_html = expando_uninit.get('data-cachedhtml') if expando_uninit else None

        # If not cached html it may be single post
        # Exp. `/r/MapPorn/comments/12hsred/which_countries_would_citizens_of_the_us_uk/`
        if not cached_html:
            expando = post.find('div', class_='expando')
            cached_html = str(expando)

        post_data = {
            'url': post.get('data-url'),
            'kind': post.get('data-kind'),
            'is_reddit_video': post.get('data-kind') == 'video',
            'author': post.get('data-author'),
            'subreddit': post.get('data-subreddit'),
            'permalink': post.get('data-permalink'),
            'rank': post.get('data-rank'),
            'comments_count': post.get('data-comments-count'),
            'score': post.get('data-score'),
            'nsfw': post.get('data-nsfw') == 'true',
            'timestamp': post.get('data-timestamp'),
            'type': post.get('data-type'),
            'is_gallery': post.get('data-is-gallery') == 'true',
            'cached_html': cached_html,
            'title': post_title
        }

        return post_data

    def _get_download_info(self, post_data: dict, d_path: str) -> dict:
        """Select downloadable links from `post_data`"""

        data = {'headers': {}, 'down_urls': []}
        data_url = post_data['url']
        cached_html = post_data.get('cached_html')
        new_soup = BeautifulSoup(cached_html, 'html.parser') if cached_html else None

        mega_regex_pattern = re.compile(r'.(jpeg|jpg|png|tiff|gif|mp4|gifv)(\?+|$)')

        # Is data url direct link for picture?
        if re.search(mega_regex_pattern, data_url):
            down_url = data_url

            # '.gifv' is just a .mp4 by igmur, this replacement is required for igmur
            if '.gifv' in down_url:
                # Check if content exist.
                with requests.get(down_url, headers=HEADERS, timeout=self.request_timeout) as res:
                    is_removed = 'https://i.imgur.com/removed.png' == res.url
                    down_url = down_url.replace('.gifv', '.mp4') if not is_removed else None

            data['down_urls'].append(down_url)

        elif 'redgifs.com' in data_url:
            r_url = data_url
            # If `r_url` endswith .jpg, .png remove it.
            re_list = re.findall(r'([A-Za-z./:]+)\.[a-zA-Z]+$', r_url)
            if re_list:
                r_url = re_list[0]

            # Special for redgifs, cause we doing request for getting down url
            # Check file is exist
            exist = False
            vd_name = r_url.split('/')[-1]
            for _ in os.listdir(d_path):
                if vd_name.lower() in _.lower():
                    exist = True

            if exist and self.update_mode:
                raise ExistFileOnUpdateModeException(f'{vd_name} is exist on update.')

            # Get video down url, prepare header for download
            if not exist:
                token = self._get_redgifs_token()
                down_url = self._get_redgifs_video(r_url, token)
                data['down_urls'].append(down_url)
                data['headers'] = {'Authorization': f'Bearer {token}'}

        elif new_soup:
            if post_data['is_gallery']:
                for a_tag in new_soup.find_all('a', class_=re.compile('gallery-item')):
                    # Could be image or gif
                    data['down_urls'].append(a_tag.get('href'))

            elif post_data['is_reddit_video']:
                video = new_soup.find('div', id=re.compile('video'))
                down_url = video.get('data-hls-url') if video else None

                data['down_urls'].append(down_url)

        # Filter for `None` and empty `str`
        data['down_urls'] = list(filter(None, data['down_urls']))

        if not data['down_urls']:
            return {}
        return data

    @_retry_on_connection_error
    def _get_redgifs_token(self, _attempt: int = 1):
        """Error wrapper for `get_redgifs_token()`"""
        return get_redgifs_token()

    @_retry_on_connection_error
    def _get_redgifs_video(self, url: str, token: Optional[str] = None, _attempt: int = 1):
        """Error wrapper for `_get_redgifs_video()`"""
        return get_redgifs_video(url, token)
