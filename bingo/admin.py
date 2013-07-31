from django.contrib import admin

from models import *


class WordAdmin(admin.ModelAdmin):
    list_filter = ("is_middle", "is_active")
    list_display = ("word", "is_active", "is_middle")

    class Meta:
        ordering = ("word",)

    def has_delete_permission(self, request, obj=None):
        return True


def bingo_user(bingo_board):
    return bingo_board.user if bingo_board.user else bingo_board.ip


def bingo_id(bingo_board):
    return u'BingoBoard #{0}'.format(bingo_board.id)


class BingoBoardAdmin(admin.ModelAdmin):
    list_display = (bingo_id, "color", "game", bingo_user)
    list_editable = ("color",)


class BingoFieldAdmin(admin.ModelAdmin):
    list_display = ("word", "board", "position")
    list_filter = ("word", "position")

admin.site.register(Word, WordAdmin)
admin.site.register(Game)
admin.site.register(BingoBoard, BingoBoardAdmin)
admin.site.register(BingoField, BingoFieldAdmin)
