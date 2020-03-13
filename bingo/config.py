from django.db import models
from django.contrib.sites.models import Site
from colorful.fields import RGBColorField
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import ugettext as _, pgettext_lazy

def default_time():
    now = timezone.get_current_timezone().normalize(timezone.now())
    return now.replace(hour=0, minute=0, second=0)

class Config(models.Model):
    site = models.OneToOneField(Site, unique=True)
    # Game Start and End
    start_enabled = models.BooleanField(default=False,
        help_text="Disable to disallow new games, even in the game times.")
    start_time_begin = models.TimeField(default=None, blank=True, null=True,
        help_text="Begin of the time where games can be started "
        "(usually before the start of the show).")
    start_time_end = models.TimeField(default=None, blank=True, null=True,
        help_text="End of the time where games can be started "
        "(usually before the start of the show).")
    vote_start_time = models.TimeField(default=None, blank=True, null=True,
        help_text="Time at which voting starts "
        "(usually the start of the show).")
    end_time = models.TimeField(default=None, blank=True, null=True,
        help_text="Time at which a game is stopped (end of the show).")

    week_days_monday = models.BooleanField(default=True,
        help_text="True, when games can be started on mondays.")
    week_days_tuesday = models.BooleanField(default=True,
        help_text="True, when games can be started on tuesdays.")
    week_days_wednesday = models.BooleanField(default=True,
        help_text="True, when games can be started on wednesdays.")
    week_days_thursday = models.BooleanField(default=True,
        help_text="True, when games can be started on thursdays.")
    week_days_friday = models.BooleanField(default=True,
        help_text="True, when games can be started on fridays.")
    week_days_saturday = models.BooleanField(default=True,
        help_text="True, when games can be started on saturdays.")
    week_days_sunday = models.BooleanField(default=True,
        help_text="True, when games can be started on sundays.")

    # Timeouts
    soft_timeout = models.IntegerField(default=None, blank=True, null=True,
        help_text = "Minutes after which inactive games are stopped. "
        "Either Soft Timeout or Hard Timeout must be set or your "
        "games will never stop.")
    hard_timeout = models.IntegerField(default=None, blank=True, null=True,
        help_text = "Minutes after which games are stopped. "
        "Either Soft Timeout or Hard Timeout must be set or your "
        "games will never stop.")
    user_activity_timeout = models.IntegerField(default=5, blank=True,
        null=True,
        help_text = "Minutes after which a user is considered inactive.")
    # Description
    description_enabled = models.BooleanField(default=False,
        help_text="Allow the User starting the game to set a description.")
    # Look and Feel
    thumbnails_enabled = models.BooleanField(default=True)
    colors_from = models.IntegerField(default=80,
        help_text="Color intensity for the game fields.")
    colors_to = models.IntegerField(default=160,
        help_text="Color intensity for the game fields.")
    middle_field_datetime_format = models.CharField(max_length=30,
        default="%Y-%m-%d %H:%M",
        help_text="Format for the date and time on the middle field.")
    # Twitter integration
    tweetbutton_text = models.CharField(max_length=280, blank=True,
        default=pgettext_lazy("tweet text", "My bingo board:"),
        help_text="The text that is used when a user clicks " +
        "the tweet or toot button.")
    tweetbutton_hashtags = models.CharField(max_length=280, blank=True,
        default="bingo",
        help_text="A comma separated list of hashtags that are used when " +
        "the user clicks the tweet or toot button.")
    twittercard_account = models.CharField(max_length=280, blank=True,
        default="",
        help_text="The Twitter account associated with the Twitter card " +
        "(useful for Twitter statistics)")
    twittercard_image = models.URLField(blank=True,
        default="",
        help_text="An Image URL for a Twitter card image." +
        " (leave blank to use the default)")
    # Description and announcements on the main page
    bingo_description = models.TextField(blank=True, default="",
        help_text="An optional description of the bingo, that will be" +
        "shown on the main page. HTML is allowed, so make sure to escape <, >" +
        " and similar characters correctly and close all your HTML tags.")

    def __str__(self):
        return "Configuration for site {0}".format(self.site)

def get(key, request=None, site=None, *args, **kwargs):
    try:
        if not site:
            assert request, "Either request or site must be set."
            site = get_current_site(request)

        (config, created) = Config.objects.get_or_create(site=site)
        return getattr(config, key)
    except AttributeError as e:
        if 'default' in kwargs:
            return kwargs['default']
        else:
            raise e
