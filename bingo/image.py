from PIL import Image, ImageDraw, ImageFont, ImageDraw, ImageFont
from models import Word, BingoField
from django.db.models import Count, Max
from django.conf import settings


COLOR_MODE_BLANK, COLOR_MODE_MARKED, COLOR_MODE_VOTED = range(3)


def get_word_sizes(bingo_fields, font):
    im = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    words = []
    word_widths = []
    word_heights = []
    for bingo_field in bingo_fields:
        word_width, word_height = draw.textsize(
            bingo_field.word.word, font=font)
        word_widths.append(word_width)
        word_heights.append(word_height)
    return word_widths, word_heights


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
    h_padding = getattr(settings, "HORIZONTAL_PADDING", 8)
    v_padding = getattr(settings, "VERTICAL_PADDING", 30)
    border = getattr(settings, "BORDER", 1)

    fontpath = getattr(settings, "FONT_PATH", "/path/to/font.ttf")
    fontsize = getattr(settings, "FONT_SIZE", 16)
    font = ImageFont.truetype(fontpath, fontsize)

    all_bingo_fields = BingoField.objects.filter(board__game=bingo_board.game)
    bingo_fields = all_bingo_fields.filter(board=bingo_board).exclude(
        position=None).order_by("position")

    # image sizes
    word_widths, word_heights = get_word_sizes(bingo_fields, font)
    max_word_width = max(word_widths)
    max_word_height = max(word_heights)

    # inside the border
    inner_width = max_word_width + 2 * h_padding
    inner_height = max_word_height + 2 * v_padding

    # with border
    field_width = inner_width + 2 * border
    field_height = inner_height + 2 * border

    # total board width
    image_width = 5*(max_word_width + (2 * h_padding)) + (6 * border)
    image_height = 5*(max_word_height + (2 * v_padding)) + (6 * border)

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
        box_left = x * (field_width - border)
        box_top = y * (field_height - border)
        # top left corner inside the box
        # inside the border, but outside of the padding
        word_left = box_left + border
        word_top = box_top + border

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
        for offset in xrange(border):
            draw.rectangle((
                (box_left + offset, box_top + offset),
                (box_left + field_width - offset,
                    box_top + field_height - offset)),
                fill=field_color,
                outline=border_color
            )

        h_center = (inner_width - word_widths[pos]) / 2.0
        v_center = (inner_height - word_heights[pos]) / 2.0
        draw.text(
            (word_left + h_center,
             word_top + v_center),
            bingo_field.word.word, font=font, fill=word_color
        )

    return im
