from django.conf import settings

def settings_context(request):
    """
        returns a dict with whitelisted settings
    """
    return {
        'THEME': getattr(settings, "THEME", "")
    }

def bingo(request):
    return {
        'settings': settings_context(request),
    }
