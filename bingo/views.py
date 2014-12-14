from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from django.utils.translation import ugettext as _
from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.conf import settings
from django.core.cache import cache
from django.middleware.cache import CacheMiddleware
from django.contrib.auth.models import User
import json

from models import Word, Game, BingoBoard, BingoField, get_game
from forms import CreateForm, ClaimForm, ReclaimForm
from forms import ChangeThemeForm, RateGameForm
import image as image_module
import times


GAME_START_DISABLED = getattr(settings, "GAME_START_DISABLED", False)
THUMBNAIL_CACHE_EXPIRY = getattr(
    settings,
    "THUMBNAIL_CACHE_EXPIRY",
    5 * 60)
OLD_THUMBNAIL_CACHE_EXPIRY = getattr(
    settings,
    "OLD_THUMBNAIL_CACHE_EXPIRY",
    24 * 60 * 60)
USE_SSE = hasattr(settings, "SSE_URL")

if USE_SSE:
    REDIS_HOST = getattr(settings, "REDIS_HOST", None)
    REDIS_PORT = getattr(settings, "REDIS_PORT", None)
    from redis import Redis
    kwargs = {}
    if REDIS_HOST:
        kwargs['host'] = REDIS_HOST
    if REDIS_PORT:
        kwargs['port'] = REDIS_PORT
    redis = Redis(**kwargs)


def _get_user_bingo_board(request):
    bingo_board = None
    game = get_game(site=get_current_site(request), create=False)
    session_board_id = request.session.get('board_id', None)
    user = request.user if request.user.is_authenticated() else None
    ip = request.META['REMOTE_ADDR']

    # try the board_id in the session
    if not session_board_id is None:
        try:
            bingo_board = BingoBoard.objects.get(id=session_board_id,
                                                 game=game)
            bingo_board.ip = ip
        except BingoBoard.DoesNotExist, e:
            pass
        # double board_id?
        except BingoBoard.MultipleObjectsReturned:
            pass

    if user:
        try:
            bingo_board = BingoBoard.objects.get(game=game, user=user)
        except BingoBoard.DoesNotExist, e:
            pass

    # no board_id in the session, try the ip
    if bingo_board is None:
        try:
            # user=None is required, to prevent anonymous users from
            # getting the board of a authenticated user on the same ip.
            bingo_board = BingoBoard.objects.get(game=game, ip=ip, user=None)
        except BingoBoard.DoesNotExist, e:
            pass

    if bingo_board is not None and not bingo_board.game.is_expired():
        BingoBoard.objects.filter(id=bingo_board.id).update(
            last_used=times.now())
        request.session['board_id'] = bingo_board.id

    return bingo_board


def _get_image_name(board_id, marked=False, voted=False):
    if voted:
        filename = _("board_{0}_voted").format(board_id)
    elif marked:
        filename = _("board_{0}_marked").format(board_id)
    else:
        filename = _("board_{0}").format(board_id)

    return filename


def _publish_num_users(site_id, num_users=None, num_active_users=None):
    if num_users is not None:
        redis.publish("num_users", json.dumps({
            'site_id': site_id,
            'num_users': num_users,
        }))
    if num_active_users is not None:
        redis.publish("num_active_users", json.dumps({
            'site_id': site_id,
            'num_active_users': num_active_users,
        }))


def main(request, reclaim_form=None, create_form=None):
    game = get_game(site=get_current_site(request), create=False)
    bingo_board = _get_user_bingo_board(request)

    create_form = CreateForm(prefix="create", game=game)
    reclaim_form = ReclaimForm(prefix="reclaim")

    boards = BingoBoard.objects.filter(game=game)
    old_games = Game.objects.filter(
        site=get_current_site(request)
    ).exclude(
        # games without any boards created
        bingoboard=None
    ).exclude(
        # games without game_id are hidden
        game_id=None
    ).order_by("-created")

    if game is not None:
        old_games = old_games.exclude(id=game.id)

    return render(request, "bingo/main.html", {
        'my_board': bingo_board,
        'create_form': create_form,
        'reclaim_form': reclaim_form,
        'boards': boards,
        'current_game': game,
        'old_games': old_games,
        'can_start_game': not GAME_START_DISABLED,
        })


def game(request, game_id):
    bingo_board = _get_user_bingo_board(request)
    return render(request, "bingo/game.html", {
        'game': get_object_or_404(
            Game, site=get_current_site(request), game_id=game_id),
        'my_board': bingo_board
    })


