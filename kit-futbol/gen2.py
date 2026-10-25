import math, os, sys, json, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from multiprocessing import Pool
sys.path.insert(0, '/home/claude/futbol')
from gen import tts, resample, beat, whoosh, pop, ball, phone, board, ease, back, clamp, SR

W, H, FPS = 1080, 1920, 30
CL = '/home/claude/futbol/clips'
OUT = '/home/claude/futbol/out2'; os.makedirs(OUT, exist_ok=True)
FONTS = {
    'poppins': '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',
    'poppins_i': '/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf',
    'cond_i': '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf',
    'serif': '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf',
    'news': '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    'med': '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf',
}
_f = {}
def font(name, sz):
    k = (name, int(sz))
    if k not in _f: _f[k] = ImageFont.truetype(FONTS[name], int(sz))
    return _f[k]

_clips = {}
def clip_frame(name, t, size):
    d = f'{CL}/{name}'
    if name not in _clips: _clips[name] = sorted(os.listdir(d))
    fs = _clips[name]; i = int(t * 30) % len(fs)
    return Image.open(f'{d}/{fs[i]}').convert('RGB').resize(size, Image.BICUBIC)

def grade(im, sat=1.15, con=1.12, bri=1.0):
    im = ImageEnhance.Color(im).enhance(sat); im = ImageEnhance.Contrast(im).enhance(con)
    return ImageEnhance.Brightness(im).enhance(bri) if bri != 1 else im

