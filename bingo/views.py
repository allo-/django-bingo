from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse

from models import Word, Game, BingoBoard, get_game
from forms import CreateForm, ReclaimForm


def _create_new_bingo(game, ip):
    bingo_board = BingoBoard(game=game, ip=ip)
    bingo_board.save()
    bingo_id = bingo_board.id
    return bingo_id


def _get_bingo_board(request):
    bingo_board = None
    game = get_game(create=False)
    session_bingo_id = request.session.get('bingo_id', None)
    ip = request.META['REMOTE_ADDR']

    # try the bingo_id in the session
    if not session_bingo_id is None:
        try:
            bingo_board = BingoBoard.objects.get(id=session_bingo_id,
                                                 game=game)
            bingo_board.ip = ip
            bingo_board.save()
        except BingoBoard.DoesNotExist, e:
            pass

    # no bingo_id in the session, try the ip
    if bingo_board is None:
        try:
            bingo_board = BingoBoard.objects.get(game=game, ip=ip)
            request.session['bingo_id'] = bingo_board.id
        except BingoBoard.DoesNotExist, e:
            pass

    return bingo_board


def main(request, reclaim_form=None, create_form=None):
    game = get_game(create=False)
    bingo_board = _get_bingo_board(request)
    create_form = CreateForm()
    reclaim_form = ReclaimForm(game=game)
    return render(request, "main.html", {
        'my_board': bingo_board,
        'create_form': create_form,
        'reclaim_form': reclaim_form,
        'boards': BingoBoard.objects.filter(game=game),
        'games': Game.objects.order_by("-created"),
        })


def reclaim_board(request):
    ip = request.META['REMOTE_ADDR']
    game = get_game(create=False)
    if request.POST:
        reclaim_form = ReclaimForm(request.POST, game=game)
        if reclaim_form.is_valid():
            bingo_board = reclaim_form.cleaned_data['bingo_board']
            request.session['bingo_id'] = bingo_board.id
            bingo_board.ip = ip
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={'bingo_id':
                                                   bingo_board.id}))
    else:
        reclaim_form = ReclaimForm(game=game)
    create_form = CreateForm()
    return render(request,
                  "reclaim_board.html", {
                      'reclaim_form': reclaim_form,
                      'create_form': create_form,
                  })


def create_board(request):
    bingo_board = _get_bingo_board(request)
    if bingo_board:
        return redirect(reverse(bingo, kwargs={'bingo_id': bingo_board.id}))
    elif request.POST:
        create_form = CreateForm(request.POST)
        if create_form.is_valid():
            ip = request.META['REMOTE_ADDR']
            game = get_game(create=True)
            password = create_form.cleaned_data['password']
            bingo_board = BingoBoard(game=game, ip=ip, password=password)
            bingo_board.save()
            return redirect(reverse(bingo, kwargs={'bingo_id': bingo_board.id}))
    else:
        return redirect(reverse(main))


def bingo(request, bingo_id=None):
    game = get_game(create=False)
    bingo_board = get_object_or_404(BingoBoard, id=bingo_id)
    all_fields = bingo_board.bingofield_set.all()
    fields = bingo_board.bingofield_set.all().exclude(position=None) \
        .order_by("position")[:25]
    return render(request, "bingo.html", {
        "fields": fields,
        "all_fields":
        all_fields.order_by("word__word"),
        "all_middle_words":
        Word.objects.filter(is_active=True, is_middle=True).order_by("word"),
        })
