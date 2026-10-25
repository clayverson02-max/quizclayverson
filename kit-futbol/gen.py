import math, os, sys, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

W, H, FPS = 1080, 1920, 30
GF = '/usr/share/fonts/truetype/google-fonts/'
FB, FM = GF + 'Poppins-Bold.ttf', GF + 'Poppins-Medium.ttf'
LIME = (198, 255, 61); WHITE = (255, 255, 255); DARK = (6, 18, 12); PITCH = (14, 60, 34)
GOLD = (255, 200, 60); RED = (255, 77, 77); INK = (10, 14, 12)
TTS = '/home/claude/tts'; ENG = TTS + '/sherpa-onnx-v1.12.15-linux-x64-shared'
VOICE = TTS + '/vits-piper-es_MX-claude-high'
OUT = '/home/claude/futbol/out'; os.makedirs(OUT, exist_ok=True)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def ease(p): p = clamp(p); return 1 - (1 - p) ** 3
def back(p, s=1.8): p = clamp(p) - 1; return 1 + (s + 1) * p ** 3 + s * p ** 2
def inout(p): p = clamp(p); return p * p * (3 - 2 * p)

_f = {}
def font(sz, b=True):
    k = (int(sz), b)
    if k not in _f: _f[k] = ImageFont.truetype(FB if b else FM, int(sz))
    return _f[k]

# ---------- audio ----------
def tts(text, path, speed=0.92):
    onnx = [f for f in os.listdir(VOICE) if f.endswith('.onnx')][0]
    subprocess.run([ENG + '/bin/sherpa-onnx-offline-tts', f'--vits-model={VOICE}/{onnx}', f'--vits-tokens={VOICE}/tokens.txt',
                    f'--vits-data-dir={VOICE}/espeak-ng-data', f'--vits-length-scale={speed}', f'--output-filename={path}', text],
                   env={**os.environ, 'LD_LIBRARY_PATH': ENG + '/lib'}, capture_output=True)
    with wave.open(path) as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return sr, a

def resample(a, sr, to=44100):
    n = int(len(a) * to / sr); return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)

SR = 44100
def beat(total, bpm=118, seed=1):
    rng = np.random.default_rng(seed); n = int(total * SR); out = np.zeros(n, np.float32); spb = 60 / bpm
    t = np.arange(int(0.45 * SR)) / SR
    kick = np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 32)) * t) * np.exp(-t * 7)
    th = np.arange(int(0.06 * SR)) / SR; hat = rng.standard_normal(len(th)) * np.exp(-th * 70) * 0.25
    ts = np.arange(int(0.2 * SR)) / SR; snare = (rng.standard_normal(len(ts)) * 0.5 + np.sin(2 * np.pi * 190 * ts)) * np.exp(-ts * 22) * 0.55
    notes = [41, 41, 44, 39]  # midi bass
    i = 0
    while i * spb / 2 < total:
        s = int(i * spb / 2 * SR); beatn = i // 2
        def add(x, at, g):
            e = min(n, at + len(x));
            if at < n: out[at:e] += x[:e - at] * g
        if i % 2 == 0: add(kick, s, 0.9)
        if i % 4 == 2: add(snare, s, 0.6)
        add(hat, s + int(spb / 4 * SR), 0.5)
        if i % 2 == 0:
            f = 440 * 2 ** ((notes[(beatn // 4) % 4] - 69) / 12); bt = np.arange(int(spb * SR)) / SR
            bass = np.tanh(2.2 * np.sin(2 * np.pi * f * bt)) * np.exp(-bt * 3) * 0.28
            add(bass, s, 1)
        i += 1
    # pad
    tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * tt) for m in (65, 68, 72)) * 0.03 * (0.6 + 0.4 * np.sin(tt * 0.8))
    return out + pad.astype(np.float32)

def whoosh(dur=0.35, seed=3):
    rng = np.random.default_rng(seed); n = int(dur * SR); x = rng.standard_normal(n)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    # crude band sweep via moving average of varying length
    y = np.convolve(x, np.ones(6) / 6, 'same') * env * 0.35
    return y.astype(np.float32)

def pop(seed=4):
    t = np.arange(int(0.08 * SR)) / SR
    return (np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 60) * 0.25).astype(np.float32)

# ---------- visuals ----------
def bg_base():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    g = np.clip(1 - (x ** 2 * 0.5 + (y - 0.35) ** 2 * 1.2), 0, 1)
    img = np.zeros((H, W, 3), np.float32)
    for c in range(3): img[..., c] = DARK[c] + (PITCH[c] - DARK[c]) * g
    # stripes
    stripes = ((np.floor((y * 9) % 2) * 0.06) * g)[..., None]
    img = img * (1 + stripes)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
BG = None
VIG = None
GRAIN = None
def init():
    global BG, VIG, GRAIN
    BG = bg_base()
    y = np.linspace(-1, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    v = np.clip(1 - 0.55 * (x ** 2 + y ** 2) ** 1.4, 0.35, 1)
    VIG = v[..., None].astype(np.float32)
    GRAIN = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2, 1)).astype(np.float32) for i in range(6)]

