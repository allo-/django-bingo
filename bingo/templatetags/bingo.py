from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


register = template.Library()


ALLOWED_TEMPLATE_SETTINGS_ACCESS = getattr(
    settings, "ALLOWED_TEMPLATE_SETTINGS_ACCESS",
    (,)
)


@register.filter
def settings_value(name):
    if name in ALLOWED_TEMPLATE_SETTINGS_ACCESS:
        return mark_safe(getattr(settings, name, u""))
    else:
        return u""
