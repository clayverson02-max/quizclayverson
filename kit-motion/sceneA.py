import sys, math, os, subprocess, wave
import numpy as np
from engine3d import *

# ---------------------------------------------------------------- narração e tempos
PH = [
    ("Todos hablan de vender por internet...", 0.00, 1.85),
    ("Pero casi nadie te enseña a no caer en estafas.", 2.42, 5.79),
    ("Después de los cuarenta y cinco,", 6.26, 7.75),
    ("ese celular que tienes en la mano puede convertirse en tu propio negocio.", 7.96, 11.97),
    ("Son solo tres pasos:", 12.36, 13.87),
    ("elegir el producto correcto,", 14.21, 15.72),
    ("armar tu vitrina desde el celular,", 16.07, 18.15),
    ("y salir a buscar tu primera venta por Instagram y Marketplace.", 18.25, 21.95),
    ("Sin computadora.", 22.23, 23.29),
    ("Con poca inversión.", 23.61, 24.69),
    ("Paso a paso.", 25.12, 26.10),
    ("Descubre tu perfil de vendedora en dos minutos:", 26.63, 29.34),
    ("toca en Más información y haz el quiz gratis.", 29.68, 32.60),
]
CAP_TXT = {"cuarenta": "45", "y": None}
TOTAL = 34.0
VO = '/home/claude/audio/vo_A.mp3'

# palavras com tempo (para legenda)
WORDS = []
for txt, s, e in PH:
    ws = txt.replace('cuarenta y cinco', '45').split()
    wt = np.array([len(w) + 2 for w in ws], float); cum = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
    for i, w in enumerate(ws):
        WORDS.append((w, s + (e - s) * cum[i], s + (e - s) * cum[i + 1]))
GROUPS = []
cur = []
for w in WORDS:
    cur.append(w)
    if len(cur) >= 3 or sum(len(x[0]) for x in cur) > 16 or w[0][-1] in '.,:':
        GROUPS.append(cur); cur = []
if cur: GROUPS.append(cur)

# cenas (início de cada uma)
SC = [0.0, 2.25, 6.10, 12.20, 22.08, 26.48, TOTAL]

# ---------------------------------------------------------------- malhas
PHONE = extrude(outline_roundrect(2.3, 4.6, 0.38), 0.3, bevel=0.07, mats=('black', 'screen', 'black'), front_tex=True)
COIN = extrude(outline_circle(0.5, 56), 0.14, bevel=0.05, mats=('gold', 'gold', 'gold'))
SHIELD = extrude(outline_shield(1.9, 2.3), 0.42, bevel=0.12, mats=('red', 'red', 'red'), front_tex=True)
CARD = extrude(outline_roundrect(3.5, 1.3, 0.24), 0.18, bevel=0.06, mats=('cream', 'cream', 'cream'), front_tex=True)
BADGE = extrude(outline_circle(0.6, 64), 0.22, bevel=0.07, mats=('green', 'green', 'green'), front_tex=True)
BUTTON = extrude(outline_roundrect(3.9, 1.0, 0.5), 0.32, bevel=0.1, mats=('orange', 'orange', 'orange'), front_tex=True)
BAG = extrude(outline_roundrect(0.9, 1.0, 0.12), 0.5, bevel=0.06, mats=('orange', 'orange', 'orange'))

