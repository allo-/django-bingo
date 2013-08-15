from django.contrib import admin
from django.db import models
from django import forms

from models import *


class WordAdmin(admin.ModelAdmin):
    list_filter = ("site", "is_middle", "is_active")
    list_display = ("word", "is_active", "is_middle")
    list_editable = ("is_active",)
    search_fields = ("word", )

    class Meta:
        ordering = ("word",)

    def has_delete_permission(self, request, obj=None):
        return False


def bingo_board_user(bingo_board):
    return bingo_board.user if bingo_board.user else bingo_board.ip


def bingo_board_name(bingo_board):
    return u'BingoBoard #{0} (site {1})'.format(
        bingo_board.board_id, bingo_board.game.site)


bingo_board_name.short_description = "Bingo"


class BingoFieldInline(admin.TabularInline):
    model = BingoField
    list_display = ("word", "position", "vote")
    readonly_fields = ("word", "position", "vote")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class BingoBoardAdmin(admin.ModelAdmin):
    list_display = (bingo_board_name, "color", "created",
                    "game", bingo_board_user)
    list_editable = ("color",)
    # cannot be changed, because its hashed.
    # if we would hash it on save, it will be hashed again on each save
    readonly_fields = ("created", "last_used", "game", "password")
    inlines = (BingoFieldInline,)


class BingoFieldAdmin(admin.ModelAdmin):
    list_display = ("word", "board", "position")
    list_filter = ("word", "position")
    readonly_fields = ("board", "word", "position", "vote")


def game_name(game):
    return u"Game #{0} (site {1})".format(game.game_id, game.site)


class GameAdmin(admin.ModelAdmin):
    list_display = (game_name, "site", "created", "last_used")
    list_filter = ("site",)
    readonly_fields = ("created", "last_used")


admin.site.register(Word, WordAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(BingoBoard, BingoBoardAdmin)
admin.site.register(BingoField, BingoFieldAdmin)
