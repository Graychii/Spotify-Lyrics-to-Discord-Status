from tkinter import *
from ctypes import windll
import sys

windll.shcore.SetProcessDpiAwareness(1)

root = Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

# Y position passed directly from the GUI at launch time — always up to date
OVERLAY_Y = int(sys.argv[1]) if len(sys.argv) > 1 else screen_h - 120

root.wm_attributes('-topmost', 1)
root.overrideredirect(True)
root.geometry(f'{screen_w}x50+0+{OVERLAY_Y}')
root.config(bg='grey')
root.wm_attributes('-transparentcolor', 'grey')
root.attributes('-alpha', 0.8)

lab = Label(root, font=('Helvetica', 25), foreground='white', bg='black', borderwidth=0)
lab.pack()

root.bind('<Escape>', lambda e: root.destroy())


def read_lyrics() -> str:
    try:
        return open('lyrics.txt', encoding='utf-8').read()
    except FileNotFoundError:
        return ''


def update():
    lab['text'] = read_lyrics()
    root.after(50, update)


update()
root.mainloop()
