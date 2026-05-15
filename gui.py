# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
import subprocess
import ctypes
import sys
import os
from dotenv import load_dotenv, set_key

load_dotenv(override=True)

ENV_PATH = '.env'

def env_bool(key, default='true') -> bool:
    return os.getenv(key, default).lower() == 'true'

def env_int(key, default=0) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

# Get physical screen dimensions before CTk changes DPI awareness —
# must match the coordinate system display.py uses (SetProcessDpiAwareness(1))
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

# ── App setup ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

app = ctk.CTk()
app.title('Spotify Lyrics')
app.resizable(False, False)
app.configure(fg_color='#141414')

# ── Process management ─────────────────────────────────────────────────────────
_procs: list[subprocess.Popen] = []

def start_app():
    stop_app()
    if env_bool('ENABLE_OVERLAY'):
        _procs.append(subprocess.Popen([sys.executable, 'display.py', str(_bar_y)]))
    _procs.append(subprocess.Popen([sys.executable, 'main.py']))
    status_dot.configure(text_color='#1DB954')
    status_text.configure(text='running')
    start_btn.configure(state='disabled', fg_color='#1a3a26')
    stop_btn.configure(state='normal', fg_color='#c0392b', hover_color='#e74c3c')

def stop_app():
    for p in _procs:
        try: p.terminate()
        except: pass
    _procs.clear()
    status_dot.configure(text_color='#555')
    status_text.configure(text='stopped')
    start_btn.configure(state='normal', fg_color='#1DB954', hover_color='#17a349')
    stop_btn.configure(state='disabled', fg_color='#333', hover_color='#444')

def on_close():
    stop_app()
    app.destroy()

app.protocol('WM_DELETE_WINDOW', on_close)

def save(key: str, value: str):
    set_key(ENV_PATH, key, value)

# ── Layout helpers ─────────────────────────────────────────────────────────────
PAD_X = 20

def section_title(parent, text: str):
    ctk.CTkLabel(parent, text=text,
                 font=ctk.CTkFont(size=10, weight='bold'),
                 text_color='#555').pack(anchor='w', padx=PAD_X, pady=(16, 4))

def rule(parent):
    ctk.CTkFrame(parent, height=1, fg_color='#242424').pack(fill='x', padx=PAD_X)

def toggle_row(parent, label: str, env_key: str, default=True):
    row = ctk.CTkFrame(parent, fg_color='transparent', height=40)
    row.pack(fill='x', padx=PAD_X, pady=2)
    row.pack_propagate(False)
    ctk.CTkLabel(row, text=label,
                 font=ctk.CTkFont(size=13)).pack(side='left', pady=8)
    var = ctk.StringVar(value='on' if env_bool(env_key, str(default).lower()) else 'off')
    sw = ctk.CTkSwitch(row, text='', variable=var, onvalue='on', offvalue='off',
                       command=lambda: save(env_key, str(var.get() == 'on').lower()),
                       button_color='#1DB954', button_hover_color='#17a349',
                       progress_color='#1a3a26')
    sw.pack(side='right', pady=8)

def slider_row(parent, label: str, env_key: str,
               from_: int, to: int, default: int, fmt=lambda v: f'{int(v):+d}ms'):
    frame = ctk.CTkFrame(parent, fg_color='transparent')
    frame.pack(fill='x', padx=PAD_X, pady=(4, 2))

    header = ctk.CTkFrame(frame, fg_color='transparent')
    header.pack(fill='x')
    ctk.CTkLabel(header, text=label,
                 font=ctk.CTkFont(size=13)).pack(side='left')
    val_lbl = ctk.CTkLabel(header, text=fmt(env_int(env_key, default)),
                           font=ctk.CTkFont(size=12), text_color='#666')
    val_lbl.pack(side='right')

    def on_change(v):
        snapped = round(v / 50) * 50
        val_lbl.configure(text=fmt(snapped))
        save(env_key, str(int(snapped)))

    sl = ctk.CTkSlider(frame, from_=from_, to=to,
                       button_color='#1DB954', button_hover_color='#17a349',
                       progress_color='#1DB954', command=on_change)
    sl.set(env_int(env_key, default))
    sl.pack(fill='x', pady=(4, 0))

# ── Header ─────────────────────────────────────────────────────────────────────
header_frame = ctk.CTkFrame(app, fg_color='#0d0d0d', corner_radius=0)
header_frame.pack(fill='x')

title_row = ctk.CTkFrame(header_frame, fg_color='transparent')
title_row.pack(fill='x', padx=PAD_X, pady=12)

ctk.CTkLabel(title_row, text='♫  Spotify Lyrics',
             font=ctk.CTkFont(size=17, weight='bold')).pack(side='left')

status_frame = ctk.CTkFrame(title_row, fg_color='transparent')
status_frame.pack(side='right')
status_dot  = ctk.CTkLabel(status_frame, text='●', text_color='#555',
                            font=ctk.CTkFont(size=10))
status_dot.pack(side='left')
status_text = ctk.CTkLabel(status_frame, text='stopped',
                            font=ctk.CTkFont(size=11), text_color='#555')
status_text.pack(side='left', padx=(3, 0))

# Start / Stop
btn_row = ctk.CTkFrame(header_frame, fg_color='transparent')
btn_row.pack(fill='x', padx=PAD_X, pady=(0, 14))

start_btn = ctk.CTkButton(btn_row, text='▶  Start', height=34,
                          fg_color='#1DB954', hover_color='#17a349',
                          font=ctk.CTkFont(size=13, weight='bold'),
                          command=start_app)
start_btn.pack(side='left', expand=True, fill='x', padx=(0, 8))

