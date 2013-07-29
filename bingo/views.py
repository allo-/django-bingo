from django.shortcuts import render

from models import Word


def bingo(request):
    words = Word.objects.order_by("?")[:25]
    fields = [{"word": word} for word in words]
    fields[12] = {"is_middle": True}
    return render(request, "bingo.html", {"fields": fields})
