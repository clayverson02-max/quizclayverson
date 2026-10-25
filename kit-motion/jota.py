"""Vídeo JOTA IMPORTS: cortes no beat de funk (original), textos estilo rua, zoom punch, flash."""
import math, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from engine3d import text3d, shine, warp3d

W, H, FPS = 1080, 1920, 30
BPM = 130; BEAT = 60 / BPM; BAR = BEAT * 4
RAW = '/home/claude/clientes/oculos/raw/'
FBI = '/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf'
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
YEL = (255, 212, 0); WHITE = (255, 255, 255); BLACK = (0, 0, 0)

# (clip, início no clipe, duração em beats)
SEG = [('c1', 0.3, 8),                                     # gancho (2 compassos)
       ('c2', 18.2, 2), ('c2', 33.0, 2), ('c2', 36.6, 2), ('c2', 46.2, 2),
       ('c2', 51.0, 2), ('c2', 60.3, 2), ('c2', 64.0, 2), ('c2', 70.0, 2),   # drop (4 compassos)
       ('c1', 9.0, 4), ('c2', 0.5, 4),                     # +400 modelos
       ('c2', 83.5, 8),                                     # site
       ('c3', 2.0, 8)]                                      # fechamento
STARTS = np.concatenate([[0], np.cumsum([s[2] for s in SEG])]) * BEAT
TOTAL = STARTS[-1] + 0.6
DROP = STARTS[1]

# textos: (início, fim, linhas[(texto, cor)], y, tamanho)
TXT = [
    (0.25, DROP - 0.05, [('AS LUPA MAIS', WHITE), ('BRABA TÁ AQUI', YEL)], 330, 104),
    (DROP, DROP + BAR * 2, [('LENTE', WHITE), ('ESPELHADA', YEL)], 320, 120),
    (DROP + BAR * 2, STARTS[9], [('TODAS AS', WHITE), ('CORES', YEL)], 320, 130),
    (STARTS[9], STARTS[11], [('+ DE 400', YEL), ('MODELOS', WHITE)], 330, 130),
    (STARTS[11], STARTS[12], [('ESCOLHE', WHITE), ('NO SITE', YEL)], 1350, 120),
]

_fc = {}
def F(size, path=FBI):
    k = (size, path)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