def pitch_lines(d, t, a):
    col = (255, 255, 255, int(40 * a))
    cx, cy = W // 2, int(H * 0.52 + 30 * math.sin(t * 0.6))
    r = 300 + 10 * math.sin(t)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=5)
    d.line([0, cy, W, cy], fill=col, width=5)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=col)
    d.rectangle([W * 0.18, H - 260, W * 0.82, H + 40], outline=col, width=5)
    d.rectangle([W * 0.18, -40, W * 0.82, 260], outline=col, width=5)

def particles(d, t):
    rng = np.random.default_rng(7)
    for i in range(26):
        x = (rng.random() * W + t * (20 + 40 * rng.random())) % W
        y = (rng.random() * H - t * (30 + 60 * rng.random())) % H
        s = 3 + rng.random() * 5
        d.ellipse([x - s, y - s, x + s, y + s], fill=(198, 255, 61, int(50 + 60 * rng.random())))

def text_block(lines, size, t0, t, accent, y, align_c=True, stagger=0.07, color=WHITE):
    """lines: list of strings; words in accent set get lime box. returns RGBA layer"""
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = font(size); lh = int(size * 1.18); k = 0
    total_h = lh * len(lines); yy = y - total_h // 2
    for li, line in enumerate(lines):
        words = line.split(' '); sp = f.getlength(' ')
        widths = [f.getlength(w) for w in words]; lw = sum(widths) + sp * (len(words) - 1)
        x = (W - lw) / 2
        for wi, w in enumerate(words):
            p = (t - t0 - k * stagger) / 0.32; k += 1
            if p <= 0: x += widths[wi] + sp; continue
            s = back(p); a = clamp(p * 2)
            ww = widths[wi]; wy = yy + li * lh + (1 - ease(p)) * 60
            clean = w.strip('¿?¡!.,:')
            if clean.upper() in accent:
                bp = ease((t - t0 - k * stagger - 0.15) / 0.25)
                pad = 14
                if bp > 0.02: d.rounded_rectangle([x - pad, wy + size * 0.12, x - pad + (ww + 2 * pad) * bp, wy + size * 1.12], 12, fill=LIME + (int(255 * a),))
                fill = INK if bp > 0.6 else color
            else:
                fill = color
            # draw scaled word via temp image
            wim = Image.new('RGBA', (int(ww + 40), int(size * 1.6)), (0, 0, 0, 0))
            ImageDraw.Draw(wim).text((20, int(size * 0.1)), w, font=f, fill=fill + (int(255 * a),))
            if abs(s - 1) > 0.01:
                wim = wim.resize((max(1, int(wim.width * s)), max(1, int(wim.height * s))), Image.BILINEAR)
            cx = x + ww / 2; cy = wy + size * 0.6
            sh = Image.new('RGBA', wim.size, (0, 0, 0, 0)); sh.putalpha(wim.getchannel('A').point(lambda v: int(v * 0.5)))
            lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (int(cx - wim.width / 2 + 4), int(cy - wim.height / 2 + 8)))
            lay.alpha_composite(wim, (int(cx - wim.width / 2), int(cy - wim.height / 2)))
            x += ww + sp
    return lay

