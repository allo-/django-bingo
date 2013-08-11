django-bingo
------------

django-bingo is a bingo-app, for playing bingo games like "bullshit bingo", by listening together to some radio show and clicking the words, which were mentioned.

Dependencies
------------

Python packages:

* django 1.5
* django-jquery 1.9.1
* django-colorful 0.1.3
* pytz 2013b
* pillow 2.1.0

Other: a ttf-file as font for the image-export.

Installing
----------

Create a django project. Then add the following options to your settings.py

* append to ```INSTALLED_APPS```
    * 'bingo'
    * 'jquery'
    * 'colorful'
* ```FONT_PATH``` = '/path/to/font.ttf'

include the bingo-app in your project urls.py, like this:
```url(r'^', include('bingo.urls'))```

You can use the Sites framework to add several different Bingo sites.
Different Sites have different sets of Words, and they will generate a different set of Games, so the Bingos are independend from each other.

Settings
--------

The game uses the following settings:

required:

* ```FONT_PATH``` the ttf font used to generate images.

optional:

* ```BORDER``` size of the field border in the images.
* ```H_BOX_PADDING```, ```V_BOX_PADDING``` padding of the fields in the images.
* ```H_LINE_MARGIN```, ```V_LINE_MARGIN``` margin of the text in the images. Needed to render multiline text nicely.
* ```COLOR_FROM```, ```COLOR_TO``` two integer values. the RGB-values of the randomly generated color for marking fields will be chosen from this range.
* ```FONT_SIZE``` the font size in the images.
* ```GAME_START_TIMES``` ```None``` for no restriction or ```((start hour, start minute), (end hour, end minute))``` for restricting the start time to a special time range (i.e. the broadcasting time of the radio show)
* ```GAME_HARD_TIMEOUT``` minutes after the game will be ended, i.e. the duration of the radio show)
* ```GAME_SOFT_TIMEOUT``` minutes of inactivity, after which the game will be be ended.
* ```USER_ACTIVY_TIMEOUT``` minutes after which a user is no longer considered active (number of active users is shown on the bingo page)
* ```SALT``` a salt for hashing the Bingo password hashs. The salt needs to be static, so a BingoBoard can be selected with a query for the hashed password. The users should not use important passwords there, anyway.
