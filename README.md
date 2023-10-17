# reddit-dl 
### Limitless reddit downloader / No API no limit

* Download from r/cats or some NFSW sub, or user profile. All supported. 
* No api limit, make archives update them. 

# Commits

* Yes please, reddit-dl needs your commit.
* Just before commit, e-mail address on profile. 

# Installation 
#### Manuel Installation
```console
    # clone the repo
    $ git clone https://github.com/reddit-dl/reddit-dl.git

    # change the working directory to sherlock
    $ cd reddit-dl/

    # install the requirements
    $ python3 -m pip install -r requirements.txt

    # then call
    $ python3 reddit_dl.py --help
```

#### Installation with pip
```console
    # install
    $ pip install -U reddit-dl  

    # then call
    $ reddit-dl --help 
```


# Example usage:
```console
    # download to `cats` subreddit media
    $ reddit-dl https://www.reddit.com/r/cats/

    # update to downloaded `cats` subreddit media
    $ reddit-dl --update https://www.reddit.com/r/cats/` 

    # download to `cats` subreddit media with `-r`
    $ reddit-dl -r cats

    # update with folder name to downloaded `cats` subreddit media
    $ reddit-dl --update r-cats  

    # Not download gifs
    $ reddit-dl -u <username> --no-gifs
```
# Usage and Options

<!-- MANPAGE: BEGIN EXCLUDED SECTION -->

    usage: reddit_dl.py [-h] [--version] [-u [USER ...]] [-r [REDDIT ...]] [-V] [-P] [-G] [-N] [--update] [--user-agent USER_AGENT]
                        [--request-timeout N] [--max-connection-attempts N]
                        [target ...]

    Download pictures, gifs, videos along with their captions and other metadata from Reddit.

    Miscellaneous Options:
    -h, --help            Show this help message and exit.
    --version             Show version number and exit.

    What to Download:
    Specify a list of targets. For each of these, reddit-dl creates a folder and downloads all media content. The following targets are
    supported:

    target                Full url of users, subreddits or their local folder names.Exp. `https://reddit.com/r/UkrainianConflict/`
    -u [USER ...], --user [USER ...]
                            Usernames to download.
    -r [REDDIT ...], --reddit [REDDIT ...]
                            Subreddit names to download.

    What to Download of each Post:
    -V, --no-videos       Do not download videos.
    -P, --no-pictures     Do not download pictures.
    -G, --no-gifs         Do not download pictures.
    -N, --no-nsfw         Do not download NSFW content.

    Which Posts to Download:
    --update              For each target, stop when encountering the first already-downloaded content.

    How to Download:
    --user-agent USER_AGENT
                            User Agent to use for HTTP requests.
    --request-timeout N   Seconds to wait before timing out a connection request. Defaults to 300.
    --max-connection-attempts N
                            Maximum number of connection attempts until a request is aborted.

    https://github.com/reddit-dl/reddit-dl



<!-- MANPAGE: END EXCLUDED SECTION -->

