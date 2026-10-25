import math, wave, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
GF = '/usr/share/fonts/truetype/google-fonts/'
FONT_B = GF + 'Poppins-Bold.ttf'
FONT_R = GF + 'Poppins-Medium.ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

NAVY = (18, 38, 63); NAVY2 = (8, 18, 32); CREAM = (246, 241, 231)
ORANGE = (242, 140, 40); RED = (229, 57, 53); WHITE = (255, 255, 255)
INK = (22, 30, 44); GRAY = (96, 106, 120); GREEN = (40, 170, 105)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def out_back(p, s=1.9):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2
def in_out(p): p = clamp(p); return 3 * p * p - 2 * p ** 3
def lerp(a, b, t): return a + (b - a) * t

_fc = {}
def font(size, bold=True):
    k = (int(size), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_B if bold else FONT_R, int(size))
    return _fc[k]

_wc = {}
def word_img(text, size, color, bold=True):
    key = (text, int(size), color, bold)
    if key in _wc: return _wc[key]
    f = font(size, bold)
    padx = int(size * 0.3)
    w = int(f.getlength(text)) + padx * 2
    h = int(size * 1.9)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((padx, int(size * 1.25)), text, font=f, fill=color + (255,), anchor='ls')
    _wc[key] = im
    return im

_ec = {}
def emoji(ch, size):
    key = (ch, int(size))
    if key in _ec: return _ec[key]
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    r = size / max(im.size)
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    _ec[key] = im
    return im

def put(canvas, im, cx, cy, scale=1.0, alpha=1.0, rot=0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)

# ---------------- backgrounds ----------------
def _grad(top, bot):
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        arr[:, :, i] = np.linspace(top[i], bot[i], H)[:, None]
    return Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')

