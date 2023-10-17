# -*- coding: utf-8 -*-

"""redgifs.com Related Module"""

from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
from random import choice

import requests

from .constants import USERAGENTS, TIMEOUT


HEADERS = {
    'User-Agent': choice(USERAGENTS),
    'Accept': '*/*',
}

def get_redgifs_token(timeout: int = TIMEOUT) -> str:
    """Returns guest bearer token for redgifs api."""
    token_url = 'https://api.redgifs.com/v2/auth/temporary'
    res = requests.get(token_url, headers=HEADERS, timeout=timeout)
    res.raise_for_status()

    return res.json()['token']

def get_redgifs_video(url: str, bearer: str = None, timeout: int = TIMEOUT) -> str:
    """Returns downloadable video url from url. 
    If url can't be found than returns empty string."""

    bearer = get_redgifs_token() if not bearer else bearer
    bearered_header = {'Authorization': f'Bearer {bearer}'}
    vid_name = PurePosixPath(unquote(urlparse(url).path)).parts[-1].lower()

    vid_url = f'https://api.redgifs.com/v2/gifs/{vid_name}'
    res = requests.get(vid_url, headers=bearered_header, timeout=timeout)

    # When content is deleted gives error code `410`
    if res.status_code in [410, 404] :
        return ''

    # Raise for other bad codes
    res.raise_for_status()

    try:
        res_json = res.json()
        urls = res_json['gif']['urls']
    except KeyError:
        # It's deleted or via...
        return ''

    vd_url = urls['hd'] if urls.get('hd') else urls.get('sd')

    if not vd_url:
        return ''

    return vd_url