_tc = {}
def sticker(text, size, col, rot=-4):
    k = (text, size, col, rot)
    if k in _tc: return _tc[k]
    f = F(size); w = int(f.getlength(text)) + 80; h = int(size * 1.6)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((40, size * 1.15), text, font=f, fill=(0, 0, 0, 200), anchor='ls', stroke_width=size // 7, stroke_fill=(0, 0, 0, 200))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.06)), (6, 10))
    d.text((40, size * 1.15), text, font=f, fill=col + (255,), anchor='ls', stroke_width=size // 9, stroke_fill=BLACK + (255,))
    im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    _tc[k] = im
    return im

def back(p, s=2.2):
    p = min(1, max(0, p)) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2

def put(fr, im, cx, cy, sc=1.0, a=1.0):
    if sc != 1.0: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def reader(clip, ss, dur):
    vf = ('scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,'
          'unsharp=5:5:0.9:5:5:0.0,eq=contrast=1.12:saturation=1.35:brightness=0.01,fps=30')
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(ss), '-i', RAW + clip + '.mp4', '-t', str(dur + 0.2), '-an',
                          '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    last = None
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            while True: yield last
        last = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        yield last

def end_card(fr, tl):
    # escurece e desfoca o fundo, título 3D dourado
    a = np.asarray(fr.convert('RGB')).astype(np.float32)
    k = min(1, tl / 0.4)
    bl = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((270, 480)).filter(ImageFilter.GaussianBlur(3)).resize((W, H)), np.float32)
    a = a * (1 - k) + (bl * 0.45) * k
    fr.paste(Image.fromarray(a.astype(np.uint8)).convert('RGBA'))
    p = (tl - 0.15) / 0.5
    if p > 0:
        img, m = text3d('JOTA', 260, (255, 240, 170), (220, 150, 20), (95, 55, 5))
        img = shine(img, m, min(1, (tl - 0.4) / 1.0))
        w = warp3d(img, ry=0.25 * math.sin(tl * 1.5), rx=-0.12, scale=0.3 + 0.7 * back(p))
        put(fr, w, W / 2, 640, 1.0, min(1, p * 3))
        img2, m2 = text3d('IMPORTS', 150, (255, 255, 255), (200, 205, 215), (40, 40, 48))
        w2 = warp3d(img2, ry=0.2 * math.sin(tl * 1.5 + 0.4), rx=-0.12, scale=0.3 + 0.7 * back(p - 0.15))
        put(fr, w2, W / 2, 860, 1.0, min(1, max(0, p - 0.15) * 3))
    q = (tl - 0.9) / 0.35
    if q > 0:
        put(fr, sticker('PEDE A SUA', 96, WHITE, -3), W / 2, 1120, back(q), min(1, q * 3))
        put(fr, sticker('NO DIRECT', 110, YEL, -3), W / 2, 1250, back(q - 0.15), min(1, max(0, q - 0.15) * 3))
    r = (tl - 1.6) / 0.35
    if r > 0:
        pill = Image.new('RGBA', (820, 110), (0, 0, 0, 0)); d = ImageDraw.Draw(pill)
        d.rounded_rectangle([0, 0, 819, 109], radius=55, fill=(0, 0, 0, 190), outline=YEL + (255,), width=4)
        d.text((410, 57), 'jota-imports.kyte.site', font=F(52, FB), fill=WHITE, anchor='mm')
        put(fr, pill, W / 2, 1450, min(1, back(r)), min(1, r * 3))

def render(out):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = int(TOTAL * FPS)
    si = -1; gen = None
    rng = np.random.default_rng(3)
    for fi in range(nf):
        t = fi / FPS
        k = min(len(SEG) - 1, int(np.searchsorted(STARTS, t, side='right') - 1))
        if k != si:
            si = k; c, ss, nb = SEG[k]; gen = reader(c, ss, nb * BEAT + 0.6)
        src = next(gen)
        tl = t - STARTS[k]
        # zoom punch no início de cada corte e em cada beat do drop
        bt = (t % BEAT) / BEAT if t >= DROP and k < 11 else 1.0
        zc = 1.0 + 0.14 * max(0, 1 - tl / 0.22) + (0.035 * max(0, 1 - bt * 3) if t >= DROP and k < 11 else 0)
        zc += 0.04 * tl / (SEG[k][2] * BEAT)                  # zoom lento contínuo
        im = Image.fromarray(src)
        if zc != 1.0:
            zw, zh = int(W * zc), int(H * zc)
            sx = int(math.sin(t * 37) * 10 * max(0, 1 - tl / 0.3)) if k in (1, 9, 11) else 0
            im = im.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2 + sx, (zh - H) // 2, (zw - W) // 2 + sx + W, (zh - H) // 2 + H))
        fr = im.convert('RGBA')
        if k == len(SEG) - 1:
            end_card(fr, tl)
        for (a, b, lines, y, size) in TXT:
            if a <= t < b:
                for j, (txt, col) in enumerate(lines):
                    p = (t - a - j * 0.12) / 0.28
                    if p <= 0: continue
                    out_k = max(0, (t - (b - 0.12)) / 0.12)
                    put(fr, sticker(txt, size, col, -4 + j * 2), W / 2 + (j * 30 - 15), y + j * size * 1.12, back(p) * (1 - 0.3 * out_k), min(1, p * 3) * (1 - out_k))
        arr = np.asarray(fr.convert('RGB')).astype(np.int16)
        # flash branco + separação RGB nos começos de compasso após o drop
        if t >= DROP - 0.02:
            bar_t = ((t - DROP) % BAR)
            fl = max(0, 1 - bar_t / 0.12) * (0.55 if abs(t - DROP) < 0.15 else 0.28)
            if fl > 0: arr = (arr * (1 - fl) + 255 * fl).astype(np.int16)
            if bar_t < 0.15:
                s = int(12 * (1 - bar_t / 0.15))
                arr[..., 0] = np.roll(arr[..., 0], s, 1); arr[..., 2] = np.roll(arr[..., 2], -s, 1)
        # vinheta leve
        enc.stdin.write(np.clip(arr * VIG + rng.integers(-3, 4, (1, 1, 1)), 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()

_yy, _xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.35 * np.clip(((_xx - W / 2) / (W * 0.8)) ** 2 + ((_yy - H / 2) / (H * 0.75)) ** 2, 0, 1))[..., None].astype(np.float32)

# ------------------------------------------------------------------ beat de funk original
SR = 44100
def beat(out):
    n = int(TOTAL * SR); mix = np.zeros(n, np.float32); rng = np.random.default_rng(5)
    def add(sig, at, g=1.0):
        i = int(at * SR)
        if i >= n or i < 0: return
        j = min(n, i + len(sig)); mix[i:j] += (sig[:j - i] * g).astype(np.float32)
    st = BEAT / 4
    def kick(L=0.42, f0=52, amp=1.0):
        x = np.arange(int(L * SR)) / SR
        ph = 2 * np.pi * np.cumsum(f0 + 170 * np.exp(-x * 40)) / SR
        return np.tanh(np.sin(ph) * np.exp(-x * 5.5) * 2.2) * amp
    def clap():
        x = np.arange(int(0.22 * SR)) / SR
        nz = rng.standard_normal(len(x))
        env = np.exp(-x * 26) + 0.6 * np.exp(-np.maximum(0, x - 0.012) * 30) * (x > 0.012)
        y = np.diff(np.concatenate([[0], nz])) * env
        return y * 0.55
    def tom(f=210):
        x = np.arange(int(0.18 * SR)) / SR
        ph = 2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-x * 30))) / SR
        return np.sin(ph) * np.exp(-x * 18) * 0.45
    def hat(open_=False):
        x = np.arange(int((0.16 if open_ else 0.04) * SR)) / SR
        nz = rng.standard_normal(len(x)); y = np.diff(np.concatenate([[0], np.diff(np.concatenate([[0], nz]))]))
        return y * np.exp(-x * (14 if open_ else 90)) * 0.08
    def bass808(f, L):
        x = np.arange(int(L * SR)) / SR
        return np.tanh(np.sin(2 * np.pi * f * x) * 2.0) * np.minimum(1, x / 0.01) * np.exp(-x * 1.6) * 0.5
    def stab(f, L=0.16):
        x = np.arange(int(L * SR)) / SR
        y = sum(np.sign(np.sin(2 * np.pi * f * m * x)) / m for m in (1, 1.5, 2)) * 0.12
        return y * np.exp(-x * 14)
    def whistle(at, f0=1800, f1=2600, L=0.5, g=0.12):
        x = np.arange(int(L * SR)) / SR
        f = f0 + (f1 - f0) * np.sin(np.pi * x / L) ** 2
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / L) ** 0.5 * g, at)
    KICK = [0, 3, 6, 10, 13]; CLAP = [4, 12]; TOM = [2, 7, 9, 11, 14, 15]
    notes = [43.65, 43.65, 51.91, 38.89]   # F1 F1 G#1 D#1
    nbars = int(math.ceil(TOTAL / BAR))
    for b in range(nbars):
        t0 = b * BAR
        intro = t0 < DROP - 1e-6
        for s in range(16):
            ts = t0 + s * st
            if ts >= TOTAL - 0.3: break
            if intro:
                if s in (0, 8): add(kick(0.3, 60, 0.45), ts)
                if s % 2 == 0: add(hat(), ts, 0.7)
                if s in TOM: add(tom(260), ts, 0.5)
            else:
                if s in KICK: add(kick(), ts)
                if s in CLAP: add(clap(), ts)
                if s in TOM: add(tom(200 + 40 * (s % 3)), ts)
                add(hat(s % 4 == 2), ts)
                if s in (0, 6, 10): add(bass808(notes[b % 4], st * 4), ts)
                if s in (3, 11) and b % 2 == 1: add(stab(349.2 if s == 3 else 415.3), ts)
        if not intro and b % 2 == 0: whistle(t0 + 7 * st)
    # riser no fim da introdução + impacto no drop
    L = int(BAR * 2 * SR); x = np.arange(L) / SR
    rise = (rng.standard_normal(L) * 0.08 + np.sin(2 * np.pi * np.cumsum(300 + 1500 * (x / x[-1]) ** 2) / SR) * 0.05) * (x / x[-1]) ** 2
    add(rise, 0)
    add(kick(1.2, 40, 1.2), DROP)
    mix /= max(1e-6, np.abs(mix).max()) / 0.95
    fade = int(0.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    s16 = (mix * 32767).astype(np.int16)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.stack([s16, s16], 1).tobytes())

if __name__ == '__main__':
    if sys.argv[1] == 'beat': beat(sys.argv[2])
    else: render(sys.argv[2])
