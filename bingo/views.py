from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site
from django.utils.translation import ugettext as _
from django.http import HttpResponse
import json

from models import Word, Game, BingoBoard, BingoField, get_game
from forms import CreateForm, ReclaimForm

from image import get_image


def _get_user_bingo_board(request):
    bingo_board = None
    game = get_game(site=get_current_site(request), create=False)
    session_board_id = request.session.get('board_id', None)
    ip = request.META['REMOTE_ADDR']

    # try the board_id in the session
    if not session_board_id is None:
        try:
            bingo_board = BingoBoard.objects.get(board_id=session_board_id,
                                                 game=game)
            bingo_board.ip = ip
        except BingoBoard.DoesNotExist, e:
            pass

    # no board_id in the session, try the ip
    if bingo_board is None:
        try:
            bingo_board = BingoBoard.objects.get(game=game, ip=ip)
            request.session['board_id'] = bingo_board.board_id
        except BingoBoard.DoesNotExist, e:
            pass

    if bingo_board is not None and not bingo_board.game.is_expired():
        bingo_board.save()  # update last_used

    return bingo_board


def main(request, reclaim_form=None, create_form=None):
    game = get_game(site=get_current_site(request), create=False)
    bingo_board = _get_user_bingo_board(request)
    create_form = CreateForm()
    reclaim_form = ReclaimForm()
    return render(request, "main.html", {
        'my_board': bingo_board,
        'create_form': create_form,
        'reclaim_form': reclaim_form,
        'boards': BingoBoard.objects.filter(game=game),
        'games': Game.objects.filter(
            site=get_current_site(request)).order_by("-created"),
        })


def reclaim_board(request):
    ip = request.META['REMOTE_ADDR']
    game = get_game(site=get_current_site(request), create=False)
    game.save()  # update last_used
    bingo_board = _get_user_bingo_board(request)
    if not bingo_board is None:
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    if request.POST:
        reclaim_form = ReclaimForm(request.POST, game=game)
        if reclaim_form.is_valid():
            bingo_board = reclaim_form.cleaned_data['bingo_board']
            request.session['board_id'] = bingo_board.board_id
            bingo_board.ip = ip
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={'board_id':
                                                   bingo_board.board_id}))
    else:
        reclaim_form = ReclaimForm()
    create_form = CreateForm()
    return render(request,
                  "reclaim_board.html", {
                      'reclaim_form': reclaim_form,
                      'create_form': create_form,
                  })


def create_board(request):
    bingo_board = _get_user_bingo_board(request)
    if bingo_board:
        bingo_board.game.save()  # update last_used
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    elif request.POST:
        create_form = CreateForm(request.POST)
        if create_form.is_valid():
            ip = request.META['REMOTE_ADDR']
            game = get_game(site=get_current_site(request), create=True)
            game.save()  # update last_used
            password = create_form.cleaned_data['password']
            bingo_board = BingoBoard(game=game, ip=ip, password=password)
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={
                'board_id': bingo_board.board_id}))
        else:
            reclaim_form = ReclaimForm()
            return render(
                request,
                "reclaim_board.html",
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
    fields_on_board = bingo_board.get_board_fields()
    all_word_fields = bingo_board.get_all_word_fields()

    return render(request, "bingo.html", {
        "fields_on_board": fields_on_board,
        "board": bingo_board,
        "my_board": my_bingo_board,
        "all_word_fields": all_word_fields,
        })


def vote(request):
    my_bingo_board = _get_user_bingo_board(request)

    # post request: update field.vote
    if "field_id" in request.POST:
        field_id = request.POST.get("field_id", 0)
        field = get_object_or_404(BingoField, id=field_id)
        if field.board == my_bingo_board:
            vote = request.POST.get("vote", "0")
            if vote == "0":
                field.vote = None
            elif vote == "+":
                field.vote = True
            elif vote == "-":
                field.vote = False
            field.save()
            my_bingo_board.game.save()  # update last_used

    # for all ajax requests, send updated field data
    if "ajax" in request.GET:
        if "bingo_board" in request.GET:
            bingo_board = get_object_or_404(
                BingoBoard, id=request.GET.get("bingo_board", 0))
        else:
            bingo_board = my_bingo_board
        data = {
            'num_users': bingo_board.game.num_users(),
            'num_active_users': bingo_board.game.num_active_users()
        }
        for field in bingo_board.bingofield_set.all():
            if field.vote is None:
                vote = "0"
            elif field.vote:
                vote = "+"
            else:
                vote = "-"
            data[field.id] = (vote, field.num_votes())
        return HttpResponse(json.dumps(data), mimetype="application/json")
    else:
        return redirect(reverse(bingo, kwargs={"board_id": field.board.id}))


def image(request, board_id, marked=False, voted=False):
    bingo_board = get_object_or_404(
        BingoBoard, board_id=board_id,
        game__site=get_current_site(request))
    response = HttpResponse(mimetype="image/png")
    if voted:
        filename = _("board_{0}_voted.png").format(board_id)
    elif marked:
        filename = _("board_{0}_marked.png").format(board_id)
    else:
        filename = _("board_{0}.png").format(board_id)
    response['Content-Disposition'] = 'filename={0}'.format(filename)
    im = get_image(bingo_board, marked, voted)
    im.save(response, "png")
    return response
