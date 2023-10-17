# -*- coding: utf-8 -*-

"""Helper Utils Module"""

import re
from urllib.parse import urlparse

from .constants import ALLOWED_URLS


def is_valid_url(url: str) -> bool:
    """Checks url is valid for Reddit, Teddit or Libreddit instances.
    If url is valid than returns url other wise False."""

    parsed_url = urlparse(url)

    if not re.search(r'/(r|reddit|u|user)+\/[a-zA-Z_0-9-]+?', parsed_url.path):
        return False

    for _ in ALLOWED_URLS:
        if urlparse(_).netloc in url:
            return True
            
    return False

def url_to_filename(url: str):
    """Create file name from url."""

    filename_regexed = re.search(r'[^/\\&\?]+\.\w{3,4}(?=([\?&].*$|$))', url)

    if not filename_regexed:
        return None

    filename = filename_regexed[0]

    if 'hlsplaylist' in filename.lower():
        paths = urlparse(url).path.split('/')
        paths = [_ for _ in paths if paths]

        if len(paths) > 1:
            filename = paths[-2]

    return filename
