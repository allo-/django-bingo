django-bingo Configuration
-------------

### Game Times

* ```GAME_START_DISABLED``` set to ```True```, to disable starting new games.
* ```GAME_START_TIMES``` ```None``` for no restriction or ```((start hour, start minute), (end hour, end minute))``` for restricting the start time to a special time range (i.e. the broadcasting time of the radio show)
* ```GAME_END_TIME``` ```None``` for no restriction or ```(end hour, end minute)``` for setting a time, after which the game is ended. The end time needs to be outside of the ```GAME_START_TIMES``` interval.
* ```VOTE_START_TIME``` ```None``` for no restriction or ```(hour, minute)``` for setting a start time for voting. This can be used to allow board creation before voting starts. The time needs to be between the ```GAME_START_TIMES[0]```(starttime start) and ```GAME_END_TIME```.
* ```GAME_HARD_TIMEOUT``` minutes after the game will be ended, i.e. the duration of the radio show)
* ```GAME_SOFT_TIMEOUT``` minutes of inactivity, after which the game will be be ended.
* ```USER_ACTIVE_TIMEOUT``` minutes after which a user is no longer considered active (number of active users is shown on the bingo page)
* ```POLLING_INTERVAL``` how often to poll for new votes.
* ```POLLING_INTERVAL_SSE``` how often to poll for new votes, when server-sent events are used. ```0``` disables polling, when server-sent events are used.

#### Notes
* At least one of the settings ```GAME_HARD_TIMEOUT``` or ```GAME_SOFT_TIMEOUT``` must be set, even when ```GAME_END_TIME``` is set. When both are ```None```, the game never ends and no new game can be created on the next day.
* You may want to set ```POLLING_INTERVAL_SSE``` to a smaller (but bigger than 0) value than ```USER_ACTIVE_TIMEOUT```, to mark users as active, who still have their boards open, but did not vote for ```USER_ACTIVE_TIMEOUT``` minutes.

### Image style

* ```BORDER``` size of the field border in the images.
* ```H_BOX_PADDING```, ```V_BOX_PADDING``` padding of the fields in the images.
* ```H_LINE_MARGIN```, ```V_LINE_MARGIN``` margin of the text in the images. Needed to render multiline text nicely.
* ```COLOR_FROM```, ```COLOR_TO``` two integer values. the RGB-values of the randomly generated color for marking fields will be chosen from this range.
* ```NEUTRAL_FIELD_COLOR``` background color of neutral fields
* ```NEUTRAL_WORD_COLOR``` word color of neutral fields
* ```MIDDLE_FIELD_COLOR``` background color of middle fields
* ```MIDDLE_WORD_COLOR``` word color of middle fields
* no ```MARKED_FIELD_COLOR```, because its chosen randomly from ```COLOR_FROM``` to ```COLOR_TO```
* ```MARKED_WORD_COLOR``` word color of marked fields
* no ```VOTED_FIELD_COLOR```, because its chosen randomly from ```COLOR_FROM``` to ```COLOR_TO```
* ```VOTES_WORD_COLOR``` word color of neutral fields
* ```VETO_FIELD_COLOR``` background color of veto fields
* ```VETO_WORD_COLOR``` word color of veto fields
* ```FONT_SIZE``` the font size in the images.
* ```BINGO_IMAGE_DATETIME_FORMAT``` format for the datetime in the board images

### Thumbnails

* ```THUMBNAILS_ENABLED``` show board thumbnails in the board list.
* ```THUMBNAIL_CACHE_EXPIRY``` time a board thumbnail is cached (seconds).
* ```OLD_THUMBNAIL_CACHE_EXPIRY``` time a board thumbnail from an old game is cached (seconds).
* ```THUMBNAIL_WIDTH``` / ```THUMBNAIL_HEIGHT``` maximum width/height of the thumbnails.

### Server-sent Events

With [server-sent events](http://www.html5rocks.com/en/tutorials/eventsource/basics/), the game needs less polling for vote numbers and the numbers are displayed almost instantly. You need a [Redis](http://redis.io/) database and you have to run a second process to deliver the events.

Configuration:

* install python modules ```sse```, ```flask```, ```redis``` and ```gevent```.
* deploy bin/django-bingo-serversent.py somewhere. you can set the ```SITE_ID``` of your bingo instance via the environment variable ```SITE_ID```. You need to use some async server, such as ```gunicorn``` with ```gevent``` workers.
  * At the moment you need to edit the script to change the redis server address. Depending on your deployment you may need to change the ```@application.route("/")``` to the path in your url as well.
* set ```USE_SSE``` to ```True```
* set ```SSE_URL``` to the url, where the server can be reached.
* ```REDIS_HOST``` and ```REDIS_PORT``` can be used to specify the address of your redis instance for the django app.

### Themes

* ```THEME``` relative or absolute URL to a theme. When the string does not start with "/", "http://" or "https://", the string is interpreted as a [static files path](https://docs.djangoproject.com/en/1.5/ref/contrib/staticfiles/). (Default: None)
* ```THEMES``` A list of themes, which will be available via a theme chooser. Example: ```THEMES = (('dark', 'bingo/themes/dark.css'), ('some other theme', 'http://mysite/mytheme.css'))``` (Default: a "dark" theme. ```None``` will disable the theme chooser)

### Other

* ```SALT``` a salt for hashing the Bingo password hashs. The salt needs to be static, so a BingoBoard can be selected with a query for the hashed password. The users should not use important passwords there, anyway.
* ```GAME_DESCRIPTION_DISABLED``` disable the "Game Description" field for new Games.

## django settings

* ```SITE_ID``` id of the current site in the Sites-Framework
* [```CACHE```](https://docs.djangoproject.com/en/1.5/topics/cache/#setting-up-the-cache)
  You need to increase ```'OPTIONS': {'MAX_ENTRIES': XXXXX}``` to cache enough entries.
  The cached entries can quickly add up to a large number of keys, while the stored data is rather small,
  and having too little cache will rapidly increase the number of database queries.
  You need at least:
  * **word cache:** 1 entry per board currently viewed by users or visible on the front page.
  * **thumbnail cache:** 1 entry per thumbnail visible on the front page or viewed on game pages.
  * **vote cache:** 2 entries per game currently viewed by users or visible on front page.
  * **game_expired:** 1 entry per game.
  * **Note:*** the "visible on the front page" is only relevant, when thumbnails are enabled.
  * **Example:** 50 words, 10 games visible, each with 10 boards: 100 + 100 + 2*100 + 10 = 410 entries.
