django-bingo
------------

django-bingo is a bingo app to play bingo games like "bullshit bingo" while listening together to some radio show and marking the words, which were mentioned.

Dependencies
------------

Install everything from requirements.txt, e.g., with `pip install -e requirements.txt`.

Additional dependencies for SSE:

* sse 1.2
* redis 2.10.3
* flask 0.10.1
* gevent 1.0.2

Other: You need a ttf-file as font for the image export.

Installing
----------

Create a django project. Then add the following options to your settings.py

* append to ```INSTALLED_APPS``` (make sure ``bingo`` is included first)
    * 'bingo'
    * 'jquery'
    * 'colorful'
    * 'registration'
* ```FONT_PATH``` = '/path/to/font.ttf'

Include the bingo-app in your project urls.py, like this:
```url(r'^', include('bingo.urls'))```
Include the ```registration``` app like this:
```url(r'^accounts/', include('registration.backends.simple.urls'))```

Registration is only tested with the ```simple``` backend.
You can use other ```django-registration``` backends, but you will need to add additional templates and views.

You can use the Sites framework to add several different Bingo sites.
Different Sites have different sets of Words, and they will generate a different set of Games, so the Bingos are independend from each other.

Upgrading
---------

For upgrading from an older version you may need to use ```manage.py migrate```, if the database scheme was changed.

When upgrading from versions prior to 1.4, upgrade first using ``south`` and ```django 1.6```. Then upgrade to the current version using the django migrations.

Settings
--------

#### required settings

* Add ``bingo.context_processors.bingo`` to the ``context_processors`` in the [OPTIONS](https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-TEMPLATES-OPTIONS) section of the ```TEMPLATE``` settings.
* Add at least one of
    * ```GAME_HARD_TIMEOUT``` time after which a game is stopped
    * ```GAME_SOFT_TIMEOUT``` time after which a game without any activity is stopped

#### optional settings

see CONFIGURATION.md

Customizing
-----------

Many minor changes can be done with [django-apptemplates](https://pypi.python.org/pypi/django-apptemplates/). See their documentation for how to add the module to the project.

After installation you can use add additional template folders in ``DIRS`` list of the ``TEMPLATES`` option in ``settings.py`` for customizing your installation. this allows for example a list like ``["thisbingosite_templates", "bingosites_templates", "default_templates"]`` for using template folders shared between different sites.

Example for ``thisbingosite_templates/bingo/main.html``:

    {% extends "bingo:bingo/base.html %}
    {% block extra_content_top %}
	    Welcome to my django-bingo game!
	    {{ block.super }}
	{% endblock %}
