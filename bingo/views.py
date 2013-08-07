from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import get_current_site

from models import Word, Game, BingoBoard, get_game
from forms import CreateForm, ReclaimForm


def _get_bingo_board(request):
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
            bingo_board.save()
        except BingoBoard.DoesNotExist, e:
            pass

    # no board_id in the session, try the ip
    if bingo_board is None:
        try:
            bingo_board = BingoBoard.objects.get(game=game, ip=ip)
            request.session['board_id'] = bingo_board.board_id
        except BingoBoard.DoesNotExist, e:
            pass

    return bingo_board


def main(request, reclaim_form=None, create_form=None):
    game = get_game(site=get_current_site(request), create=False)
    bingo_board = _get_bingo_board(request)
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
    bingo_board = _get_bingo_board(request)
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
    bingo_board = _get_bingo_board(request)
    if bingo_board:
        return redirect(reverse(bingo, kwargs={
            'board_id': bingo_board.board_id}))
    elif request.POST:
        create_form = CreateForm(request.POST)
        if create_form.is_valid():
            ip = request.META['REMOTE_ADDR']
            game = get_game(site=get_current_site(request), create=True)
            password = create_form.cleaned_data['password']
            bingo_board = BingoBoard(game=game, ip=ip, password=password)
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={
                'board_id': bingo_board.board_id}))
        else:
            reclaim_form = ReclaimForm()
            return render(request,
                          "reclaim_board.html", {
                              'reclaim_form': reclaim_form,
                              'create_form': create_form,
                          })
    else:
        return redirect(reverse(main))


def bingo(request, board_id=None):
    game = get_game(site=get_current_site(request), create=False)
    bingo_board = get_object_or_404(BingoBoard, board_id=board_id, game=game)
    all_fields = bingo_board.bingofield_set.all()
    fields = bingo_board.bingofield_set.all().exclude(position=None) \
        .order_by("position")[:25]
    return render(request, "bingo.html", {
        "fields": fields,
        "board": bingo_board,
        "all_fields":
        all_fields.order_by("word__word"),
        "all_middle_words":
        Word.objects.filter(
            site=game.site, is_active=True, is_middle=True).order_by("word"),
        })
