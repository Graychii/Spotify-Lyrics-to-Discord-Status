"""
Downloads Google Fonts as TTF and registers them with Windows GDI
so tkinter can use them by name.
"""
import os
import re
import ctypes
import requests

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')

# Display name → Google Fonts family param
GOOGLE_FONTS = {
    'Courier Prime': 'Courier+Prime',
}


def _fetch_ttf_url(family_param: str) -> str | None:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    try:
        css = requests.get(
            f'https://fonts.googleapis.com/css2?family={family_param}:wght@400&display=swap',
            headers=headers, timeout=10
        ).text
        match = re.search(r"url\(([^)]+\.ttf)\)", css)
        return match.group(1) if match else None
    except Exception as e:
        print(f'Font: CSS fetch failed — {e}')
        return None


def ensure_font(name: str) -> bool:
    """
    Download (once) and register a Google Font with Windows GDI.
    Returns True if the font is ready to use in tkinter.
    """
    if name not in GOOGLE_FONTS:
        return False

    os.makedirs(_DIR, exist_ok=True)
    fpath = os.path.join(_DIR, name.replace(' ', '_') + '.ttf')

    if not os.path.exists(fpath):
        print(f'Font: downloading {name}...')
        url = _fetch_ttf_url(GOOGLE_FONTS[name])
        if not url:
            print(f'Font: could not find TTF URL for {name}')
            return False
        try:
            data = requests.get(url, timeout=10).content
            with open(fpath, 'wb') as f:
                f.write(data)
            print(f'Font: {name} saved')
        except Exception as e:
            print(f'Font: download failed — {e}')
            return False

    result = ctypes.windll.gdi32.AddFontResourceExW(os.path.abspath(fpath), 0x10, 0)
    if result == 0:
        print(f'Font: failed to register {name} with Windows GDI')
        return False

    return True