def profile(request, username):
    user = get_object_or_404(User, username=username)
    form = ClaimForm(request.POST or None, user=user)
    form.is_valid()
    boards = user.bingoboard_set.filter(game__site=get_current_site(request))
    return render(request, "bingo/profile.html",
            {'profile_user': user, 'boards': boards, 'claim_form': form})


def reclaim_board(request):
    ip = request.META['REMOTE_ADDR']
    game = get_game(site=get_current_site(request), create=False)
    if game is not None:
        Game.objects.filter(id=game.id).update(last_used=times.now())
    bingo_board = _get_user_bingo_board(request)

    if not bingo_board is None:
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    if request.POST:
        reclaim_form = ReclaimForm(request.POST, game=game, prefix="reclaim")
        if reclaim_form.is_valid():
            bingo_board = reclaim_form.cleaned_data['bingo_board']
            request.session['board_id'] = bingo_board.id
            bingo_board.ip = ip
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={'board_id':
                                                   bingo_board.board_id}))
    else:
        reclaim_form = ReclaimForm(prefix="reclaim")
    create_form = CreateForm(prefix="create", game=game)
    return render(request,
                  "bingo/reclaim_board.html", {
                      'reclaim_form': reclaim_form,
                      'create_form': create_form,
                  })


def create_board(request):
    bingo_board = _get_user_bingo_board(request)
    game = bingo_board.game if bingo_board is not None else None
    user = request.user

    if bingo_board:
        Game.objects.filter(id=bingo_board.game.id).update(
            last_used=times.now())
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    elif request.POST:
        create_form = CreateForm(
            request.POST,
            prefix="create",
            game=game)

        if create_form.is_valid():
            with transaction.commit_on_success():
                ip = request.META['REMOTE_ADDR']
                password = create_form.cleaned_data.get('password')
                game_description = create_form.cleaned_data.get(
                    'description', '')
                game = get_game(
                    site=get_current_site(request),
                    description=game_description,
                    create=True)
                Game.objects.filter(id=game.id).update(
                    last_used=times.now())

                # if the user is logged in, associate the board with
                # the user, and ignore the password
                # (so no other user can claim the board)
                user = user if user.is_authenticated() else None
                if user:
                    password = None

                bingo_board = BingoBoard(
                    game=game, user=user, ip=ip, password=password)
                bingo_board.save()

                if USE_SSE:
                    _publish_num_users(game.site.id, game.num_users(),
                                       game.num_active_users())

                return redirect(reverse(bingo, kwargs={
                    'board_id': bingo_board.board_id}))
        else:
            reclaim_form = ReclaimForm(prefix="reclaim")
            return render(
                request,
                "bingo/reclaim_board.html",
                {
                    'reclaim_form': reclaim_form,
                    'create_form': create_form,
                }
            )
    else:
        return redirect(reverse(main))


def bingo(request, board_id=None):
    bingo_board = get_object_or_404(
        BingoBoard, board_id=board_id,
        game__site=get_current_site(request)
    )
    my_bingo_board = _get_user_bingo_board(request)
    fields_on_board = bingo_board.get_board_fields().select_related()
    all_word_fields = bingo_board.get_all_word_fields().order_by(
        "word__word").select_related()

    return render(request, "bingo/bingo.html", {
        "fields_on_board": fields_on_board,
        "board": bingo_board,
        "my_board": my_bingo_board,
        "all_word_fields": all_word_fields,
        "rate_form": RateGameForm(),
        })


class VoteException(Exception):
    """
        something went wrong voting on a field.
        (i.e. the field does not belong to the user's board)
    """
    pass


def _post_vote(user_bingo_board, field, vote):
    """
        change vote on a field
        @param user_bingo_board: the user's bingo board or None
        @param field: the BingoField to vote on
        @param vote: the vote property from the HTTP POST
        @raises: VoteException: if user_bingo_board is None or
        the field does not belong to the user's bingo board.
        @raises Http404: If the BingoField does not exist.
    """

    if field.board != user_bingo_board:
        raise VoteException(
            "the voted field does not belong to the user's BingoBoard")

    if vote == "0":
        field.vote = None
    elif vote == "+":
        field.vote = True
    elif vote == "-":
        field.vote = False
    field.save()

    # update last_used with current timestamp
    game = user_bingo_board.game
    Game.objects.filter(id=game.id).update(
        last_used=times.now())

    # invalidate vote cache
    vote_counts_cachename = 'vote_counts_game={0:d}'.format(
        field.board.game.id)
    cache.delete(vote_counts_cachename)

    # publish the new vote counts for server-sent events
    if USE_SSE:
        votes = field.num_votes()
        redis.publish("word_votes", json.dumps({
            'site_id': game.site.id,
            'word_id': field.word.id,
            'vote_count': votes,
        }))
        redis.publish("field_vote", json.dumps({
            'site_id': game.site.id,
            'field_id': field.id,
            'vote': vote,
        }))


