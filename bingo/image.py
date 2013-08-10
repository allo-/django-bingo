from django.db.models import Count, Max
from django.conf import settings
from django.utils.translation import ugettext as _

from PIL import Image, ImageDraw, ImageFont, ImageDraw, ImageFont

from models import Word, BingoField


# constants
COLOR_MODE_BLANK, COLOR_MODE_MARKED, COLOR_MODE_VOTED = range(3)

# settings
H_BOX_PADDING = getattr(settings, "HORIZONTAL_PADDING", 8)
V_BOX_PADDING = getattr(settings, "VERTICAL_PADDING", 30)
H_LINE_MARGIN = getattr(settings, "HORIZONTAL_LINE_MARGIN", 0)
V_LINE_MARGIN = getattr(settings, "VERTICAL_LINE_MARGIN", 5)
BORDER = getattr(settings, "BORDER", 1)
FONTPATH = getattr(settings, "FONT_PATH", "/path/to/font.ttf")
FONTSIZE = getattr(settings, "FONT_SIZE", 16)
BINGO_DATETIME_FORMAT = getattr(
    settings, "BINGO_DATETIME_FORMAT", "%Y-%m-%d %H:%M")


class Text(object):
    def __init__(self, draw, font, input):
        self.line_widths = []
        self.line_heights = []
        self.lines = input.split("\n")
        for line in self.lines:
            line_width, line_height = draw.textsize(line, font=font)
            self.line_widths.append(line_width + H_LINE_MARGIN)
            self.line_heights.append(line_height + V_LINE_MARGIN)

    def get_total_width(self):
        return sum(self.line_widths)

    def get_total_height(self):
        return sum(self.line_heights)


def get_texts(bingo_fields, font):
    im = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    words = []
    word_widths = []
    word_heights = []
    texts = []

    for bingo_field in bingo_fields:
        text = bingo_field.word.word
        if bingo_field.is_middle():
            text += _("\n{time}\nBoard #{board_id}").format(
                time=bingo_field.board.created.strftime(BINGO_DATETIME_FORMAT),
                board_id=bingo_field.board.id)
        texts.append(Text(draw, font, text))
    return texts


def get_colors(bingo_field, vote_counts, colormode=COLOR_MODE_BLANK):
    marked_field_color = bingo_field.board.color[1:]

    # convert from #rrggbb to decimal (r, g, b)
    marked_field_color = (
        int(marked_field_color[:2], 16),
        int(marked_field_color[2:4], 16),
        int(marked_field_color[4:6], 16),
    )
    # normal fields
    neutral_field_color = (255, 255, 255)
    neutral_word_color = (0, 0, 0)
    # middle field
    middle_field_color = (90, 90, 90)
    middle_board_text_color = (255, 255, 255)
    # border 
    border_color = (0, 0, 0)

    field_color = neutral_field_color
    word_color = neutral_word_color
    if bingo_field.is_middle():
        field_color = (90, 90, 90)
        word_color = (255, 255, 255)
    elif colormode == COLOR_MODE_MARKED and bingo_field.vote:
        field_color = marked_field_color
    elif colormode == COLOR_MODE_VOTED:
        max_votes = max(vote_counts.values())
        if max_votes > 0:
            votes = vote_counts[bingo_field.word.id]
            scaling = votes / float(max_votes)
            color_0 = int(255 - scaling * (255 - marked_field_color[0]))
            color_1 = int(255 - scaling * (255 - marked_field_color[1]))
            color_2 = int(255 - scaling * (255 - marked_field_color[2]))
            field_color = (color_0, color_1, color_2)

    return field_color, word_color, border_color


def get_image(bingo_board, marked=False, voted=False):
    font = ImageFont.truetype(FONTPATH, FONTSIZE)

    all_bingo_fields = BingoField.objects.filter(board__game=bingo_board.game)
    bingo_fields = all_bingo_fields.filter(board=bingo_board).exclude(
        position=None).order_by("position")

    # image sizes
    texts = get_texts(bingo_fields, font)
    max_text_width = 0
    max_text_height = 0
    for text in texts:
        max_text_width = max(max_text_width, text.get_total_width())
        max_text_height = max(max_text_height, text.get_total_height())

    # inside the border
    inner_width = max_text_width + 2 * H_BOX_PADDING
    inner_height = max_text_height + 2 * V_BOX_PADDING

    # with border
    field_width = inner_width + 2 * BORDER
    field_height = inner_height + 2 * BORDER

    # total board width
    image_width = 5*(max_text_width + (2 * H_BOX_PADDING)) + (6 * BORDER)
    image_height = 5*(max_text_height + (2 * V_BOX_PADDING)) + (6 * BORDER)

    im = Image.new("RGB", (image_width, image_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    # get the words of the board. This does include words deactivated later,
    # and does not include words added later
    words = Word.objects.filter(bingofield__board=bingo_board)

    # count votes per word, find the maximum
    vote_counts = {}
    for word in words:
        vote_counts[word.id] = all_bingo_fields.filter(
            word=word, vote=True).count()

    # draw the board
    for bingo_field in bingo_fields:
        pos = bingo_field.position - 1
        y, x = divmod(pos, 5)
        # top left corner of the box
        box_left = x * (field_width - BORDER)
        box_top = y * (field_height - BORDER)
        # top left corner inside the box
        # inside the border, but outside of the padding
        word_left = box_left + BORDER
        word_top = box_top + BORDER

        # calculate the background and foreground color
        # for the field
        if marked:
            colormode = COLOR_MODE_MARKED
        elif voted:
            colormode = COLOR_MODE_VOTED
        else:
            colormode = COLOR_MODE_BLANK
        field_color, word_color, border_color = get_colors(
            bingo_field, vote_counts, colormode=colormode)

        # draw a border. if its more than 1px, its extended
        # by drawing smaller boxes inside
        for offset in xrange(BORDER):
            draw.rectangle((
                (box_left + offset, box_top + offset),
                (box_left + field_width - offset,
                    box_top + field_height - offset)),
                fill=field_color,
                outline=border_color
            )

        v_center = (inner_height - texts[pos].get_total_height()) / 2.0
        text = texts[pos]
        h_offset = 0
        for idx, line in enumerate(text.lines):
            h_center = (inner_width - text.line_widths[idx]) / 2.0
            draw.text(
                (word_left + h_center,
                 word_top + v_center + h_offset),
                line, font=font, fill=word_color
            )
            h_offset += text.line_heights[idx]

    return im
