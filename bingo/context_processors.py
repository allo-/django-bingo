from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

static_url = staticfiles_storage.url


DEFAULT_THEMES = (
    ('Dark', 'bingo/themes/dark.css'),
)


def settings_context(request):
    """
        returns a dict with whitelisted settings
    """
    return {
    }


def themes(request):
    STATIC_ROOT = getattr(settings, "STATIC_ROOT", "")

    site_theme = getattr(settings, "THEME", "")
    if site_theme != '' and not site_theme.startswith("http://") \
            and not site_theme.startswith("https://"):
        site_theme = static_url(site_theme)

    themes = list(getattr(settings, "THEMES", DEFAULT_THEMES))
    if len(themes) > 0:
        themes = [(_("Default"), "")] + list(themes)
        for i in xrange(len(themes)):
            theme_name, theme_url = themes[i]
            if theme_url != '' and not theme_url.startswith("http://") \
                    and not theme_url.startswith("https://"):
                themes[i] = (theme_name, static_url(theme_url))
    else:
        # if there is no theme list, the user cannot
        # reset the theme, so we remove it from session
        # and use the default one.
        if 'theme' in request.session:
            del request.session['theme']

    user_theme = request.session.get('theme', '')

    return {
        'site_theme': site_theme,
        'themes': themes,
        'user_theme': user_theme,
    }


def bingo(request):
    sse_url = getattr(settings, "SSE_URL", None)
    use_sse = True if hasattr(settings, "USE_SSE") and sse_url else False
    polling_interval = getattr(settings, "POLLING_INTERVAL", 10)
    polling_interval_sse = getattr(settings, "POLLING_INTERVAL", 120)
    items = {
        'settings': settings_context(request),
        'use_sse': use_sse,
        'sse_url': sse_url,
        'polling_interval': polling_interval,
        'polling_interval_sse': polling_interval_sse,
    }
    for key, value in themes(request).items():
        items[key] = value

    return items