def vote(request, ajax, board_id=None):
    user_bingo_board = _get_user_bingo_board(request)
    field = None

    # post request: update field.vote
    if "field_id" in request.POST and times.is_after_votetime_start():
        field_id = request.POST.get("field_id", 0)
        field = get_object_or_404(BingoField, id=field_id)
        vote = request.POST.get("vote", "0")
        try:
            _post_vote(user_bingo_board, field, vote)
        except VoteException:
            pass  # ignore the vote

    # form submitted without ajax, redirect back to the bingo page
    if not ajax:
        if field:
            return redirect(
                reverse(bingo, kwargs={"board_id": field.board.board_id}))
        else:
            return redirect(reverse(main))

    # page submitted with ajax, return vote data as json
    if board_id is not None:  # board id given in the url
        bingo_board = get_object_or_404(BingoBoard, id=board_id)
    elif user_bingo_board is not None:  # user's bingo board
        bingo_board = user_bingo_board
    else:  # missing the needed parameters
        # Set data to {} to prevent an AttributeError
        return HttpResponse(json.dumps({}), content_type="application/json")

    # add data about the game
    game = bingo_board.game
    num_users = game.num_users()
    num_active_users = game.num_active_users()
    data = {
        'num_users': num_users,
        'num_active_users': num_active_users,
        'is_expired': bingo_board.game.is_expired(),
    }

    # send user number, if changed
    if USE_SSE:
        old_num_users = cache.get(
            "num_users__site={0:d}".format(game.site.id))
        old_num_active_users = cache.get(
            "num_active_users__site={0:d}".format(game.site.id))

        if old_num_users != num_users:
            cache.set("num_users", num_users)
            _publish_num_users(game.site.id, num_users=num_users)
        if old_num_active_users != num_active_users:
            cache.set("num_active_users", num_active_users)
            _publish_num_users(game.site.id, num_active_users=num_active_users)

    for field in bingo_board.bingofield_set.all():
        # None="0", "+"=vote, "-"=veto
        vote = "0" if field.vote is None else "+" if field.vote else "-"
        data[field.id] = (vote, field.num_votes())

    return HttpResponse(json.dumps(data), content_type="application/json")


def rate_game(request):
    bingo_board = _get_user_bingo_board(request)
    if bingo_board:
        form = RateGameForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            if rating == "None":
                rating = None
            BingoBoard.objects.filter(id=bingo_board.id).update(rating=rating)
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    else:
        return redirect(reverse(main))


def image(request, board_id, marked=False, voted=False):
    bingo_board = get_object_or_404(
        BingoBoard, board_id=board_id,
        game__site=get_current_site(request))
    response = HttpResponse(content_type="image/png")
    filename = _get_image_name(board_id, marked, voted) + ".png"
    response['Content-Disposition'] = 'filename={0}'.format(filename)
    im = image_module.get_image(bingo_board, marked, voted)
    im.save(response, "png")
    return response


def thumbnail(request, board_id, marked=False, voted=False):
    bingo_board = get_object_or_404(
        BingoBoard, board_id=board_id,
        game__site=get_current_site(request))

    # check if the board is from an expired game
    game_expired_cachename = "game_expired__board={0:d}".format(
        int(bingo_board.id))
    game_expired = cache.get(
        game_expired_cachename)
    if game_expired is None:
        game_expired = bingo_board.game.is_expired()
        cache.set(
            game_expired_cachename,
            game_expired, 60 * 60)

    # when the game of the board is expired,
    # the thumbnail can be cached longer.
    if game_expired:
        m = CacheMiddleware(cache_timeout=OLD_THUMBNAIL_CACHE_EXPIRY)
    else:
        m = CacheMiddleware(cache_timeout=THUMBNAIL_CACHE_EXPIRY)

    response = m.process_request(request)
    if response:  # cached
        return response

    response = HttpResponse(content_type="image/png")
    filename = _get_image_name(board_id, marked, voted) + \
        "_" + _("thumbnail") + ".png"
    response['Content-Disposition'] = 'filename={0}'.format(filename)
    im = image_module.get_thumbnail(bingo_board, marked, voted)
    im.save(response, "png")

    return m.process_response(request, response)


def change_theme(request):
    if request.POST:
        form = ChangeThemeForm(request.POST)
        if form.is_valid():
            request.session['theme'] = form.cleaned_data['theme']
    return redirect(reverse('bingo.views.main'))
