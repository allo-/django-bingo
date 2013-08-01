from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.conf import settings

from models import Word, Game, BingoBoard


GAME_SOFT_TIMEOUT = getattr(settings, "GAME_SOFT_TIMEOUT", 120)
GAME_HARD_TIMEOUT = getattr(settings, "GAME_HARD_TIMEOUT", 300)


def _get_game():
    """
        get the current game. creates a new one, if the old one is expired.
    """

    games = Game.objects.order_by("-created")
    # no game, yet
    if games.count() == 0:
        game = Game()
        game.save()

    # game expired, because no one used it
    elif (timezone.now() - games[0].last_used).seconds \
            > (GAME_SOFT_TIMEOUT * 60):
        game = Game()
        game.save()

    # game expired, because its too old, even when someone is using it
    elif (timezone.now() - games[0].created).seconds \
            > (GAME_HARD_TIMEOUT * 60):
        game = Game()
        game.save()

    # there is a valid game
    else:
        game = games[0]
        game.save()  # update timestamp
    return game


def _create_new_bingo(game, ip):
    bingo_board = BingoBoard(game=game, ip=ip)
    bingo_board.save()
    bingo_id = bingo_board.id
    return bingo_id


def bingo(request, bingo_id=None):
    game = _get_game()
    session_bingo_id = request.session.get('bingo_id', None)
    ip = request.META['REMOTE_ADDR']

    # if a bingo_id is given in the url, just show this bingo
    if not bingo_id is None:
        bingo_board = get_object_or_404(BingoBoard, id=bingo_id)
        fields = bingo_board.bingofield_set.all().order_by("position")
        return render(request, "bingo.html", {"fields": fields})

    # no bingo_id in the url, no bingo_id in the session, try the ip
    elif bingo_id is None and session_bingo_id is None:
        try:
            bingo_board = BingoBoard.objects.get(game=game, ip=ip)
            bingo_id = bingo_board.id
        except BingoBoard.DoesNotExist:
            bingo_id = _create_new_bingo(game, ip)

        request.session['bingo_id'] = bingo_id
        return redirect(reverse(bingo, kwargs={'bingo_id': bingo_id}))

    # no bingo_id in the url, but a bingo_id in the session
    elif bingo_id is None and not session_bingo_id is None:
        try:
            bingo_board = BingoBoard.objects.get(id=session_bingo_id,
                                                 game=game)
            bingo_id = bingo_board.id
        except BingoBoard.DoesNotExist, e:
            bingo_id = _create_new_bingo(game, ip)

        request.session['bingo_id'] = bingo_id
        return redirect(reverse(bingo, kwargs={'bingo_id': session_bingo_id}))