# ---------------------------------------------------------------- texturas
def tex_exclaim():
    im = Image.new('RGBA', (600, 726), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([255, 120, 345, 470], radius=40, fill=(255, 255, 255, 255))
    d.ellipse([250, 520, 350, 620], fill=(255, 255, 255, 255))
    return im
EXCL = tex_exclaim()

def tex_check():
    S = 600; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([(150, 320), (255, 425), (455, 205)], fill=(255, 255, 255, 255), width=70, joint='curve')
    return im
CHECK = tex_check()

def tex_button():
    im = Image.new('RGBA', (1560, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lab = 'HACER EL QUIZ GRATIS'; f = font(118); tw = f.getlength(lab)
    x = 780 - (tw + 150) / 2
    d.text((x, 200), lab, font=f, fill=(255, 255, 255, 255), anchor='lm')
    ax = x + tw + 40
    d.line([(ax, 200), (ax + 90, 200)], fill=(255, 255, 255, 255), width=26)
    d.polygon([(ax + 60, 150), (ax + 115, 200), (ax + 60, 250)], fill=(255, 255, 255, 255))
    return im
BTN = tex_button()

_cards = {}
def tex_card(n, title, sub, active):
    k = (n, active)
    if k in _cards: return _cards[k]
    im = Image.new('RGBA', (1400, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = ORANGE if active else NAVY
    d.ellipse([60, 120, 340, 400], fill=col + (255,))
    d.text((200, 262), str(n), font=font(170), fill=(255, 255, 255, 255), anchor='mm')
    d.text((395, 235), title, font=font(110 if len(title) < 10 else 92), fill=NAVY + (255,), anchor='ls')
    d.text((395, 350), sub, font=font(70), fill=(70, 82, 102, 255), anchor='ls')
    _cards[k] = im
    return im
CARDS = [(1, 'PRODUCTO', 'Elegir qué vender'), (2, 'VITRINA', 'Tu tienda en el celular'), (3, 'PRIMERA VENTA', 'Instagram + Marketplace')]

def screen_store(t):
    im = Image.new('RGBA', (460, 920), (246, 241, 231, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 460, 120], fill=NAVY + (255,))
    d.ellipse([28, 40, 88, 100], fill=ORANGE + (255,))
    d.text((110, 72), 'Mi Tienda', font=font(40), fill=(255, 255, 255, 255), anchor='lm')
    d.rounded_rectangle([30, 150, 430, 520], radius=34, fill=(252, 196, 120, 255))
    e = emoji('\U0001F6CD', 210); im.alpha_composite(e, (230 - e.width // 2, 335 - e.height // 2))
    d.rounded_rectangle([30, 550, 330, 590], radius=20, fill=(40, 52, 72, 255))
    d.rounded_rectangle([30, 610, 430, 636], radius=13, fill=(206, 210, 218, 255))
    d.rounded_rectangle([30, 650, 360, 676], radius=13, fill=(206, 210, 218, 255))
    pulse = 1 + 0.03 * math.sin(t * 6)
    bw = 400 * pulse
    d.rounded_rectangle([230 - bw / 2, 720, 230 + bw / 2, 800], radius=40, fill=ORANGE + (255,))
    d.text((230, 760), 'COMPRAR', font=font(40), fill=(255, 255, 255, 255), anchor='mm')
    d.rounded_rectangle([30, 820, 430, 890], radius=35, outline=(37, 211, 102, 255), width=5)
    d.text((230, 855), 'Pedir por WhatsApp', font=font(30), fill=(30, 150, 80, 255), anchor='mm')
    return im

def screen_quiz(t):
    im = Image.new('RGBA', (460, 920), (246, 241, 231, 255)); d = ImageDraw.Draw(im)
    d.text((230, 90), 'Pregunta 3 de 8', font=font(30, False), fill=(90, 100, 118, 255), anchor='mm')
    d.rounded_rectangle([40, 120, 420, 136], radius=8, fill=(220, 214, 200, 255))
    pr = 0.25 + 0.12 * clamp(t / 2.5)
    d.rounded_rectangle([40, 120, 40 + 380 * pr, 136], radius=8, fill=ORANGE + (255,))
    d.text((230, 210), '¿Qué te describe', font=font(40), fill=NAVY + (255,), anchor='mm')
    d.text((230, 262), 'mejor?', font=font(40), fill=NAVY + (255,), anchor='mm')
    opts = ['Me gusta conversar', 'Me gusta organizar', 'Me gusta crear', 'Números y estrategia']
    sel = 2 if t > 1.2 else -1
    for i, o in enumerate(opts):
        y = 330 + i * 130
        on = i == sel
        d.rounded_rectangle([40, y, 420, y + 104], radius=26, fill=(ORANGE if on else (255, 255, 255)) + (255,),
                            outline=(ORANGE if on else (225, 218, 204)) + (255,), width=4)
        d.text((230, y + 52), o, font=font(30), fill=((255, 255, 255) if on else NAVY) + (255,), anchor='mm')
    return im

# ---------------------------------------------------------------- textos 2D
_t2 = {}
def text2d(s, size, col=(255, 255, 255), stroke=0, scol=(0, 0, 0)):
    k = (s, size, col, stroke)
    if k not in _t2:
        f = font(size); w = int(f.getlength(s)) + 40 + stroke * 2; h = int(size * 1.5) + stroke * 2
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((20 + stroke, int(size * 1.12) + stroke), s, font=f, fill=(0, 0, 0, 150), anchor='ls')
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.08))
        im.alpha_composite(sh, (0, int(size * 0.05)))
        ImageDraw.Draw(im).text((20 + stroke, int(size * 1.12) + stroke), s, font=f, fill=col + (255,), anchor='ls',
                                stroke_width=stroke, stroke_fill=scol + (255,))
        _t2[k] = im
    return _t2[k]

def pop_text(fr, s, size, cx, cy, tl, start, col=(255, 255, 255), dur=0.35):
    p = (tl - start) / dur
    if p <= 0: return
    im = text2d(s, size, col)
    sc = 0.6 + 0.4 * back(p)
    if sc != 1: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    put(fr, im, cx, cy + (1 - ease_out(p)) * 40, clamp(p * 3))

def head3d(fr, s, size, cx, cy, tl, start, top, bot, side, sway=0.22, dur=0.6):
    p = (tl - start) / dur
    if p <= 0: return
    img, mask = text3d(s, size, top, bot, side)
    img = shine(img, mask, clamp((tl - start - 0.3) / 1.1))
    sc = 0.3 + 0.7 * elastic(p)
    ry = (1 - ease_out(p)) * 1.2 + sway * math.sin(tl * 1.3)
    rx = -0.12 + 0.05 * math.sin(tl * 0.9)
    w = warp3d(img, ry=ry, rx=rx, scale=sc)
    put(fr, w, cx, cy, clamp(p * 2.5))

# ---------------------------------------------------------------- legendas
def captions(fr, t):
    g = None
    for gr in GROUPS:
        if gr[0][1] - 0.05 <= t <= gr[-1][2] + 0.25: g = gr
    if g is None: return
    size = 64
    items = []
    for w, s, e in g:
        active = s <= t < e + 0.05
        items.append((w.upper(), active, s))
    f = font(size)
    widths = [f.getlength(w) for w, _, _ in items]; gap = 22
    tw = sum(widths) + gap * (len(items) - 1)
    pad = 34; bw, bh = int(tw + pad * 2), int(size * 1.55)
    y = 1590
    p_in = clamp((t - g[0][1] + 0.05) / 0.15)
    bg = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, fill=(8, 14, 26, 170))
    put(fr, bg, W / 2, y, p_in)
    x = W / 2 - tw / 2
    for (w, active, s), wd in zip(items, widths):
        col = ORANGE if active else (255, 255, 255)
        im = text2d(w, size, col, stroke=3, scol=(10, 14, 24))
        sc = 1.0 + (0.12 * (1 - clamp((t - s) / 0.18)) if active else 0)
        if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BILINEAR)
        put(fr, im, x + wd / 2, y - 2, p_in)
        x += wd + gap

# ---------------------------------------------------------------- cenas
EV = []  # efeitos sonoros (tipo, tempo)
def sfx(kind, t): EV.append((kind, t))

def scene1(fr, tl, t):
    cam = Cam(pos=(0.8 * math.sin(0.5 * t), 0.35, 10.6 - 0.35 * tl), target=(0, 0.1, 0))
    bg = background(t, cam, 'navy', 'orange', 'blue'); fr.alpha_composite(bg)
    p = ease_out(tl / 1.1)
    objs = [dict(mesh=PHONE, R=rot(0.08, lerp(4.2, -0.35, p) + 0.06 * math.sin(tl * 2), 0.04),
                 T=(0, lerp(0.2, -0.15, p), lerp(-14, 0, p)), s=0.74, tex=screen_store(tl))]
    for i in range(6):
        q = (tl - 0.45 - i * 0.07) / 0.5
        if q <= 0: continue
        a = tl * 1.1 + i * math.tau / 6
        r = 1.75 * back(q, 1.2)
        objs.append(dict(mesh=COIN, R=rot(1.25 + 0.3 * math.sin(a), tl * 3 + i, 0), T=(r * math.cos(a), -0.2 + 1.5 * math.sin(a * 1.3 + i), r * math.sin(a) * 1.3), s=0.62))
    draw3d(fr, objs, cam, shadow=(540, 1420, 260, 34, p))
    pop_text(fr, 'TODOS HABLAN DE', 66, W / 2, 255, tl, 0.05)
    head3d(fr, 'VENDER ONLINE', 122, W / 2, 385, tl, 0.45, (255, 205, 130), (240, 120, 20), (110, 45, 5))
    return dict(zoom=1 + 0.012 * tl)

def scene2(fr, tl, t):
    cam = Cam(pos=(0.5 * math.sin(0.7 * t), 0.2, 9.6), target=(0, 0.2, 0), roll=0.03 * math.sin(t * 1.7))
    bg = background(t, cam, 'red', 'red', 'red'); fr.alpha_composite(bg)
    p = ease_out(tl / 0.8)
    objs = [dict(mesh=SHIELD, R=rot(lerp(-1.6, -0.05, p), 0.35 * math.sin(tl * 1.8), 0), T=(0, lerp(-6, 0.55, p), 0), s=1.15, tex=EXCL)]
    draw3d(fr, objs, cam, shadow=(540, 1330, 300, 36, p))
    pop_text(fr, 'PERO CASI NADIE', 70, W / 2, 210, tl, 0.0)
    pop_text(fr, 'TE ENSEÑA A', 70, W / 2, 300, tl, 0.35)
    hit = 2.35
    pop_text(fr, 'NO CAER EN', 74, W / 2, 1170, tl, 1.75, col=(255, 230, 230))
    if tl >= hit:
        img, mask = text3d('ESTAFAS', 205, (255, 140, 130), (215, 25, 35), (90, 8, 14))
        img = shine(img, mask, clamp((tl - hit) / 0.9))
        q = (tl - hit) / 0.35
        sc = 1.6 - 0.6 * ease_out(q)
        sh = (math.sin(tl * 60) * 8, math.cos(tl * 47) * 6) if tl - hit < 0.6 else (0, 0)
        w = warp3d(img, ry=0.12 * math.sin(tl * 2), rx=-0.1, scale=sc)
        put(fr, w, W / 2 + sh[0], 1320 + sh[1], clamp(q * 3))
    d = tl - hit
    fl = clamp(1 - d / 0.25) * 0.45 if d >= 0 else 0
    return dict(flash=fl, flash_col=(255, 60, 60), ca=8 * clamp(1 - d / 0.5) if d >= 0 else 0,
                shake=(math.sin(tl * 70) * 14 * clamp(1 - d / 0.5), math.cos(tl * 53) * 10 * clamp(1 - d / 0.5)) if d >= 0 else (0, 0),
                zoom=1.0 + (0.05 * clamp(1 - d / 0.5) if d >= 0 else 0.01 * tl))

def scene3(fr, tl, t):
    cam = Cam(pos=(0.6 * math.sin(0.4 * t), 0.4, 10.4 - 0.15 * tl), target=(0, 0.1, 0))
    split = 7.96 - SC[2]
    bg = background(t, cam, 'navy', 'gold' if tl < split + 0.3 else 'orange', 'blue'); fr.alpha_composite(bg)
    # fase 1: 45+
    if tl < split + 0.5:
        pop_text(fr, 'DESPUÉS DE LOS', 70, W / 2, 330, tl, 0.1)
        p = (tl - 0.75) / 0.6
        if p > 0:
            out = clamp((tl - split) / 0.45)
            img, mask = text3d('45+', 420, (255, 240, 180), (225, 150, 30), (105, 55, 8))
            img = shine(img, mask, clamp((tl - 0.9) / 1.0))
            w = warp3d(img, ry=(1 - ease_out(p)) * 1.4 + 0.25 * math.sin(tl * 1.4), rx=-0.12, scale=(0.4 + 0.6 * elastic(p)) * (1 - 0.7 * out))
            put(fr, w, W / 2, 820 - 500 * ease_in_out(out), clamp(p * 3) * (1 - out))
        if 0.75 <= tl < 0.80: pass
    # fase 2: celular -> negócio
    if tl >= split - 0.1:
        q = ease_out((tl - split + 0.1) / 0.9)
        objs = [dict(mesh=PHONE, R=rot(0.06, lerp(-2.2, 0.28, q) + 0.07 * math.sin(tl * 1.6), lerp(0.4, -0.03, q)),
                     T=(lerp(5, 0.05, q), -0.05, lerp(-4, 0.2, q)), s=0.74, tex=screen_store(tl))]
        bagp = (tl - split - 1.2) / 0.5
        for i, (bx, by) in enumerate([(-1.45, 0.9), (1.45, -0.2), (-1.35, -1.4)]):
            bq = bagp - i * 0.25
            if bq > 0:
                objs.append(dict(mesh=BAG, R=rot(0.3 * math.sin(tl + i), tl * 1.2 + i, 0.2), T=(bx, by + 0.15 * math.sin(tl * 2 + i), 0.8), s=0.55 * back(bq)))
        draw3d(fr, objs, cam, shadow=(540, 1440, 260, 34, q))
        pop_text(fr, 'TU CELULAR PUEDE SER', 62, W / 2, 230, tl, split + 0.25)
        head3d(fr, 'TU NEGOCIO', 150, W / 2, 360, tl, 11.2 - SC[2], (255, 205, 130), (240, 120, 20), (110, 45, 5))
    return dict(zoom=1 + 0.006 * tl)

def scene4(fr, tl, t):
    cam = Cam(pos=(0.4 * math.sin(0.5 * t), 1.1, 11.2), target=(0, -0.2, 0))
    bg = background(t, cam, 'deep', 'orange', 'blue'); fr.alpha_composite(bg)
    pop_text(fr, 'SON SOLO', 62, W / 2, 175, tl, 0.1)
    head3d(fr, '3 PASOS', 170, W / 2, 320, tl, 0.35, (255, 205, 130), (240, 120, 20), (110, 45, 5), sway=0.15)
    starts = [14.21 - SC[3], 16.07 - SC[3], 18.25 - SC[3]]
    act = -1
    for i, s in enumerate(starts):
        if tl >= s - 0.15: act = i
    # rotação do carrossel
    tgt = 0.0 if act < 0 else -act * (math.tau / 3)
    if act > 0:
        prev = -(act - 1) * (math.tau / 3)
        k = ease_in_out((tl - starts[act] + 0.15) / 0.6)
        ang0 = lerp(prev, tgt, k)
    else:
        ang0 = tgt
    objs = []
    Rr = 2.1
    for i, (n, ti, su) in enumerate(CARDS):
        q = (tl - 0.6 - i * 0.18) / 0.6
        if q <= 0: continue
        a = i * math.tau / 3 + ang0
        x = Rr * math.sin(a) * 0.95; z = Rr * math.cos(a) - Rr; y = -0.35 + (1 - back(q)) * -6
        front = math.cos(a)
        s = 0.82 + 0.1 * clamp((front - 0.5) * 2) if act >= 0 else 0.8
        objs.append(dict(mesh=CARD, R=rot(-0.05, a + 0.05 * math.sin(tl * 2 + i), 0), T=(x, y + 0.08 * math.sin(tl * 2.2 + i), z), s=s,
                         tex=tex_card(n, ti, su, i == act)))
    draw3d(fr, objs, cam, shadow=(540, 1330, 380, 36, 1))
    return dict(zoom=1.0)

def scene5(fr, tl, t):
    cam = Cam(pos=(0.5 * math.sin(0.6 * t), 0.2, 10.5), target=(0, 0, 0))
    bg = background(t, cam, 'navy', 'green', 'blue'); fr.alpha_composite(bg)
    head3d(fr, 'ASÍ DE SIMPLE', 130, W / 2, 300, tl, 0.0, (255, 255, 255), (215, 222, 235), (40, 60, 95), sway=0.12)
    rows = [(22.23, 'Sin computadora'), (23.61, 'Poca inversión'), (25.12, 'Paso a paso')]
    objs = []
    for i, (s, lab) in enumerate(rows):
        q = (tl - (s - SC[4]) + 0.05) / 0.55
        if q <= 0: continue
        y = 1.45 - i * 1.18
        objs.append(dict(mesh=BADGE, R=rot(0.1, lerp(math.pi * 2, 0.25, ease_out(q)) + 0.1 * math.sin(tl * 2 + i), 0), T=(-1.15, y, 0.2), s=0.85 * back(q, 1.4), tex=CHECK))
    draw3d(fr, objs, cam)
    for i, (s, lab) in enumerate(rows):
        q = (tl - (s - SC[4]) - 0.05) / 0.4
        if q <= 0: continue
        im = text2d(lab, 74)
        yy = cam.project(np.array([[0, 1.45 - i * 1.18, 0.2]]))[1][0]
        put(fr, im, lerp(1400, 360 + im.width / 2, ease_out(q)), yy, clamp(q * 3))
    return dict(zoom=1 + 0.005 * tl)

def scene6(fr, tl, t):
    cam = Cam(pos=(0.45 * math.sin(0.5 * t), 0.3, 10.8), target=(0, 0, 0))
    bg = background(t, cam, 'warm', 'orange', 'gold'); fr.alpha_composite(bg)
    head3d(fr, 'DESCUBRE TU PERFIL', 100, W / 2, 215, tl, 0.05, (255, 255, 255), (220, 226, 238), (40, 60, 95), sway=0.1)
    p = (tl - 0.6) / 0.35
    if p > 0:
        pill = Image.new('RGBA', (560, 110), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([0, 0, 559, 109], radius=55, fill=ORANGE + (255,))
        ImageDraw.Draw(pill).text((280, 57), 'EN 2 MINUTOS', font=font(60), fill=NAVY + (255,), anchor='mm')
        put(fr, pill.resize((int(560 * back(p)), int(110 * back(p)))) if back(p) > 0.05 else pill, W / 2, 335, clamp(p * 3))
    q = ease_out(tl / 0.8)
    objs = [dict(mesh=PHONE, R=rot(0.05, lerp(-1.5, -0.12, q) + 0.06 * math.sin(tl * 1.5), 0), T=(0, lerp(-6, 0.3, q), -0.4), s=0.62, tex=screen_quiz(tl))]
    bs = 29.68 - SC[5] - 0.2
    bq = (tl - bs) / 0.5
    tap = (tl - bs - 1.3) % 1.4
    press = 1 - 0.07 * math.exp(-((tap - 0.15) / 0.08) ** 2) if tl > bs + 1.0 else 1
    if bq > 0:
        objs.append(dict(mesh=BUTTON, R=rot(0.18 + 0.04 * math.sin(tl * 3), 0.1 * math.sin(tl * 1.7), 0), T=(0, -1.3, 1.6),
                         s=0.72 * back(bq, 1.5) * (1 + 0.03 * math.sin(tl * 6)) * press, tex=BTN))
    draw3d(fr, objs, cam, shadow=(540, 1330, 240, 30, q))
    if tl > bs + 1.0:
        hy = 1480 + 30 * math.sin(tl * 4.5)
        put(fr, emoji('\U0001F446', 110), 960, hy + 40, clamp((tl - bs - 1.0) * 3))
    if tl > bs + 0.8:
        put(fr, text2d('Contenido educativo. Los resultados varían y no están garantizados.', 26, (230, 230, 230)), W / 2, 1855, 0.8)
    return dict(zoom=1.0)

SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]

def frame_at(fi):
    t = fi / FPS
    k = max(i for i in range(6) if SC[i] <= t)
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    fx = SCENES[k](fr, t - SC[k], t) or {}
    if not (k == 5 and t > 32.4):
        if t < 32.9: captions(fr, t)
    # transição: zoom blur + flash nas fronteiras
    zb = 0; fl = fx.get('flash', 0); fcol = fx.get('flash_col', (255, 255, 255))
    for b in SC[1:6]:
        d = t - b
        if -0.12 <= d <= 0.18:
            zb = max(zb, 3.5 * (1 - abs(d) / 0.18))
            if abs(d) < 0.06: fl = max(fl, 0.35); fcol = (255, 240, 220)
    ca = max(fx.get('ca', 0), zb * 2.5)
    return post(fr, fi, bloom=0.5, ca=ca, shake=fx.get('shake', (0, 0)), zoom=fx.get('zoom', 1.0) + zb * 0.03,
                flash=fl, flash_col=fcol, zblur=zb)

# ---------------------------------------------------------------- áudio
SR = 44100
def build_audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', VO, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    vo = np.frombuffer(raw, np.float32).copy()
    n = int(TOTAL * SR); t = np.arange(n) / SR
    mus = np.zeros(n, np.float32)
    def add(sig, at, buf=mus):
        i = int(at * SR)
        if i >= n or i < 0: return
        j = min(n, i + len(sig)); buf[i:j] += sig[:j - i]
    bpm = 104; beat = 60 / bpm
    rng = np.random.default_rng(1)
    chords = [(55.0, 65.41, 82.41), (43.65, 65.41, 87.31), (49.0, 61.74, 73.42), (41.2, 61.74, 82.41)]
    bar = beat * 4
    k = 0; tt = 0.0
    while tt < TOTAL - 0.5:
        root, c2, c3 = chords[k % 4]
        L = int(bar * SR); x = np.arange(L) / SR
        pad = (np.sin(2 * np.pi * c2 * 2 * x) + np.sin(2 * np.pi * c3 * 2 * x) + 0.5 * np.sin(2 * np.pi * c3 * 4 * x)) * 0.018
        pad *= np.minimum(1, x / 0.3) * np.minimum(1, (bar - x) / 0.3)
        add(pad.astype(np.float32), tt)
        for b in range(8):
            Lb = int(beat / 2 * SR); xb = np.arange(Lb) / SR
            f = root * 2
            bass = np.sign(np.sin(2 * np.pi * f * xb)) * 0.035 * np.exp(-xb * 7)
            add(bass.astype(np.float32), tt + b * beat / 2)
        for b in range(16):
            Lp = int(0.16 * SR); xp = np.arange(Lp) / SR
            arp = [c2 * 4, c3 * 4, c2 * 8, c3 * 8][b % 4]
            add((np.sin(2 * np.pi * arp * xp) * 0.022 * np.exp(-xp * 22)).astype(np.float32), tt + b * beat / 4)
        tt += bar; k += 1
    tt = 0.0
    while tt < TOTAL - 0.5:
        L = int(0.35 * SR); x = np.arange(L) / SR
        ph = 2 * np.pi * np.cumsum(46 + 140 * np.exp(-x * 30)) / SR
        add((0.30 * np.sin(ph) * np.exp(-x * 9)).astype(np.float32), tt)
        L2 = int(0.05 * SR); x2 = np.arange(L2) / SR
        add((0.04 * rng.standard_normal(L2) * np.exp(-x2 * 80)).astype(np.float32), tt + beat / 2)
        tt += beat
    # ducking sob a voz
    env = np.zeros(n, np.float32); m = min(n, len(vo)); env[:m] = np.abs(vo[:m])
    win = int(0.12 * SR); env = np.convolve(env, np.ones(win) / win, 'same')
    duck = 1 - 0.62 * np.clip(env / 0.05, 0, 1)
    mus *= duck
    fx = np.zeros(n, np.float32)
    def whoosh(at, dur=0.55, amp=0.5):
        L = int(dur * SR); x = np.arange(L) / SR
        no = rng.standard_normal(L).astype(np.float32)
        k = np.linspace(60, 4, L).astype(int); cs = np.cumsum(no)
        y = np.array([(cs[i] - cs[max(0, i - k[i])]) / max(1, k[i]) for i in range(L)], np.float32)
        add(y * np.sin(np.pi * x / dur) ** 1.4 * amp * 3, at - dur * 0.55, fx)
    def impact(at, amp=0.9):
        L = int(1.2 * SR); x = np.arange(L) / SR
        ph = 2 * np.pi * np.cumsum(38 + 90 * np.exp(-x * 8)) / SR
        y = np.sin(ph) * np.exp(-x * 3.2) * amp + rng.standard_normal(L) * 0.25 * np.exp(-x * 18) * amp
        add(y.astype(np.float32), at, fx)
    def ding(at, amp=0.22, f0=1046.5):
        L = int(1.0 * SR); x = np.arange(L) / SR
        add(((np.sin(2 * np.pi * f0 * x) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * x)) * np.exp(-x * 5) * amp).astype(np.float32), at, fx)
    def riser(at, dur=1.4, amp=0.25):
        L = int(dur * SR); x = np.arange(L) / SR
        f = 200 + 1400 * (x / dur) ** 2; ph = 2 * np.pi * np.cumsum(f) / SR
        add((np.sin(ph) * (x / dur) ** 2 * amp + rng.standard_normal(L) * 0.06 * (x / dur) ** 2).astype(np.float32), at - dur, fx)
    for b in SC[1:6]: whoosh(b)
    impact(SC[1] + 2.35)
    impact(SC[2] + 0.75, 0.7)
    impact(11.2, 0.5)
    for s in [14.21, 16.07, 18.25]: whoosh(s - 0.1, 0.45, 0.35)
    for s in [22.23, 23.61, 25.12]: ding(s + 0.05)
    riser(29.6); impact(29.55, 0.6)
    for k in range(4): ding(29.68 + 1.3 + k * 1.4 + 0.15, 0.08, 1568)
    voice = np.zeros(n, np.float32); voice[:m] = vo[:m] * 1.15
    mix = voice + mus * 1.0 + fx * 0.75
    mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
    fade = int(0.8 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    s16 = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.stack([s16, s16], 1).tobytes())

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        os.makedirs('/home/claude/stills/A3', exist_ok=True)
        for ts in sys.argv[2:]:
            fi = int(float(ts) * FPS)
            Image.fromarray(frame_at(fi)).save(f'/home/claude/stills/A3/{float(ts):05.2f}.png')
    elif mode == 'part':
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for fi in range(a, b):
            p.stdin.write(frame_at(fi).tobytes())
            if fi % 30 == 0: print(out, fi, flush=True)
        p.stdin.close(); p.wait()
    elif mode == 'audio':
        build_audio(sys.argv[2])
