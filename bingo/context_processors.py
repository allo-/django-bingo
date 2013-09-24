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
    if not site_theme.startswith("http://") and \
            not site_theme.startswith("https://"):
        site_theme = static_url(site_theme)

    themes = list(getattr(settings, "THEMES", DEFAULT_THEMES))
    if len(themes) > 0:
        themes = [(_("Default"), "")] + list(themes)
    else:
        # if there is no theme list, the user cannot
        # reset the theme, so we remove it from session
        # and use the default one.
        if 'theme' in request.session:
            del request.session['theme']

    user_theme = request.session.get('theme', '')
    if user_theme != '' and not user_theme.startswith("http://") and \
            not user_theme.startswith("https://"):
        user_theme = static_url(user_theme)

    return {
        'site_theme': site_theme,
        'themes': themes,
        'user_theme': user_theme,
    }


def bingo(request):
    items = {
        'settings': settings_context(request),
    }
    for key, value in themes(request).items():
        items[key] = value

    return items
