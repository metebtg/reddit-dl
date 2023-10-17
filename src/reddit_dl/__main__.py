# -*- coding: utf-8 -*-

"""Download pictures, gifs, videos along with their captions and other metadata from Reddit."""

import os
import sys
from typing import List
from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from urllib.parse import urlparse, urlunparse

from . import __version__
from .reddit_dl import RedditDownloader
from .utils import is_valid_url
from .exceptions import ExistFileOnUpdateModeException, ConnectionException


def build_url(list_, type_):
    """Build urls from args."""

    if not list_:
        return []
    data = []

    if type_ == 'user':
        for _ in list_:
            data.append(f'https://old.reddit.com/user/{_}/submitted/')

    elif type_ == 'reddit':
        for _ in list_:
            data.append(f'https://old.reddit.com/r/{_}/new/')

    elif type_ == 'target':
        users = [_.split('user-')[-1] for _ in list_ if _.startswith('user-')]
        reddits = [_.split('r-')[-1] for _ in list_ if _.startswith('r-')]
        urls = [_ for _ in list_ if (not _.startswith('r-') and not _.startswith('user-'))]

        if users:
            for _ in users:
                data.append(f'https://old.reddit.com/user/{_}/submitted/')
        if reddits:
            for _ in reddits:
                data.append(f'https://old.reddit.com/r/{_}/new/')
        if urls:
            for _ in urls:
                data.append(urlunparse(urlparse(_)._replace(netloc='old.reddit.com')))

    return data

def is_valid_target(target):
    """Determine is valid folder or url"""
    if (os.path.exists(os.path.join(os.getcwd(), target)) and
        (target.startswith('r-') or target.startswith('user-'))):
        return target

    if is_valid_url(target):
        return target
    raise ArgumentTypeError(f"target:{target} is not valid.")

def _main(redl: RedditDownloader, targetlist: List[str]) -> None:

    for target in targetlist:
        print(f'Downloading: {urlparse(target).path}')

        try:
            redl.download(target)
        except ExistFileOnUpdateModeException:
            print('\nUpdate completed.')
        except ConnectionException:
            if redl.raise_exception:
                raise

def main():
    """Entry point for cli."""

    try:
        parser = ArgumentParser(
            description=__doc__, add_help=False, fromfile_prefix_chars='+',
            epilog="https://github.com/reddit-dl/reddit-dl")

        g_misc = parser.add_argument_group('Miscellaneous Options')
        g_misc.add_argument('-h', '--help', action='help', help='Show this help message and exit.')
        g_misc.add_argument(
            '--version', action='version', 
            help='Show version number and exit.', version=__version__)

        g_targets = parser.add_argument_group(
            "What to Download",
            "Specify a list of targets. For each of these, reddit-dl creates a folder "
            "and downloads all media content. The following targets are supported:")
        g_targets.add_argument(
            'target',
            nargs='*',
            type=is_valid_target,
            help="Full url of users, subreddits or their local folder names."
                "Exp. `https://reddit.com/r/UkrainianConflict/`")

        g_targets.add_argument('-u', '--user', nargs='*', help="Usernames to download.")
        g_targets.add_argument('-r', '--reddit', nargs='*', help="Subreddit names to download.")

        g_post = parser.add_argument_group("What to Download of each Post")
        g_post.add_argument('--metadata-json', action='store_true', help=SUPPRESS)
        g_post.add_argument(
            '-V', '--no-videos', action='store_true', help='Do not download videos.')
        g_post.add_argument(
            '-P', '--no-pictures', action='store_true', help='Do not download pictures.')
        g_post.add_argument(
            '-G', '--no-gifs', action='store_true',help='Do not download pictures.')
        g_post.add_argument(
            '-N', '--no-nsfw', action='store_true', help='Do not download NSFW content.')

        g_cond = parser.add_argument_group("Which Posts to Download")
        g_cond.add_argument(
            '--update', action='store_true',
            help='For each target, stop when encountering the first already-downloaded content.')

        g_how = parser.add_argument_group('How to Download')
        g_how.add_argument('--user-agent', help='User Agent to use for HTTP requests.')
        g_how.add_argument(
            '--request-timeout', metavar='N', type=float, default=300.0,
            help='Seconds to wait before timing out a connection request. Defaults to 300.')
        g_how.add_argument(
            '--max-connection-attempts', metavar='N', type=int, default=3,
            help='Maximum number of connection attempts until a request is aborted.')
        g_how.add_argument('-S', '--no-sleep', action='store_true', help=SUPPRESS)
        
        args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
        url_list = [
            *build_url(args.user, 'user'),
            *build_url(args.reddit, 'reddit'),
            *build_url(args.target, 'target'),
        ]

        redl = RedditDownloader(
            sleep=not args.no_sleep,
            user_agent=args.user_agent,
            download_pictures=not args.no_pictures,
            download_videos=not args.no_videos,
            download_gifs=not args.no_gifs,
            save_metadata=args.metadata_json,
            max_connection_attempts=args.max_connection_attempts,
            request_timeout=args.request_timeout,
            download_nsfw=not args.no_nsfw,
            update_mode=args.update)

        _main(redl, url_list)

    except KeyboardInterrupt:
        print('Keyboard interrupt, exiting.')

if __name__ == "__main__":
    main()