def _grid(color, alpha):
    g = Image.new('RGBA', (W + 120, H + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for x in range(0, W + 120, 60): d.line([(x, 0), (x, H + 120)], fill=color + (alpha,), width=1)
    for y in range(0, H + 120, 60): d.line([(0, y), (W + 120, y)], fill=color + (alpha,), width=1)
    return g

def _glow(radius, color, alpha):
    s = radius * 2
    yy, xx = np.mgrid[0:s, 0:s]
    r = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = (np.clip(1 - r, 0, 1) ** 2 * alpha).astype(np.uint8)
    arr = np.zeros((s, s, 4), np.uint8); arr[..., 0] = color[0]; arr[..., 1] = color[1]; arr[..., 2] = color[2]; arr[..., 3] = a
    return Image.fromarray(arr, 'RGBA')

BG = {
    'dark': (_grad((22, 46, 76), NAVY2), _grid((255, 255, 255), 14), _glow(520, ORANGE, 70)),
    'cream': (_grad((250, 246, 238), (236, 228, 212)), _grid((18, 38, 63), 14), _glow(520, ORANGE, 60)),
    'orange': (_grad((251, 166, 70), (226, 104, 14)), _grid((18, 38, 63), 20), _glow(560, (255, 230, 170), 90)),
}

def background(mode, t):
    base, grid, glow = BG[mode]
    c = base.copy()
    ox = int(-((t * 16) % 60)); oy = int(-((t * 22) % 60))
    c.paste(grid, (ox, oy), grid)
    gx = W * 0.5 + math.sin(t * 0.8) * 320; gy = H * 0.30 + math.cos(t * 0.6) * 260
    c.paste(glow, (int(gx - glow.width / 2), int(gy - glow.height / 2)), glow)
    gx2 = W * 0.5 + math.cos(t * 0.7) * 300; gy2 = H * 0.78 + math.sin(t * 0.5) * 220
    c.paste(glow, (int(gx2 - glow.width / 2), int(gy2 - glow.height / 2)), glow)
    return c

# ---------------- animated text ----------------
class Block:
    def __init__(self, lines, cy, t0, color, size, off, ev, stagger=0.13, maxw=930, gap=1.12,
                 hl_fill=None, hl_text=None):
        self.tokens = []
        self.hl_fill = hl_fill or ORANGE
        self.hl_text = hl_text or NAVY
        norm = []
        for ln in lines:
            nl = []
            for tk in ln:
                if isinstance(tk, str): tk = (tk, {})
                text, o = tk
                nl.append(dict(text=text, color=o.get('color', color), size=o.get('size', size), fx=o.get('fx')))
            norm.append(nl)
        def line_w(nl, f):
            return sum(font(t['size'] * f).getlength(t['text']) + (44 * f if t['fx'] == 'hl' else 0) for t in nl) + \
                   sum(0.24 * t['size'] * f for t in nl[:-1])
        f = 1.0
        mw = max(line_w(nl, 1.0) for nl in norm)
        if mw > maxw: f = maxw / mw
        heights = [max(t['size'] for t in nl) * f * gap for nl in norm]
        y = cy - sum(heights) / 2
        idx = 0
        for nl, lh in zip(norm, heights):
            x = W / 2 - line_w(nl, f) / 2
            for t in nl:
                s = int(t['size'] * f)
                w = font(s).getlength(t['text'])
                start = t0 + idx * stagger
                if t['fx'] == 'hl': x += 22 * f
                self.tokens.append(dict(t, size=s, w=w, x=x + w / 2, y=y + lh / 2, start=start))
                ev.append(('pop', off + start))
                x += w + 0.24 * s; idx += 1
                if t['fx'] == 'hl': x += 22 * f
            y += lh

    def draw(self, c, tl):
        d = ImageDraw.Draw(c)
        for tk in self.tokens:
            p = (tl - tk['start']) / 0.28
            if p <= 0: continue
            s = 0.5 + 0.5 * out_back(p); a = clamp(p * 4)
            cx = tk['x']; cy = tk['y'] + (1 - out_cubic(p)) * 45
            col = tk['color']
            if tk['fx'] == 'shake' and p > 1:
                cx += math.sin(tl * 52) * 6; cy += math.cos(tl * 61) * 5
            if tk['fx'] == 'hl':
                hp = out_cubic((tl - tk['start'] - 0.1) / 0.35)
                hw = (tk['w'] + 40) * hp; hh = tk['size'] * 1.22
                x0 = cx - tk['w'] / 2 - 20
                if hw > 2:
                    d.rounded_rectangle([x0, cy - hh / 2, x0 + hw, cy + hh / 2], radius=int(hh * 0.22), fill=self.hl_fill + (255,))
                col = self.hl_text
            put(c, word_img(tk['text'], tk['size'], col), cx, cy, scale=s, alpha=a)

# ---------------- icons / widgets ----------------
def phone_img():
    S = 2; w, h = 380 * S, 680 * S
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w, h], radius=64 * S, fill=(10, 12, 18, 255), outline=(90, 104, 130, 255), width=4 * S)
    m = 16 * S
    d.rounded_rectangle([m, m, w - m, h - m], radius=50 * S, fill=(250, 248, 243, 255))
    d.rounded_rectangle([w // 2 - 50 * S, m + 8 * S, w // 2 + 50 * S, m + 30 * S], radius=11 * S, fill=(10, 12, 18, 255))
    x0, y0, x1, y1 = m + 24 * S, 90 * S, w - m - 24 * S, 330 * S
    d.rounded_rectangle([x0, y0, x1, y1], radius=26 * S, fill=(246, 170, 80, 255))
    e = emoji('\U0001F6CD', 150 * S)
    im.paste(e, (int((x0 + x1) / 2 - e.width / 2), int((y0 + y1) / 2 - e.height / 2)), e)
    d.rounded_rectangle([x0, 358 * S, x0 + 210 * S, 384 * S], radius=12 * S, fill=(40, 52, 72, 255))
    d.rounded_rectangle([x0, 404 * S, x1, 424 * S], radius=10 * S, fill=(206, 210, 218, 255))
    d.rounded_rectangle([x0, 440 * S, x1 - 70 * S, 460 * S], radius=10 * S, fill=(206, 210, 218, 255))
    d.rounded_rectangle([x0, 520 * S, x1, 590 * S], radius=35 * S, fill=NAVY + (255,))
    d.text(((x0 + x1) / 2, 555 * S), 'COMPRAR', font=font(28 * S), fill=(255, 255, 255, 255), anchor='mm')
    return im.resize((380, 680), Image.LANCZOS)

_PH = None
def phone():
    global _PH
    if _PH is None: _PH = phone_img()
    return _PH

def check_circle(size, fill=GREEN):
    S = 3; s = size * S
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=fill + (255,))
    pts = [(s * 0.26, s * 0.52), (s * 0.43, s * 0.69), (s * 0.75, s * 0.33)]
    d.line(pts, fill=(255, 255, 255, 255), width=int(s * 0.11), joint='curve')
    return im.resize((size, size), Image.LANCZOS)

def circle_num(size, n, fill=NAVY):
    S = 3; s = size * S
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, s - 1, s - 1], fill=fill + (255,))
    d.text((s / 2, s * 0.53), str(n), font=font(int(s * 0.5)), fill=(255, 255, 255, 255), anchor='mm')
    return im.resize((size, size), Image.LANCZOS)

