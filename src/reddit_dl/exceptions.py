# -*- coding: utf-8 -*-

class RedditDlException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""
    pass

class ConnectionException(RedditDlException):
    pass

class BadResponseException(RedditDlException):
    pass

class ExistFileOnUpdateModeException(RedditDlException):
    pass