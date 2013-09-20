from django.contrib import admin
from django.db import models
from django import forms

from models import *


def bingoboard_user(bingo_board):
    return bingo_board.user if bingo_board.user else bingo_board.ip


def bingoboard_name(bingo_board):
    return u'BingoBoard #{0} (site {1})'.format(
        bingo_board.board_id, bingo_board.game.site)


def word_sites(word):
    """
        @returns: the sites, where a Word instance is active,
        truncated, so at most 5 sites are displayed
    """
    sites = map(lambda site: site.domain, word.site.all()[:5])
    return ", ".join(sites if len(sites) <= 5 else sites+["[...]"])


def game_id(game):
    """
        just the game.id prefixed by "Game #"
        so its easier to click in the admin interface
    """
    return u"Game #{0}".format(game.game_id)


def bingoboard_game_id(bingo_board):
    """
        @returns the game.id for the game of a BingoBoard instance
    """
    return game_id(bingo_board.game)


bingoboard_name.short_description = "Bingo"
bingoboard_game_id.short_description = "Game"
word_sites.short_description = "Sites"


class WordAdmin(admin.ModelAdmin):
    list_filter = ("site", "site", "is_middle")
    list_display = ("word", word_sites, "is_middle")
    search_fields = ("word", )

    class Meta:
        ordering = ("word",)

    def has_delete_permission(self, request, obj=None):
        return False


class BingoFieldInline(admin.TabularInline):
    model = BingoField
    list_display = ("word", "position", "vote")
    readonly_fields = ("word", "position", "vote")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class BingoBoardAdmin(admin.ModelAdmin):
    list_display = (bingoboard_name, "color", "created",
                    bingoboard_game_id, bingoboard_user)
    list_editable = ("color",)
    list_filter = ("game__site",)
    # cannot be changed, because its hashed.
    # if we would hash it on save, it will be hashed again on each save
    readonly_fields = ("created", "last_used", "game", "password")
    inlines = (BingoFieldInline,)


class BingoFieldAdmin(admin.ModelAdmin):
    list_display = ("word", "board", "position")
    readonly_fields = ("board", "word", "position", "vote")


class GameAdmin(admin.ModelAdmin):
    list_display = (game_id, "site", "created", "last_used")
    list_filter = ("site",)
    readonly_fields = ("created", "last_used")


admin.site.register(Word, WordAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(BingoBoard, BingoBoardAdmin)
admin.site.register(BingoField, BingoFieldAdmin)