stop_btn = ctk.CTkButton(btn_row, text='■  Stop', height=34,
                         fg_color='#333', hover_color='#444',
                         font=ctk.CTkFont(size=13, weight='bold'),
                         state='disabled', command=stop_app)
stop_btn.pack(side='left', expand=True, fill='x')

# ── Body ───────────────────────────────────────────────────────────────────────
body = ctk.CTkFrame(app, fg_color='transparent')
body.pack(fill='both', expand=True)

# Features
section_title(body, 'FEATURES')
toggle_row(body, 'Discord Status',    'ENABLE_DISCORD',  default=True)
toggle_row(body, 'Subtitle Overlay',  'ENABLE_OVERLAY',  default=True)
toggle_row(body, 'Emojis',            'ENABLE_EMOJIS',   default=True)
toggle_row(body, 'Censor Words',      'ENABLE_CENSOR',   default=False)

rule(body)

# Timing
section_title(body, 'TIMING')
slider_row(body, 'Lyric Offset',  'LYRIC_OFFSET_MS',  -1000, 1000, 0,
           fmt=lambda v: f'{int(v):+d}ms')
slider_row(body, 'Discord Lead',  'DISCORD_LEAD_MS',  0, 1000, 300,
           fmt=lambda v: f'{int(v)}ms')

rule(body)

# Overlay position
section_title(body, 'OVERLAY POSITION')

overlay_header = ctk.CTkFrame(body, fg_color='transparent')
overlay_header.pack(fill='x', padx=PAD_X, pady=(0, 4))
ctk.CTkLabel(overlay_header, text='Drag the bar to set subtitle position',
             font=ctk.CTkFont(size=11), text_color='#555').pack(side='left')

def open_position_picker():
    picker = tk.Toplevel()
    picker.overrideredirect(True)
    picker.attributes('-topmost', True)
    picker.attributes('-alpha', 0.75)
    picker.geometry(f'{SCREEN_W}x50+0+{_bar_y}')
    picker.config(bg='#1DB954')

    lbl = tk.Label(picker,
                   text='≡  Drag to position subtitles  |  Enter or Escape to confirm',
                   font=('Helvetica', 13, 'bold'),
                   fg='#0d0d0d', bg='#1DB954', cursor='fleur')
    lbl.pack(expand=True, fill='both')

    _drag_offset = [0]

    def on_pick_press(e):
        _drag_offset[0] = e.y_root - picker.winfo_y()

    def on_pick_drag(e):
        new_y = e.y_root - _drag_offset[0]
        new_y = max(0, min(SCREEN_H - 50, new_y))
        picker.geometry(f'{SCREEN_W}x50+0+{new_y}')

    def confirm(e=None):
        global _bar_y
        _bar_y = picker.winfo_y()
        save('OVERLAY_Y', str(_bar_y))
        draw_bar(_bar_y)
        picker.destroy()

    lbl.bind('<Button-1>',   on_pick_press)
    lbl.bind('<B1-Motion>',  on_pick_drag)
    picker.bind('<Return>',  confirm)
    picker.bind('<Escape>',  confirm)
    picker.focus_force()

ctk.CTkButton(overlay_header, text='Pick on Screen', width=110, height=24,
              fg_color='#1a2a1a', hover_color='#1a3a1a',
              border_color='#1DB954', border_width=1,
              font=ctk.CTkFont(size=11),
              text_color='#1DB954',
              command=open_position_picker).pack(side='right')

CANVAS_W  = 320
CANVAS_H  = int(CANVAS_W * SCREEN_H / SCREEN_W)
SCALE     = CANVAS_W / SCREEN_W
BAR_H     = max(6, int(44 * SCALE))

canvas = tk.Canvas(body, width=CANVAS_W, height=CANVAS_H,
                   bg='#111', highlightthickness=1,
                   highlightbackground='#2a2a2a', cursor='sb_v_double_arrow')
canvas.pack(padx=PAD_X, pady=(8, 16))

# Screen grid lines (subtle)
for row in range(1, 4):
    y = int(CANVAS_H * row / 4)
    canvas.create_line(0, y, CANVAS_W, y, fill='#1a1a1a', tags='grid')

_bar_y = env_int('OVERLAY_Y', SCREEN_H - 120)

def draw_bar(y_screen: int):
    canvas.delete('bar')
    y = int(max(0, min(SCREEN_H - 44, y_screen)) * SCALE)
    canvas.create_rectangle(0, y, CANVAS_W, y + BAR_H,
                             fill='#1a2a1a', outline='#1DB954', width=1, tags='bar')
    canvas.create_text(CANVAS_W // 2, y + BAR_H // 2,
                       text='── subtitles ──', fill='#1DB954',
                       font=('Helvetica', 8), tags='bar')

draw_bar(_bar_y)

def _canvas_to_screen(y_canvas: int) -> int:
    return int(max(0, min(CANVAS_H - BAR_H, y_canvas)) / SCALE)

def on_press(event):
    global _bar_y
    _bar_y = _canvas_to_screen(event.y)
    draw_bar(_bar_y)

def on_drag(event):
    global _bar_y
    _bar_y = _canvas_to_screen(event.y)
    draw_bar(_bar_y)

def on_release(event):
    global _bar_y
    _bar_y = _canvas_to_screen(event.y)
    draw_bar(_bar_y)
    save('OVERLAY_Y', str(_bar_y))

canvas.bind('<Button-1>',        on_press)
canvas.bind('<B1-Motion>',       on_drag)
canvas.bind('<ButtonRelease-1>', on_release)

# ── Fit window to content ──────────────────────────────────────────────────────
app.update_idletasks()
app.geometry(f'360x{app.winfo_reqheight()}')

app.mainloop()