def grad_overlay(top_a, bot_a, mid=0.5, color=(0, 0, 0)):
    y = np.linspace(0, 1, H)[:, None]
    a = np.where(y < mid, top_a * (1 - y / mid) ** 1.3, bot_a * ((y - mid) / (1 - mid)) ** 1.6)
    arr = np.zeros((H, W, 4), np.uint8); arr[..., :3] = color; arr[..., 3] = (np.repeat(a, W, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

# --------------- text ---------------
def text_block(lines, st, size, t, y, accent, anim='pop', stagger=0.07, color=None, maxw=960):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    color = color or st['text']; f = font(st['font'], size)
    # auto-shrink to fit width
    while max(f.getlength(l) for l in lines) > maxw and size > 40:
        size -= 4; f = font(st['font'], size)
    lh = int(size * st.get('lh', 1.16)); k = 0; yy = y - lh * len(lines) // 2
    for li, line in enumerate(lines):
        words = line.split(' '); sp = f.getlength(' '); ws = [f.getlength(w) for w in words]
        x = (W - (sum(ws) + sp * (len(ws) - 1))) / 2
        for wi, w in enumerate(words):
            p = (t - k * stagger) / 0.3; k += 1
            if p <= 0: x += ws[wi] + sp; continue
            a = clamp(p * 2.2); e = ease(p)
            ox = oy = 0; sc = 1
            if anim == 'pop': sc = max(back(p), 0.05); oy = (1 - e) * 40
            elif anim == 'slide': ox = (1 - e) * -120
            elif anim == 'drop': oy = (1 - back(p, 2.4)) * -90
            elif anim == 'rise': oy = (1 - e) * 70
            wy = yy + li * lh + oy; wx = x + ox; ww = ws[wi]
            clean = w.strip('¿?¡!.,:…').upper()
            fill = color
            if clean in accent:
                bp = ease((t - k * stagger - 0.1) / 0.25)
                hs = st.get('hl', 'box'); pad = int(size * 0.14)
                if hs == 'box' and bp > 0.02:
                    d.rounded_rectangle([wx - pad, wy + size * 0.1, wx - pad + (ww + 2 * pad) * bp, wy + size * 1.12], int(size * 0.14), fill=st['accent'] + (int(255 * a),))
                    if bp > 0.55: fill = st['on_accent']
                elif hs == 'under' and bp > 0.02:
                    d.rectangle([wx, wy + size * 1.02, wx + ww * bp, wy + size * 1.14], fill=st['accent'] + (int(255 * a),)); fill = st['accent']
                elif hs == 'color':
                    fill = st['accent']
                elif hs == 'tape' and bp > 0.02:
                    d.polygon([(wx - pad, wy + size * 0.18), (wx - pad + (ww + 2 * pad) * bp, wy + size * 0.08), (wx - pad + (ww + 2 * pad) * bp, wy + size * 1.1), (wx - pad, wy + size * 1.2)], fill=st['accent'] + (int(255 * a),))
                    if bp > 0.55: fill = st['on_accent']
            wim = Image.new('RGBA', (int(ww + size), int(size * 1.7)), (0, 0, 0, 0))
            ImageDraw.Draw(wim).text((size // 2, int(size * 0.08)), w, font=f, fill=fill + (int(255 * a),),
                                     stroke_width=st.get('stroke', 0), stroke_fill=st.get('stroke_col', (0, 0, 0)) + (int(255 * a),))
            if abs(sc - 1) > 0.01: wim = wim.resize((max(1, int(wim.width * sc)), max(1, int(wim.height * sc))), Image.BILINEAR)
            cx = wx + ww / 2; cy = wy + size * 0.62
            if st.get('shadow', True):
                sh = Image.new('RGBA', wim.size, (0, 0, 0, 0)); sh.putalpha(wim.getchannel('A').point(lambda v: int(v * 0.55)))
                lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (int(cx - wim.width / 2 + 3), int(cy - wim.height / 2 + 7)))
            lay.alpha_composite(wim, (int(cx - wim.width / 2), int(cy - wim.height / 2)))
            x += ws[wi] + sp
    return lay

# --------------- props (styled) ---------------
def checklist(items, st, t, y0=900, light=False):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i, it in enumerate(items):
        p = (t - 0.2 - i * 0.26) / 0.35
        if p <= 0: continue
        x = 130 + (1 - ease(p)) * -220; y = y0 + i * 145; a = int(255 * clamp(p * 2))
        bg = (255, 255, 255, int(a * (0.92 if light else 0.14)))
        d.rounded_rectangle([x, y, W - 130, y + 118], 30, fill=bg, outline=st['accent'] + (int(a * 0.8),), width=3)
        d.ellipse([x + 24, y + 24, x + 94, y + 94], fill=st['accent'] + (a,))
        d.line([x + 43, y + 60, x + 56, y + 74, x + 77, y + 45], fill=st['on_accent'] + (a,), width=9)
        d.text((x + 118, y + 59), it, font=font(st.get('body', 'poppins'), 46), fill=(st['text'] if not light else (25, 30, 40)) + (a,), anchor='lm')
    return lay

def cta(st, t, sub, y=1420):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    p = (t - 0.1) / 0.4
    if p <= 0: return lay
    s = max(back(p), 0.02) * (1 + 0.035 * math.sin(t * 7)); bw, bh = 780 * s, 168 * s; cx = W / 2
    d.rounded_rectangle([cx - bw / 2, y - bh / 2, cx + bw / 2, y + bh / 2], int(84 * s) if st.get('round', True) else 18, fill=st['accent'] + (255,))
    if p > 0.6: d.text((cx, y), st.get('cta', 'ACCEDE AHORA'), font=font(st['font'], int(62 * s)), fill=st['on_accent'] + (255,), anchor='mm')
    q = clamp((t - 0.45) / 0.4)
    d.text((W / 2, y + 150), sub, font=font('med', 40), fill=st['text'] + (int(235 * q),), anchor='mm')
    # arrow pointing
    ax = cx + bw / 2 + 30 + 18 * math.sin(t * 8)
    if p > 0.8: d.polygon([(ax, y), (ax + 50, y - 34), (ax + 50, y + 34)], fill=st['accent'] + (255,))
    return lay

def price(st, t, big, small):
    p = max(back(t / 0.5), 0.02)
    tag = Image.new('RGBA', (720, 380), (0, 0, 0, 0)); td = ImageDraw.Draw(tag)
    td.rounded_rectangle([10, 10, 710, 370], 46, fill=st['accent'] + (255,))
    td.rounded_rectangle([28, 28, 692, 352], 34, outline=st['on_accent'] + (120,), width=3)
    td.text((360, 150), big, font=font(st['font'], 130), fill=st['on_accent'] + (255,), anchor='mm')
    td.text((360, 280), small, font=font('med', 46), fill=st['on_accent'] + (255,), anchor='mm')
    return tag.resize((max(1, int(720 * p)), max(1, int(380 * p)))).rotate(-5, resample=Image.BICUBIC, expand=True)

def counter(st, t, dur):
    n = int(2000 * ease(t / max(dur * 0.7, .1)))
    lay = Image.new('RGBA', (W, 420), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((W / 2, 210), f'+{n:,}'.replace(',', '.'), font=font(st['font'], 240), fill=st['accent'] + (255,), anchor='mm',
                             stroke_width=6, stroke_fill=(0, 0, 0, 200))
    return lay

def stripes(w, h, off):
    im = Image.new('RGBA', (w, h), (255, 205, 0, 255)); d = ImageDraw.Draw(im)
    for x in range(-h * 2, w + h, 70): d.polygon([(x + off, 0), (x + off + 35, 0), (x + off + 35 - h, h), (x + off - h, h)], fill=(15, 15, 15, 255))
    return im


_coach = {}
def coach_img(h, mirror=False):
    k = (h, mirror)
    if k not in _coach:
        im = Image.open('/home/claude/futbol/avatar/coach_cut.png').convert('RGBA')
        if mirror: im = ImageOps.mirror(im)
        im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
        a = im.getchannel('A'); glow = Image.new('RGBA', im.size, (255, 255, 255, 0)); glow.putalpha(a.filter(ImageFilter.MaxFilter(9)).point(lambda v: int(v * .9)))
        out = Image.new('RGBA', (im.width + 20, im.height + 20), (0, 0, 0, 0)); out.alpha_composite(glow, (10, 10)); out.alpha_composite(im, (10, 10))
        _coach[k] = out
    return _coach[k]

def draw_coach(frame, mode, lt, amp, accent):
    # framings: close (rosto grande), mid (meio corpo), left/right (canto, espelhado), low (de baixo)
    cfg = {'close': (1750, W / 2, 2000, False), 'mid': (1250, W / 2, 1960, False), 'left': (800, 270, 1940, False), 'right': (800, W - 270, 1940, False), 'low': (1600, W / 2 + 160, 2080, False)}[mode]
    h, cx, by, mir = cfg
    p = ease(lt / 0.45); sc = 1 + 0.025 * amp + 0.01 * math.sin(lt * 2.2)
    im = coach_img(h, mir)
    if abs(sc - 1) > 0.004: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BILINEAR)
    rot = 1.5 * math.sin(lt * 3.1) * amp
    if abs(rot) > 0.2: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    x = int(cx - im.width / 2 + (1 - p) * (-300 if cx < W / 2 else 300 if cx > W / 2 else 0)); y = int(by - im.height + (1 - p) * 400)
    frame.alpha_composite(im, (x, y))

# --------------- frame ---------------
def init():
    global GRAIN
    GRAIN = [np.random.default_rng(i).normal(0, 6, (H // 2, W // 2, 1)).astype(np.float32) for i in range(6)]

def background(spec, sc, lt, t):
    st = spec['style']; mode = st['mode']; clip = sc.get('clip', spec.get('clip', 't1')); ct = sc.get('cs', 0) + lt
    z = 1.0 + 0.06 * (lt / max(sc['dur'], .1))
    if mode == 'full':
        fr = clip_frame(clip, ct, (int(W * z), int(H * z))); fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H))
        fr = grade(fr, 1.2, 1.15).convert('RGBA'); fr.alpha_composite(grad_overlay(0.85, 0.75, 0.55)); return fr
    if mode == 'split':
        base = Image.new('RGBA', (W, H), st['panel'] + (255,))
        fr = clip_frame(clip, ct, (int(W * z), int(1180 * z))).crop((0, 0, W, 1180)); fr = grade(fr, 1.25, 1.2).convert('RGBA')
        m = Image.new('L', (W, 1180), 255); ImageDraw.Draw(m).polygon([(0, 1060), (W, 1150), (W, 1180), (0, 1180)], fill=0)
        base.paste(fr, (0, 0), m)
        ImageDraw.Draw(base).polygon([(0, 1060), (W, 1150), (W, 1170), (0, 1080)], fill=st['accent'] + (255,))
        return base
    if mode == 'card':
        base = Image.new('RGBA', (W, H), st['panel'] + (255,)); d = ImageDraw.Draw(base)
        rng = np.random.default_rng(5)
        for i in range(14):
            x = rng.random() * W; y = 700 + (rng.random() * (H - 700) + t * 25 * (1 + i % 3)) % (H - 700); r = 18 + rng.random() * 40
            col = [st['accent'], (61, 160, 255), (255, 120, 170)][i % 3]
            if i % 2: d.ellipse([x - r, y - r, x + r, y + r], fill=col + (90,))
            else: d.rounded_rectangle([x - r, y - r, x + r, y + r], 10, fill=col + (70,))
        if not sc.get('nocard'):
            cw, chh = 760, 900
            fr = clip_frame(clip, ct, (cw, int(cw * 16 / 9))).crop((0, 200, cw, 200 + chh)); fr = grade(fr, 1.25, 1.1)
            card = Image.new('RGBA', (cw + 40, chh + 40), (255, 255, 255, 255)); card.paste(fr, (20, 20))
            m = Image.new('L', card.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, card.width, card.height], 40, fill=255)
            c2 = Image.new('RGBA', card.size, (0, 0, 0, 0)); c2.paste(card, (0, 0), m)
            p = back(lt / 0.5); ang = -4 + 2 * math.sin(t * 1.5)
            c2 = c2.resize((max(1, int(c2.width * p)), max(1, int(c2.height * p)))).rotate(ang, resample=Image.BICUBIC, expand=True)
            sh = Image.new('RGBA', c2.size, (0, 0, 0, 0)); sh.putalpha(c2.getchannel('A').point(lambda v: int(v * .35)))
            base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)), (int(W / 2 - c2.width / 2 + 10), int(1180 - c2.height / 2 + 24)))
            base.alpha_composite(c2, (int(W / 2 - c2.width / 2), int(1180 - c2.height / 2)))
        return base
    if mode == 'premium':
        fr = clip_frame(clip, ct, (W // 4, H // 4)).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BICUBIC)
        fr = grade(fr, 0.75, 1.05, 0.75).convert('RGBA')
        tint = Image.new('RGBA', (W, H), st['panel'] + (120,)); fr.alpha_composite(tint)
        d = ImageDraw.Draw(fr)
        for i in range(6):
            yy = (i * 380 + t * 60) % (H + 400) - 200
            d.line([0, yy, W, yy - 400], fill=st['accent'] + (28,), width=2)
        return fr
    if mode == 'warn':
        fr = clip_frame(clip, ct, (int(W * z), int(H * z))); fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H))
        if sc.get('bad'):
            g = ImageOps.grayscale(fr).convert('RGB'); fr = Image.blend(g, Image.new('RGB', (W, H), (150, 20, 20)), 0.28)
        else: fr = grade(fr, 1.25, 1.15)
        fr = fr.convert('RGBA'); fr.alpha_composite(grad_overlay(0.82, 0.7, 0.55)); return fr