# ---------- props ----------
def ball(size, rot):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([2, 2, size - 2, size - 2], fill=(250, 250, 250, 255), outline=(30, 30, 30, 255), width=max(2, size // 40))
    c = size / 2; r = size * 0.18
    for i in range(5):
        ang = rot + i * 72
        px = c + math.cos(math.radians(ang)) * size * 0.32; py = c + math.sin(math.radians(ang)) * size * 0.32
        pts = [(px + math.cos(math.radians(ang + j * 72)) * r * 0.55, py + math.sin(math.radians(ang + j * 72)) * r * 0.55) for j in range(5)]
        d.polygon(pts, fill=(25, 25, 25, 255))
    pts = [(c + math.cos(math.radians(rot + 36 + j * 72)) * r, c + math.sin(math.radians(rot + 36 + j * 72)) * r) for j in range(5)]
    d.polygon(pts, fill=(25, 25, 25, 255))
    hl = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).ellipse([size * 0.2, size * 0.12, size * 0.55, size * 0.4], fill=(255, 255, 255, 90))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(size / 20)))
    return im

def board(p, t):
    """tactical board drawing X/O and arrows progressively"""
    bw, bh = 820, 560
    im = Image.new('RGBA', (bw + 40, bh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, bw + 20, bh + 20], 36, fill=(12, 70, 40, 245), outline=(255, 255, 255, 200), width=6)
    d.line([bw / 2 + 20, 30, bw / 2 + 20, bh + 10], fill=(255, 255, 255, 90), width=4)
    d.ellipse([bw / 2 - 70, bh / 2 - 50, bw / 2 + 110, bh / 2 + 90], outline=(255, 255, 255, 90), width=4)
    marks = [('O', 170, 160), ('O', 170, 420), ('O', 330, 290), ('X', 560, 180), ('X', 600, 400), ('X', 700, 290)]
    for i, (m, x, y) in enumerate(marks):
        q = clamp(p * 8 - i)
        if q <= 0: continue
        s = 34 * back(q)
        if m == 'O': d.ellipse([x - s, y - s, x + s, y + s], outline=LIME + (255,), width=9)
        else:
            d.line([x - s, y - s, x + s, y + s], fill=RED + (255,), width=10); d.line([x - s, y + s, x + s, y - s], fill=RED + (255,), width=10)
    arrows = [((210, 160), (520, 160)), ((370, 290), (640, 300)), ((210, 420), (540, 420))]
    for i, (a, b) in enumerate(arrows):
        q = clamp(p * 4 - 1.6 - i * 0.5)
        if q <= 0: continue
        ex = a[0] + (b[0] - a[0]) * ease(q); ey = a[1] + (b[1] - a[1]) * ease(q)
        n = 14
        for k in range(n):
            if k % 2: continue
            x0 = a[0] + (ex - a[0]) * k / n; y0 = a[1] + (ey - a[1]) * k / n
            x1 = a[0] + (ex - a[0]) * (k + 1) / n; y1 = a[1] + (ey - a[1]) * (k + 1) / n
            d.line([x0, y0, x1, y1], fill=(255, 255, 255, 240), width=7)
        if q > 0.95:
            ang = math.atan2(ey - a[1], ex - a[0])
            d.polygon([(ex, ey), (ex - 30 * math.cos(ang - 0.45), ey - 30 * math.sin(ang - 0.45)), (ex - 30 * math.cos(ang + 0.45), ey - 30 * math.sin(ang + 0.45))], fill=(255, 255, 255, 240))
    return im

