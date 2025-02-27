"""
Monkey-patch django's reverse function to add resource_link_id to all URLs.
"""
from urllib.parse import urlparse, urlunparse, parse_qs
from urllib.parse import urlencode

from .thread_local import get_current_request

import logging

django_reverse = None

logger = logging.getLogger(__name__)


def reverse(*args, **kwargs):
    """
    Call django's reverse function and append the current resource_link_id as a
    query parameter

    :param kwargs['exclude_resource_link_id']: Do not add the resource link id
    as a query parameter
    :returns Django named url
    """
    request = get_current_request()

    # Check for custom exclude_resource_link_id kwarg and remove it before
    # passing kwargs to django reverse
    exclude_resource_link_id = kwargs.pop('exclude_resource_link_id', False)

    url = django_reverse(*args, **kwargs)
    if not exclude_resource_link_id:
        # Append resource_link_id query param if exclude_resource_link_id kwarg
        # was not passed or is False
        logger.info(f'URL: {url}')
        parsed = urlparse(url)
        logger.info(f'Pared URL: {parsed}')
        query = parse_qs(parsed.query)
        logger.info(f'Query: {query}')
        if 'resource_link_id' not in list(query.keys()):
            query['resource_link_id'] = request.LTI.get('resource_link_id')
            url = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params,
                 urlencode(query), parsed.fragment)
            )
            logger.info(f'New URL: {url}')
    return url


def patch_reverse():
    """
    Monkey-patches the reverse function. Will not patch twice.
    """
    global django_reverse
    from django import urls
    if urls.reverse is not reverse:
        django_reverse = urls.reverse
        urls.reverse = reverse

        # Django 1.10 moves url helper functions like `reverse` into a new urls
        # module, so we need to patch it as well.  In addition, the
        # django.shortcuts module now includes `reverse` directly, and the
        # module appears to be loaded before middleware so we need to
        # retroactively patch that `reverse` reference as well.
        try:
            from django import urls, shortcuts

            urls.reverse = reverse
            shortcuts.reverse = reverse
        except ImportError:
            pass

patch_reverse()
