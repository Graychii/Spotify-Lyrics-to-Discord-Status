from tkinter import *
from tkinter import font as tkfont
from ctypes import windll
import sys
import colorsys
import os

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

windll.shcore.SetProcessDpiAwareness(1)

try:
    from fonts import ensure_font, GOOGLE_FONTS
except ImportError:
    GOOGLE_FONTS = {}
    def ensure_font(_): return False

RAINBOW    = os.getenv('ENABLE_RAINBOW',         'false').lower() == 'true'
TEXT_COLOR = os.getenv('SUBTITLE_COLOR',         '#ffffff')
BG_COLOR   = os.getenv('SUBTITLE_BG',            '#000000')
BG_TRANSP  = os.getenv('SUBTITLE_BG_TRANSPARENT','false').lower() == 'true'
ALPHA      = float(os.getenv('SUBTITLE_ALPHA',   '0.8'))
SIZE       = int(os.getenv('SUBTITLE_SIZE',      '25'))
EFFECT     = os.getenv('SUBTITLE_EFFECT',        'none').lower()
FONT_NAME  = os.getenv('SUBTITLE_FONT',          'Helvetica')

if FONT_NAME in GOOGLE_FONTS:
    ensure_font(FONT_NAME)

TRANSP_KEY = 'grey'
OVERLAY_H  = max(54, SIZE * 2 + 20)
FONT_T     = (FONT_NAME, SIZE, 'bold')
PAD_X      = 28

root = Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

OVERLAY_Y = int(sys.argv[1]) if len(sys.argv) > 1 else screen_h - 120
OVERLAY_Y = max(0, min(screen_h - OVERLAY_H, OVERLAY_Y))

root.wm_attributes('-topmost', 1)
root.overrideredirect(True)
root.geometry(f'10x{OVERLAY_H}+0+{OVERLAY_Y}')
root.config(bg=TRANSP_KEY)
root.wm_attributes('-transparentcolor', TRANSP_KEY)
root.attributes('-alpha', ALPHA)

effective_bg = TRANSP_KEY if BG_TRANSP else BG_COLOR

cv = Canvas(root, bg=effective_bg, highlightthickness=0, bd=0)
cv.pack(fill='both', expand=True)

root.bind('<Escape>', lambda e: root.destroy())

_tk_font = tkfont.Font(family=FONT_NAME, size=SIZE, weight='bold')
_hue     = 0.0
_last    = None


def read_lyrics() -> str:
    try:
        return open('lyrics.txt', encoding='utf-8').read()
    except FileNotFoundError:
        return ''


def _hex(h) -> str:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, 1.0, 1.0)
    return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'


def resize(text: str):
    if text:
        w = _tk_font.measure(text) + PAD_X * 2
    else:
        w = 10
    x = (screen_w - w) // 2
    root.geometry(f'{w}x{OVERLAY_H}+{x}+{OVERLAY_Y}')


def _draw_chars(text: str, cx: int, cy: int, color_or_none, hue_off: float):
    total = _tk_font.measure(text)
    x = cx - total // 2
    n = max(len(text), 1)
    for i, ch in enumerate(text):
        col = color_or_none if color_or_none else _hex((hue_off + i / n) % 1.0)
        cw  = _tk_font.measure(ch)
        cv.create_text(x + cw // 2, cy, text=ch, font=FONT_T, fill=col, anchor='center')
        x += cw


def draw(text: str):
    cv.delete('all')
    if not text:
        return

    w  = cv.winfo_width()
    h  = cv.winfo_height()
    cx = w // 2
    cy = h // 2

    # Effect pass (drawn behind main text)
    if EFFECT == 'shadow':
        if RAINBOW:
            _draw_chars(text, cx + 2, cy + 2, '#1a1a1a', _hue)
        else:
            cv.create_text(cx + 2, cy + 2, text=text, font=FONT_T,
                           fill='#1a1a1a', anchor='center')
    elif EFFECT == 'outline':
        offsets = [(-2,-2),(0,-2),(2,-2),(-2,0),(2,0),(-2,2),(0,2),(2,2)]
        for dx, dy in offsets:
            if RAINBOW:
                _draw_chars(text, cx + dx, cy + dy, '#000000', _hue)
            else:
                cv.create_text(cx + dx, cy + dy, text=text, font=FONT_T,
                               fill='#000000', anchor='center')

    # Main text pass
    if RAINBOW:
        _draw_chars(text, cx, cy, None, _hue)
    else:
        cv.create_text(cx, cy, text=text, font=FONT_T, fill=TEXT_COLOR, anchor='center')


def update():
    global _hue, _last
    text = read_lyrics()
    if RAINBOW:
        _hue = (_hue + 0.015) % 1.0
    if text != _last:
        resize(text)
        _last = text
    draw(text)
    root.after(50, update)


update()
root.mainloop()