CARDS = ['PORTERO', 'DEFENSA', 'MEDIOCAMPO', 'DELANTERO', 'REGATE', 'TIRO', 'PASE', 'AGILIDAD', 'SUB-8', 'SUB-12', 'SUB-15', 'ADULTO', 'TÁCTICA', 'FÍSICO', 'TÉCNICA', 'CIRCUITOS']
CC = [(198, 255, 61), (61, 214, 255), (255, 200, 60), (255, 110, 110)]
def phone(t):
    pw, ph = 560, 1080
    im = Image.new('RGBA', (pw + 60, ph + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, pw + 40, ph + 50], 70, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d.rounded_rectangle([30, 30, pw + 30, ph + 30], 70, fill=(20, 20, 24, 255))
    scr = Image.new('RGBA', (pw - 36, ph - 36), (240, 244, 240, 255)); sd = ImageDraw.Draw(scr)
    sd.rectangle([0, 0, pw, 150], fill=(12, 60, 34, 255))
    sd.text((30, 50), '+2.000 EJERCICIOS', font=font(38), fill=LIME + (255,))
    off = -(t * 140) % 330
    for i in range(14):
        col = i % 2; row = i // 2
        x = 24 + col * 252; y = 175 + row * 165 - off
        if y > ph or y < 60: continue
        c = CC[i % 4]
        sd.rounded_rectangle([x, y, x + 232, y + 145], 22, fill=(255, 255, 255, 255), outline=(220, 225, 220, 255), width=2)
        sd.rounded_rectangle([x + 14, y + 14, x + 70, y + 70], 14, fill=c + (255,))
        sd.text((x + 14, y + 86), CARDS[i % len(CARDS)], font=font(26), fill=(20, 30, 24, 255))
        sd.rounded_rectangle([x + 14, y + 122, x + 150, y + 130], 4, fill=(210, 215, 210, 255))
    sd.rectangle([0, 0, pw, 150], fill=(12, 60, 34, 255)); sd.text((30, 50), '+2.000 EJERCICIOS', font=font(38), fill=LIME + (255,))
    mask = Image.new('L', scr.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, scr.width, scr.height], 54, fill=255)
    im.paste(scr, (48, 48), mask)
    d.rounded_rectangle([pw / 2 - 40, 52, pw / 2 + 100, 82], 15, fill=(20, 20, 24, 255))
    return im

def counter(p):
    n = int(2000 * ease(p))
    lay = Image.new('RGBA', (W, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = f'+{n:,}'.replace(',', '.')
    d.text((W / 2, 200), s, font=font(230), fill=LIME + (255,), anchor='mm')
    return lay

def checklist(items, t0, t):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    y0 = 760
    for i, it in enumerate(items):
        p = (t - t0 - i * 0.28) / 0.35
        if p <= 0: continue
        x = 140 + (1 - ease(p)) * -200; y = y0 + i * 150; a = int(255 * clamp(p * 2))
        d.rounded_rectangle([x, y, W - 140, y + 120], 30, fill=(255, 255, 255, int(a * 0.1)), outline=(255, 255, 255, int(a * 0.35)), width=3)
        d.ellipse([x + 26, y + 26, x + 94, y + 94], fill=LIME + (a,))
        d.line([x + 44, y + 60, x + 56, y + 74, x + 78, y + 46], fill=INK + (a,), width=9)
        d.text((x + 120, y + 60), it, font=font(46), fill=WHITE + (a,), anchor='lm')
    return lay

def cta(t0, t, line2):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    p = (t - t0) / 0.4
    if p <= 0: return lay
    s = max(back(p), 0.02); pulse = 1 + 0.035 * math.sin((t - t0) * 7)
    bw, bh = 760 * s * pulse, 170 * s * pulse; cx, cy = W / 2, 1330
    d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 85, fill=LIME + (255,))
    if p > 0.6: d.text((cx, cy), 'ACCEDE AHORA', font=font(int(64 * s)), fill=INK + (255,), anchor='mm')
    q = clamp((t - t0 - 0.35) / 0.4)
    d.text((W / 2, 1490), line2, font=font(40, False), fill=(255, 255, 255, int(230 * q)), anchor='mm')
    # shine sweep
    sx = cx - bw / 2 + ((t - t0) * 600 % (bw + 400)) - 200
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(sx, cy - bh / 2), (sx + 60, cy - bh / 2), (sx + 10, cy + bh / 2), (sx - 50, cy + bh / 2)], fill=(255, 255, 255, 90))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 85, fill=255)
    lay.paste(sh, (0, 0), Image.composite(sh, Image.new('RGBA', (W, H)), m).getchannel('A'))
    return lay