_sh = {}
def card_shadow(w, h):
    k = (w, h)
    if k not in _sh:
        im = Image.new('RGBA', (w + 120, h + 120), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([60, 72, 60 + w, 72 + h], radius=36, fill=(10, 20, 40, 90))
        _sh[k] = im.filter(ImageFilter.GaussianBlur(22))
    return _sh[k]

def card_img(w, h, num, title, sub, hot=False):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=36, fill=(255, 255, 255, 255),
                        outline=(ORANGE + (255,)) if hot else (222, 214, 198, 255), width=6 if hot else 3)
    c = circle_num(110, num, ORANGE if hot else NAVY)
    im.paste(c, (36, (h - 110) // 2), c)
    d.text((176, 104), title, font=font(56), fill=NAVY + (255,), anchor='ls')
    d.text((176, 170), sub, font=font(35, False), fill=GRAY + (255,), anchor='ls')
    return im

def draw_card(c, tl, start, y, num, title, sub, hot=False):
    p = (tl - start) / 0.5
    if p <= 0: return
    w, h = 900, 230
    x = lerp(W * 1.2, W / 2, out_back(p, 1.5)); a = clamp(p * 3)
    put(c, card_shadow(w, h), x, y + 8, alpha=a)
    put(c, card_img(w, h, num, title, sub, hot), x, y, alpha=a)

def arrow_down(c, tl, start, y):
    p = clamp((tl - start) / 0.3)
    if p <= 0: return
    d = ImageDraw.Draw(c)
    yy = y + (1 - p) * -14
    d.polygon([(W / 2 - 34, yy - 14), (W / 2 + 34, yy - 14), (W / 2, yy + 20)], fill=ORANGE + (int(255 * p),))

# ---------------- timeline ----------------
class Scene:
    def __init__(self, start, end, mode, fn):
        self.start, self.end, self.mode, self.fn = start, end, mode, fn

def wipe(c, t, T, dur=0.5):
    h = dur / 2; d = ImageDraw.Draw(c)
    if T - h <= t < T:
        y = int(H * in_out((t - (T - h)) / h))
        d.rectangle([0, 0, W, y], fill=ORANGE + (255,)); d.rectangle([0, y - 16, W, y], fill=CREAM + (255,))
    elif T <= t < T + h:
        y = int(H * in_out((t - T) / h))
        d.rectangle([0, y, W, H], fill=ORANGE + (255,)); d.rectangle([0, y, W, y + 16], fill=CREAM + (255,))

# ---------------- audio (sintetizado, sem direitos autorais) ----------------
SR = 44100
def synth(total, ev, bounds):
    n = int(total * SR); t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    out += (0.040 * (np.sin(2 * np.pi * 110 * t) + 0.6 * np.sin(2 * np.pi * 164.81 * t) + 0.4 * np.sin(2 * np.pi * 220 * t)) *
            (0.75 + 0.25 * np.sin(2 * np.pi * 0.2 * t))).astype(np.float32)
    def add(sig, at):
        i = int(at * SR)
        if i >= n or i < 0: return
        j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    notes = [220, 261.63, 329.63, 392.0, 440.0, 392.0, 329.63, 261.63]
    k = 0; tt = 0.5
    while tt < total - 0.6:
        L = int(0.22 * SR); x = np.arange(L) / SR; fr = notes[k % 8]
        add((0.045 * np.sin(2 * np.pi * fr * x) * np.exp(-x * 9)).astype(np.float32), tt)
        tt += 0.25; k += 1
    tt = 0.5
    while tt < total - 0.6:
        L = int(0.32 * SR); x = np.arange(L) / SR
        ph = 2 * np.pi * np.cumsum(48 + 120 * np.exp(-x * 35)) / SR
        add((0.20 * np.sin(ph) * np.exp(-x * 8)).astype(np.float32), tt)
        tt += 0.5
    rng = np.random.default_rng(3)
    tt = 0.75
    while tt < total - 0.6:
        L = int(0.05 * SR); x = np.arange(L) / SR
        add((0.025 * rng.standard_normal(L) * np.exp(-x * 70)).astype(np.float32), tt)
        tt += 0.5
    for kind, at in ev:
        if kind == 'pop':
            L = int(0.10 * SR); x = np.arange(L) / SR
            ph = 2 * np.pi * np.cumsum(520 + 4000 * x) / SR
            add((0.085 * np.sin(ph) * np.exp(-x * 38)).astype(np.float32), at)
        elif kind == 'thunk':
            L = int(0.25 * SR); x = np.arange(L) / SR
            add((0.22 * np.sin(2 * np.pi * 85 * x) * np.exp(-x * 14)).astype(np.float32), at)
        elif kind == 'chime':
            L = int(0.9 * SR); x = np.arange(L) / SR
            add((0.10 * (np.sin(2 * np.pi * 880 * x) + 0.7 * np.sin(2 * np.pi * 1318.5 * x)) * np.exp(-x * 4)).astype(np.float32), at)
    for T in bounds:
        L = int(0.5 * SR); x = np.arange(L) / SR
        noise = rng.standard_normal(L).astype(np.float32)
        # whoosh: ruído com filtro passa-baixa que abre (vetorizado via média móvel crescente)
        k = np.linspace(40, 3, L)
        cs = np.cumsum(noise)
        y = np.empty(L, np.float32)
        for i in range(L):
            kk = int(k[i]); j = max(0, i - kk)
            y[i] = (cs[i] - cs[j]) / max(1, i - j)
        env = np.sin(np.pi * x / 0.5) ** 1.5
        add((3.0 * y * env).astype(np.float32), T - 0.25)
    pk = np.max(np.abs(out)) or 1.0
    out = out / pk * 0.85
    fade = int(0.6 * SR); out[-fade:] *= np.linspace(1, 0, fade).astype(np.float32)
    return out

def write_wav(path, sig):
    s = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    st = np.stack([s, s], axis=1).reshape(-1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())

# ---------------- render ----------------
_noise = [np.random.default_rng(i).integers(-2, 3, (H, W, 1), dtype=np.int16) for i in range(6)]

def frame(scenes, bounds, t, fi):
    sc = scenes[-1]
    for s in scenes:
        if s.start <= t < s.end: sc = s; break
    c = background(sc.mode, t)
    sc.fn(c, t - sc.start)
    for T in bounds: wipe(c, t, T)
    arr = np.asarray(c.convert('RGB'), dtype=np.int16) + _noise[fi % 6]
    return np.clip(arr, 0, 255).astype(np.uint8)

def render(scenes, bounds, ev, total, out_path, stills=None, still_dir=None):
    if stills:
        os.makedirs(still_dir, exist_ok=True)
        for tt in stills:
            Image.fromarray(frame(scenes, bounds, tt, int(tt * FPS))).save(f'{still_dir}/{os.path.basename(out_path)}_{tt:05.2f}.png')
        return
    wav = out_path + '.wav'
    write_wav(wav, synth(total, ev, bounds))
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(total * FPS)
    for fi in range(nf):
        p.stdin.write(frame(scenes, bounds, fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
