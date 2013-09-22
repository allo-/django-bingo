from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


register = template.Library()


ALLOWED_TEMPLATE_SETTINGS_ACCESS = getattr(
    settings, "ALLOWED_TEMPLATE_SETTINGS_ACCESS",
    ("THEME", "THEMES")
)


@register.filter
def settings_value(name):
    if name in ALLOWED_TEMPLATE_SETTINGS_ACCESS:
        value = getattr(settings, name, u"")
        if isinstance(value, basestring):
            return mark_safe(value)
        else:
            return value
    else:
        return u""