# ---------- scene rendering ----------
def render_frame(args):
    spec, fi = args
    t = fi / FPS
    scenes = spec['scenes']
    si = max(i for i, s in enumerate(scenes) if s['start'] <= t + 1e-6)
    sc = scenes[si]; lt = t - sc['start']; dur = sc['dur']
    frame = BG.copy().convert('RGBA')
    d = ImageDraw.Draw(frame, 'RGBA')
    pitch_lines(d, t, 1.0); particles(d, t)
    # props
    k = sc.get('prop')
    if k == 'ball':
        p = ease(lt / 0.6); bs = int(330 * back(lt / 0.6)) or 1
        b = ball(max(bs, 40), lt * 140)
        frame.alpha_composite(b, (int(W / 2 - b.width / 2), int(1330 - b.height / 2 + math.sin(lt * 5) * 18)))
    elif k == 'board':
        bd = board(lt / max(dur * 0.85, 0.1), lt); s = 0.92 + 0.08 * ease(lt / 0.5)
        bd = bd.resize((int(bd.width * s), int(bd.height * s)))
        frame.alpha_composite(bd, (int(W / 2 - bd.width / 2), 1010 + int((1 - ease(lt / 0.5)) * 120)))
    elif k == 'phone':
        ph = phone(lt); s = 0.86 * (0.9 + 0.1 * ease(lt / 0.5))
        ph = ph.resize((int(ph.width * s), int(ph.height * s))).rotate(-4 + 3 * math.sin(lt * 1.3), resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(ph, (int(W / 2 - ph.width / 2), 820 + int((1 - ease(lt / 0.55)) * 400)))
    elif k == 'counter':
        frame.alpha_composite(counter(lt / max(dur * 0.7, 0.1)), (0, 1060))
    elif k == 'check':
        frame.alpha_composite(checklist(sc['items'], 0.2, lt))
    elif k == 'cta':
        frame.alpha_composite(cta(0.15, lt, sc.get('sub', '')))
    elif k == 'price':
        p = max(back(lt / 0.5), 0.02); dd = ImageDraw.Draw(frame)
        tag = Image.new('RGBA', (700, 360), (0, 0, 0, 0)); td = ImageDraw.Draw(tag)
        td.rounded_rectangle([10, 10, 690, 350], 50, fill=(255, 255, 255, 255))
        td.text((350, 120), sc['big'], font=font(120), fill=INK + (255,), anchor='mm')
        td.text((350, 260), sc['small'], font=font(46, False), fill=(60, 70, 60, 255), anchor='mm')
        tag = tag.resize((max(1, int(700 * p)), max(1, int(360 * p)))).rotate(-5, resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(tag, (int(W / 2 - tag.width / 2), int(1250 - tag.height / 2)))
    # text
    frame.alpha_composite(text_block(sc['lines'], sc.get('size', 96), 0.05, lt, set(sc.get('accent', [])), sc.get('y', 620)))
    # tag top
    if spec.get('tag'):
        d2 = ImageDraw.Draw(frame); tw = font(34).getlength(spec['tag']) + 50
        d2.rounded_rectangle([W / 2 - tw / 2, 270, W / 2 + tw / 2, 330], 30, fill=(0, 0, 0, 120), outline=LIME + (200,), width=3)
        d2.text((W / 2, 300), spec['tag'], font=font(34), fill=LIME + (255,), anchor='mm')
    # transition in (first 0.22 s of each scene except first)
    arr = np.asarray(frame.convert('RGB')).astype(np.float32)
    if si > 0 and lt < 0.22:
        q = lt / 0.22; tr = sc.get('tr', 'whip')
        if tr == 'whip':
            shift = int((1 - ease(q)) * 300)
            nb = 6; step = max(1, int((1 - q) * 18))
            acc = np.zeros_like(arr)
            for j in range(nb): acc += np.roll(arr, -shift - j * step, axis=1)
            arr = acc / nb
        elif tr == 'zoom':
            z = 1 + (1 - ease(q)) * 0.25; im = Image.fromarray(arr.astype(np.uint8)); cw, ch = int(W / z), int(H / z)
            im = im.crop(((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)).resize((W, H)); arr = np.asarray(im).astype(np.float32)
        elif tr == 'flash':
            arr = arr + (1 - q) * 200
        elif tr == 'glitch':
            if fi % 2 == 0:
                arr[..., 0] = np.roll(arr[..., 0], 18, axis=1); arr[..., 2] = np.roll(arr[..., 2], -18, axis=1)
    # punch zoom on beat-ish micro movement
    arr = arr * VIG
    g = GRAIN[fi % 6].repeat(2, 0).repeat(2, 1)
    arr = arr + g
    # progress bar
    prog = t / spec['total']
    arr[H - 14:H - 6, :int(W * prog)] = LIME
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f"{spec['fdir']}/{fi:05d}.jpg", quality=92)
    return fi

def build(spec):
    name = spec['name']; fdir = f'/home/claude/futbol/frames_{name}'; os.makedirs(fdir, exist_ok=True)
    for f in os.listdir(fdir): os.remove(os.path.join(fdir, f))
    # narration per scene
    voice = []; t = 0.0
    for i, sc in enumerate(spec['scenes']):
        sr, a = tts(sc['say'], f'/tmp/{name}_{i}.wav', spec.get('speed', 0.9))
        a = resample(a, sr); dur = max(sc.get('min', 1.6), len(a) / SR + 0.35)
        sc['start'] = t; sc['dur'] = dur; voice.append((t + 0.12, a)); t += dur
    total = t + 0.4; spec['total'] = total; spec['fdir'] = fdir
    n = int(total * FPS)
    with Pool(2, initializer=init) as pool:
        list(pool.imap_unordered(render_frame, [(spec, i) for i in range(n)], chunksize=4))
    # audio mix
    N = int(total * SR); vo = np.zeros(N, np.float32)
    for st, a in voice:
        s = int(st * SR); e = min(N, s + len(a)); vo[s:e] += a[:e - s] * 1.0
    mus = beat(total, spec.get('bpm', 118), spec.get('seed', 1))[:N]
    env = np.convolve((np.abs(vo) > 0.02).astype(np.float32), np.ones(4410) / 4410, 'same')
    duck = 1 - 0.65 * np.clip(env * 3, 0, 1)
    sfx = np.zeros(N, np.float32)
    for i, sc in enumerate(spec['scenes']):
        s = int(sc['start'] * SR)
        w = whoosh() if i > 0 else pop()
        e = min(N, s + len(w)); sfx[s:e] += w[:e - s]
    mixes = {'narrada': vo * 1.0 + mus * 0.30 * duck + sfx, 'musica': mus * 0.55 + sfx}
    outs = []
    for tag, m in mixes.items():
        m = m / (np.max(np.abs(m)) + 1e-6) * 0.95
        wav = f'/tmp/{name}_{tag}.wav'
        with wave.open(wav, 'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m * 32767).astype(np.int16).tobytes())
        mp4 = f'{OUT}/{name}_{tag}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{fdir}/%05d.jpg', '-i', wav,
                        '-af', 'loudnorm=I=-14:TP=-1', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4], check=True)
        outs.append(mp4)
    return outs

if __name__ == '__main__':
    specs = json.load(open('/home/claude/futbol/specs.json'))
    only = sys.argv[1:] or [s['name'] for s in specs]
    for s in specs:
        if s['name'] in only: print(build(s), flush=True)