def render_frame(args):
    spec, fi = args; st = spec['style']
    t = fi / FPS; scenes = spec['scenes']
    si = max(i for i, s in enumerate(scenes) if s['start'] <= t + 1e-6); sc = scenes[si]; lt = t - sc['start']
    frame = background(spec, sc, lt, t)
    if sc.get('coach'):
        env = spec.get('env'); amp = float(env[min(fi, len(env) - 1)]) if env is not None else 0.5
        draw_coach(frame, sc['coach'], lt, amp, st['accent'])
    k = sc.get('prop'); light = st['mode'] == 'card'
    if k == 'ball':
        b = ball(max(40, int(300 * back(lt / 0.6))), lt * 160); frame.alpha_composite(b, (int(W / 2 - b.width / 2), int(sc.get('py', 1380) - b.height / 2 + math.sin(lt * 5) * 16)))
    elif k == 'board':
        bd = board(lt / max(sc['dur'] * .85, .1), lt); frame.alpha_composite(bd, (int(W / 2 - bd.width / 2), sc.get('py', 1060)))
    elif k == 'phone':
        ph = phone(lt); s = .82; ph = ph.resize((int(ph.width * s), int(ph.height * s))).rotate(-4 + 3 * math.sin(lt * 1.3), resample=Image.BICUBIC, expand=True)
        frame.alpha_composite(ph, (int(W / 2 - ph.width / 2), sc.get('py', 840) + int((1 - ease(lt / .55)) * 420)))
    elif k == 'counter': frame.alpha_composite(counter(st, lt, sc['dur']), (0, sc.get('py', 1080)))
    elif k == 'check': frame.alpha_composite(checklist(sc['items'], st, lt, sc.get('py', 900), light))
    elif k == 'cta': frame.alpha_composite(cta(st, lt, sc.get('sub', ''), sc.get('py', 1420)))
    elif k == 'price':
        tg = price(st, lt, sc['big'], sc['small']); frame.alpha_composite(tg, (int(W / 2 - tg.width / 2), int(sc.get('py', 1250) - tg.height / 2)))
    if st['mode'] == 'warn' and sc.get('bad'):
        sp = stripes(W, 70, int(t * 120) % 70); frame.alpha_composite(sp, (0, 0)); frame.alpha_composite(sp, (0, H - 70))
        if sc.get('xmark'):
            q = ease((lt - 0.4) / 0.3); d = ImageDraw.Draw(frame); c = (W / 2, 1300); r = 230 * q
            if q > 0: d.line([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(255, 40, 40, 255), width=34); d.line([c[0] - r, c[1] + r, c[0] + r, c[1] - r], fill=(255, 40, 40, 255), width=34)
    frame.alpha_composite(text_block(sc['lines'], st, sc.get('size', st.get('size', 96)), lt, sc.get('y', st.get('ty', 560)), set(sc.get('accent', [])), st.get('anim', 'pop')))
    if spec.get('tag'):
        d = ImageDraw.Draw(frame); f = font('poppins', 32); tw = f.getlength(spec['tag']) + 56; ty = st.get('tagy', 250)
        d.rounded_rectangle([W / 2 - tw / 2, ty, W / 2 + tw / 2, ty + 62], 31, fill=st.get('tagbg', (0, 0, 0)) + (170,), outline=st['accent'] + (220,), width=3)
        d.text((W / 2, ty + 31), spec['tag'], font=f, fill=st['accent'] + (255,), anchor='mm')
    arr = np.asarray(frame.convert('RGB')).astype(np.float32)
    if si > 0 and lt < 0.24:
        q = lt / 0.24; tr = sc.get('tr', 'whip')
        if tr == 'whip':
            sh = int((1 - ease(q)) * 320); step = max(1, int((1 - q) * 20)); acc = np.zeros_like(arr)
            for j in range(6): acc += np.roll(arr, -sh - j * step, axis=1)
            arr = acc / 6
        elif tr == 'zoom':
            zz = 1 + (1 - ease(q)) * .3; im = Image.fromarray(arr.astype(np.uint8)); cw, ch = int(W / zz), int(H / zz)
            arr = np.asarray(im.crop(((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)).resize((W, H))).astype(np.float32)
        elif tr == 'flash': arr = arr + (1 - q) * 210
        elif tr == 'glitch' and fi % 2 == 0:
            arr[..., 0] = np.roll(arr[..., 0], 20, 1); arr[..., 2] = np.roll(arr[..., 2], -20, 1)
        elif tr == 'slideup':
            sh = int((1 - ease(q)) * H * 0.35); arr = np.roll(arr, sh, 0)
        elif tr == 'circle':
            yy, xx = np.ogrid[:H, :W]; r = ease(q) * 1300; m = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2) < r * r
            arr = np.where(m[..., None], arr, np.array(st['accent'], np.float32))
    yy, xx = np.ogrid[:H, :W]
    if not hasattr(render_frame, 'vig'):
        render_frame.vig = np.clip(1 - 0.5 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.5, 0.45, 1)[..., None].astype(np.float32)
    arr = arr * (render_frame.vig if st['mode'] != 'card' else 1) + GRAIN[fi % 6].repeat(2, 0).repeat(2, 1) * (0.6 if st['mode'] == 'card' else 1)
    arr[H - 12:H - 4, :int(W * t / spec['total'])] = st['accent']
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(f"{spec['fdir']}/{fi:05d}.jpg", quality=92)
    return fi

def build(spec):
    name = spec['name']; fdir = f'/home/claude/futbol/fr2_{name}'; os.makedirs(fdir, exist_ok=True)
    for f in os.listdir(fdir): os.remove(os.path.join(fdir, f))
    voice = []; t = 0.0
    import gen
    gen.VOICE = '/home/claude/tts/' + spec.get('voice', 'vits-piper-es_MX-claude-high')
    for i, sc in enumerate(spec['scenes']):
        sr, a = tts(sc['say'], f'/tmp/{name}_{i}.wav', spec.get('speed', 0.9)); a = resample(a, sr)
        dur = max(sc.get('min', 1.6), len(a) / SR + 0.3); sc['start'] = t; sc['dur'] = dur; voice.append((t + 0.1, a)); t += dur
    total = t + 0.4; spec['total'] = total; spec['fdir'] = fdir; n = int(total * FPS)
    vtmp = np.zeros(int(total * SR) + SR, np.float32)
    for s0, a in voice:
        s1 = int(s0 * SR); vtmp[s1:s1 + len(a)] += a
    hop = SR // FPS; e = np.array([np.sqrt(np.mean(vtmp[i * hop:(i + 1) * hop] ** 2)) for i in range(n)])
    spec['env'] = list(np.clip(e / (e.max() + 1e-6) * 1.4, 0, 1))
    with Pool(2, initializer=init) as pool: list(pool.imap_unordered(render_frame, [(spec, i) for i in range(n)], chunksize=4))
    N = int(total * SR); vo = np.zeros(N, np.float32)
    for s0, a in voice:
        s = int(s0 * SR); e = min(N, s + len(a)); vo[s:e] += a[:e - s]
    mus = beat(total, spec.get('bpm', 118), spec.get('seed', 1))[:N]
    env = np.convolve((np.abs(vo) > .02).astype(np.float32), np.ones(4410) / 4410, 'same'); duck = 1 - .65 * np.clip(env * 3, 0, 1)
    sfx = np.zeros(N, np.float32)
    for i, sc in enumerate(spec['scenes']):
        s = int(sc['start'] * SR); w = whoosh(seed=i + 3) if i else pop(); e = min(N, s + len(w)); sfx[s:e] += w[:e - s]
    outs = []
    for tag, m in {'narrada': vo + mus * .3 * duck + sfx, 'musica': mus * .55 + sfx}.items():
        m = m / (np.max(np.abs(m)) + 1e-6) * .95; wav = f'/tmp/{name}_{tag}.wav'
        with wave.open(wav, 'w') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m * 32767).astype(np.int16).tobytes())
        mp4 = f'{OUT}/{name}_{tag}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{fdir}/%05d.jpg', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-maxrate', '10M', '-bufsize', '20M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4], check=True)
        outs.append(mp4)
    return outs

if __name__ == '__main__':
    specs = json.load(open(os.environ.get('SPECS', '/home/claude/futbol/specs2.json')))
    for sp in specs: sp['style'] = {k: (tuple(v) if isinstance(v, list) else v) for k, v in sp['style'].items()}
    if sys.argv[1:2] == ['--stills']:
        init()
        for s in specs:
            t = 0
            for sc in s['scenes']: sc['start'] = t; sc['dur'] = sc.get('min', 2.5); t += sc['dur']
            s['total'] = t; s['fdir'] = '/tmp/st_' + s['name']; os.makedirs(s['fdir'], exist_ok=True)
            for sc in s['scenes']: render_frame((s, int((sc['start'] + min(1.4, sc['dur'] - .2)) * FPS)))
        sys.exit()
    only = sys.argv[1:] or [s['name'] for s in specs]
    for s in specs:
        if s['name'] in only: print(build(s), flush=True)
