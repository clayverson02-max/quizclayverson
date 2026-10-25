"""Motor 3D por software (numpy/PIL): malhas extrudadas, iluminação de estúdio (matcap),
texto 3D extrudado com reflexo, cenário 3D, bloom e efeitos de pós-produção."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
GF = '/usr/share/fonts/truetype/google-fonts/'
FB = GF + 'Poppins-Bold.ttf'
FM = GF + 'Poppins-Medium.ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

NAVY = (18, 38, 63); CREAM = (246, 241, 231); ORANGE = (242, 140, 40)
RED = (232, 52, 52); GREEN = (34, 180, 110); GOLD = (255, 196, 70); WHITE = (255, 255, 255)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in_out(p): p = clamp(p); return p * p * (3 - 2 * p)
def back(p, s=1.7):
    p = clamp(p) - 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2
def elastic(p):
    p = clamp(p)
    if p in (0, 1): return p
    return 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * (2 * math.pi) / 3) + 1
def lerp(a, b, t): return a + (b - a) * t

_fonts = {}
def font(size, bold=True):
    k = (int(size), bold)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FB if bold else FM, int(size))
    return _fonts[k]

_emo = {}
def emoji(ch, size):
    k = (ch, int(size))
    if k not in _emo:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox()); r = size / max(im.size)
        _emo[k] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _emo[k]

# ============================== matemática 3D ==============================
def rot(rx=0, ry=0, rz=0):
    cx, sx = math.cos(rx), math.sin(rx); cy, sy = math.cos(ry), math.sin(ry); cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

class Cam:
    def __init__(self, pos=(0, 0, 10), target=(0, 0, 0), fov=34, roll=0.0):
        self.pos = np.array(pos, float); t = np.array(target, float)
        f = t - self.pos; f /= np.linalg.norm(f)
        up = np.array([math.sin(roll), math.cos(roll), 0.0])
        r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
        self.R = np.stack([r, u, -f])
        self.fpx = (H / 2) / math.tan(math.radians(fov) / 2)
    def to_cam(self, P): return (P - self.pos) @ self.R.T
    def project(self, P):
        pc = self.to_cam(P); d = -pc[:, 2]
        d = np.maximum(d, 1e-3)
        return W / 2 + self.fpx * pc[:, 0] / d, H / 2 - self.fpx * pc[:, 1] / d, d

# ============================== materiais (matcap) ==============================
MS = 256
_yy, _xx = np.mgrid[0:MS, 0:MS]
_nx = (_xx + 0.5) / MS * 2 - 1; _ny = -((_yy + 0.5) / MS * 2 - 1)
_r2 = np.clip(_nx ** 2 + _ny ** 2, 0, 1); _nz = np.sqrt(1 - _r2)
_N = np.stack([_nx, _ny, _nz], -1)
_N /= np.linalg.norm(_N, axis=-1, keepdims=True)

def _norm(v): v = np.array(v, float); return v / np.linalg.norm(v)
KEY = _norm([-0.55, 0.65, 0.75]); FILL = _norm([0.75, 0.05, 0.55]); TOP = _norm([0.0, 1.0, 0.35])

def make_matcap(base, metal=False, gloss=1.0, rim=(255, 170, 90), rim_k=0.55, amb=0.32):
    base = np.array(base, float) / 255; rimc = np.array(rim, float) / 255
    n = _N
    v = np.array([0, 0, 1.0])
    ndv = n[..., 2]
    r = 2 * ndv[..., None] * n - v
    dk = np.clip(n @ KEY, 0, 1); df = np.clip(n @ FILL, 0, 1); dt = np.clip(n @ TOP, 0, 1)
    fres = (1 - np.clip(ndv, 0, 1)) ** 3
    if metal:
        env = 0.25 + 0.95 * np.clip(r[..., 1] * 0.6 + 0.5, 0, 1) ** 1.6
        env += 0.5 * np.exp(-((r[..., 0] + 0.35) ** 2) * 18) * (r[..., 1] > -0.1)
        col = base[None, None, :] * env[..., None] * (0.55 + 0.6 * dk[..., None])
    else:
        diff = amb + 0.75 * dk + 0.25 * df + 0.15 * dt
        col = base[None, None, :] * diff[..., None]
    col = col + rimc[None, None, :] * fres[..., None] * rim_k
    # reflexos de softbox de estúdio
    sp = (np.clip(r @ KEY, 0, 1) ** 90) * 1.4 + (np.clip(r @ FILL, 0, 1) ** 40) * 0.45 + (np.clip(r @ TOP, 0, 1) ** 12) * 0.18
    box = np.exp(-(((r[..., 0] + 0.42) / 0.16) ** 2 + ((r[..., 1] - 0.48) / 0.24) ** 2) ** 2)
    sp = (sp + box * 0.9) * gloss
    return np.clip(col, 0, 1.6).astype(np.float32), sp.astype(np.float32)

MAT_NAMES = []
_DIFF = []; _SPEC = []
def add_mat(name, *a, **k):
    d, s = make_matcap(*a, **k); MAT_NAMES.append(name); _DIFF.append(d); _SPEC.append(s)
add_mat('orange', ORANGE, gloss=1.0)
add_mat('navy', (30, 58, 96), gloss=1.0, rim=(242, 140, 40), rim_k=0.7)
add_mat('cream', (250, 246, 236), gloss=0.8, rim=(255, 200, 150), rim_k=0.3, amb=0.45)
add_mat('gold', (255, 190, 70), metal=True, gloss=1.2, rim=(255, 230, 160), rim_k=0.4)
add_mat('chrome', (210, 220, 235), metal=True, gloss=1.2, rim=(160, 200, 255), rim_k=0.4)
add_mat('black', (22, 24, 30), gloss=1.3, rim=(140, 160, 200), rim_k=0.5, amb=0.4)
add_mat('red', RED, gloss=1.0, rim=(255, 140, 120), rim_k=0.5)
add_mat('green', GREEN, gloss=1.0, rim=(180, 255, 200), rim_k=0.4)
add_mat('white', (245, 245, 245), gloss=0.7, amb=0.5, rim_k=0.2)
add_mat('screen', (255, 255, 255), gloss=0.6, amb=0.78, rim_k=0.0)
DIFF = np.stack(_DIFF); SPEC = np.stack(_SPEC)
MID = {n: i for i, n in enumerate(MAT_NAMES)}

# ============================== malhas ==============================
class Mesh:
    def __init__(self, V, F, N, UV, fmat, ftex):
        self.V, self.F, self.N, self.UV, self.fmat, self.ftex = V, F, N, UV, fmat, ftex

def outline_roundrect(w, h, r, seg=10):
    pts = []
    for cx, cy, a0 in [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)]:
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)

def outline_circle(r, n=72):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([r * np.cos(a), r * np.sin(a)], 1)

def outline_shield(w, h, n=80):
    pts = []
    for i in range(n):
        t = i / n
        if t < 0.5:   # lado direito: de cima para a ponta
            u = t / 0.5
            x = w / 2 * (1 - u ** 2.2) ** 0.55; y = h * 0.42 - u * h * 0.92
        else:
            u = (t - 0.5) / 0.5
            x = -w / 2 * (1 - (1 - u) ** 2.2) ** 0.55; y = h * 0.42 - (1 - u) * h * 0.92
        pts.append((x, y))
    # topo levemente curvo
    top = [(w / 2 * (1 - 2 * k / 20), h * 0.42 + 0.06 * h * math.sin(math.pi * k / 20)) for k in range(1, 20)]
    pts = pts[: n // 2] + pts[n // 2:] + top[::-1]
    P = np.array(pts)
    # ordem anti-horária
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return P if area > 0 else P[::-1]

def _offset(P, d):
    n = len(P); out = np.zeros_like(P)
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        e1 = b - a; e2 = c - b
        n1 = np.array([e1[1], -e1[0]]); n1 /= (np.linalg.norm(n1) + 1e-9)
        n2 = np.array([e2[1], -e2[0]]); n2 /= (np.linalg.norm(n2) + 1e-9)
        nn = n1 + n2; nn /= (np.linalg.norm(nn) + 1e-9)
        out[i] = b + nn * d
    return out

def _zigzag(P):
    """Triangulação em faixas horizontais finas (polígono convexo) — caixas pequenas = render rápido."""
    k = len(P); top = int(np.argmax(P[:, 1]))
    idx = [(top + i) % k for i in range(k)]
    i, j = 1, k - 1; tris = []; prev_a, prev_b = idx[0], idx[0]
    a, b = idx[0], idx[0]
    left = [idx[0]]; L = 1; R = k - 1
    cur_l, cur_r = idx[0], idx[0]
    while L <= R:
        if P[idx[L], 1] >= P[idx[R], 1]:
            nl = idx[L]; tris.append((cur_l, nl, cur_r)); cur_l = nl; L += 1
        else:
            nr = idx[R]; tris.append((cur_l, nr, cur_r)); cur_r = nr; R -= 1
    return [t for t in tris if len(set(t)) == 3]

def extrude(outline, depth, bevel=0.06, mats=('orange', 'orange', 'orange'), front_tex=False):
    """Extrusão com chanfro. As laterais vão para o rasterizador; as tampas planas são
    desenhadas por transformação de perspectiva (bem mais rápido)."""
    P = outline
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0: P = P[::-1]
    d2 = depth / 2; b = bevel
    prof = [(-b, d2), (-b * 0.3, d2 - b * 0.35), (0, d2 - b), (0, -d2 + b), (-b * 0.3, -d2 + b * 0.35), (-b, -d2)]
    rings = [np.column_stack([_offset(P, off), np.full(len(P), z)]) for off, z in prof]
    k = len(P)
    V = np.concatenate(rings); F = []
    for j in range(len(rings) - 1):
        for i in range(k):
            a = j * k + i; b2 = j * k + (i + 1) % k; c = (j + 1) * k + i; d = (j + 1) * k + (i + 1) % k
            F.append([a, c, b2]); F.append([b2, c, d])
    F = np.array(F, int)
    fa = V[F[:, 1]] - V[F[:, 0]]; fb = V[F[:, 2]] - V[F[:, 0]]
    fn = np.cross(fa, fb)
    cen = V[F].mean(1)
    sgn = np.sign(np.sum(fn * np.column_stack([cen[:, 0], cen[:, 1], cen[:, 2] * 3]), 1)); sgn[sgn == 0] = 1
    fn *= sgn[:, None]
    N = np.zeros_like(V)
    for v in range(3): np.add.at(N, F[:, v], fn)
    N /= (np.linalg.norm(N, axis=1, keepdims=True) + 1e-9)
    fnn = fn / (np.linalg.norm(fn, axis=1, keepdims=True) + 1e-9)
    m = Mesh(V, F, N, np.zeros((len(V), 2)), np.full(len(F), MID[mats[0]]), np.zeros(len(F), bool))
    m.fn = fnn; m.fc = cen
    m.caps = [dict(poly=rings[0][:, :2], z=d2, sign=1, mat=mats[1], tex=front_tex),
              dict(poly=rings[-1][:, :2], z=-d2, sign=-1, mat=mats[2], tex=False)]
    return m

# ============================== rasterizador ==============================
def render_objects(objs, cam, ss=2, pad=6):
    Vs = []; Ns = []; Fs = []; FM = []; off = 0
    for o in objs:
        m = o['mesh']; R = o.get('R', np.eye(3)); T = np.array(o.get('T', (0, 0, 0)), float); s = o.get('s', 1.0)
        Vw = (m.V * s) @ R.T + T; Nw = m.N @ R.T
        fnw = m.fn @ R.T; fcw = (m.fc * s) @ R.T + T
        vis = np.sum(fnw * (cam.pos[None, :] - fcw), 1) > 0
        Vs.append(Vw); Ns.append(Nw); Fs.append(m.F[vis] + off); FM.append(m.fmat[vis]); off += len(m.V)
    V = np.concatenate(Vs); N = np.concatenate(Ns); F = np.concatenate(Fs); FMv = np.concatenate(FM)
    if len(F) == 0: return None
    sx, sy, dz = cam.project(V)
    Nc = N @ cam.R.T
    used = np.unique(F)
    x0 = int(max(0, math.floor(sx[used].min()) - pad)); x1 = int(min(W, math.ceil(sx[used].max()) + pad))
    y0 = int(max(0, math.floor(sy[used].min()) - pad)); y1 = int(min(H, math.ceil(sy[used].max()) + pad))
    if x1 <= x0 or y1 <= y0: return None
    rw, rh = (x1 - x0) * ss, (y1 - y0) * ss
    px = (sx - x0) * ss; py = (sy - y0) * ss
    zb = np.full((rh, rw), np.inf, np.float32); ib = np.full((rh, rw), -1, np.int32)
    B0 = np.zeros((rh, rw), np.float32); B1 = np.zeros((rh, rw), np.float32)
    for fi, (a, b, c) in enumerate(F):
        ax, ay, bx, by, cx, cy = px[a], py[a], px[b], py[b], px[c], py[c]
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if abs(area) < 1e-6: continue
        xa = max(0, int(min(ax, bx, cx))); xb = min(rw, int(max(ax, bx, cx)) + 2)
        ya = max(0, int(min(ay, by, cy))); yb = min(rh, int(max(ay, by, cy)) + 2)
        if xb <= xa or yb <= ya: continue
        gx = np.arange(xa, xb, dtype=np.float32)[None, :] + 0.5; gy = np.arange(ya, yb, dtype=np.float32)[:, None] + 0.5
        w0 = ((bx - gx) * (cy - gy) - (by - gy) * (cx - gx)) / area
        w1 = ((cx - gx) * (ay - gy) - (cy - gy) * (ax - gx)) / area
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        za, zb_, zc = dz[a], dz[b], dz[c]
        iz = w0 / za + w1 / zb_ + w2 / zc
        depth = 1 / iz
        sub = zb[ya:yb, xa:xb]
        m &= depth < sub
        if not m.any(): continue
        sub[m] = depth[m]
        ib[ya:yb, xa:xb][m] = fi
        B0[ya:yb, xa:xb][m] = (w0 / za / iz)[m]
        B1[ya:yb, xa:xb][m] = (w1 / zb_ / iz)[m]
    hit = ib >= 0
    out = np.zeros((rh, rw, 4), np.float32)
    if hit.any():
        fi = ib[hit]; b0 = B0[hit]; b1 = B1[hit]; b2 = 1 - b0 - b1
        tri = F[fi]
        n = Nc[tri[:, 0]] * b0[:, None] + Nc[tri[:, 1]] * b1[:, None] + Nc[tri[:, 2]] * b2[:, None]
        n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
        n[n[:, 2] < 0] *= -1
        mu = np.clip(((n[:, 0] * 0.5 + 0.5) * (MS - 1)).astype(int), 0, MS - 1)
        mv = np.clip(((0.5 - 0.5 * n[:, 1]) * (MS - 1)).astype(int), 0, MS - 1)
        mid = FMv[fi]
        c = DIFF[mid, mv, mu] + SPEC[mid, mv, mu][:, None]
        out[hit, :3] = np.clip(c, 0, 1); out[hit, 3] = 1
    out = out.reshape(rh // ss, ss, rw // ss, ss, 4).mean((1, 3))
    rgb = out[..., :3] / np.maximum(out[..., 3:4], 1e-6)
    img = np.concatenate([rgb, out[..., 3:4]], -1)
    return Image.fromarray((img * 255).astype(np.uint8), 'RGBA'), x0, y0

_capcache = {}
def _cap_image(poly, mat, tex_img, n_view, key):
    """Imagem RGBA da tampa (no espaço da textura), sombreada pela normal na vista."""
    mn = poly.min(0); mx = poly.max(0); asp = (mx[0] - mn[0]) / (mx[1] - mn[1])
    th = 900 if tex_img is None else tex_img.height
    tw = int(th * asp)
    mk = ('mask', key, tw, th)
    if mk not in _capcache:
        S = 2
        msk = Image.new('L', (tw * S, th * S), 0)
        pp = [((p[0] - mn[0]) / (mx[0] - mn[0]) * tw * S, (1 - (p[1] - mn[1]) / (mx[1] - mn[1])) * th * S) for p in poly]
        ImageDraw.Draw(msk).polygon(pp, fill=255)
        _capcache[mk] = msk.resize((tw, th), Image.LANCZOS)
    msk = _capcache[mk]
    nz = n_view / (np.linalg.norm(n_view) + 1e-9)
    mu = int(clamp(nz[0] * 0.5 + 0.5) * (MS - 1)); mv = int(clamp(0.5 - 0.5 * nz[1]) * (MS - 1))
    mi = MID[mat]
    base = DIFF[mi, mv, mu]; sp = SPEC[mi, mv, mu]
    # degradê sutil de brilho na tampa (reflexo de estúdio)
    gk = ('grad', tw, th)
    if gk not in _capcache:
        yy, xx = np.mgrid[0:th, 0:tw]
        _capcache[gk] = np.exp(-(((xx / tw) - 0.25 + (yy / th) * 0.4) / 0.22) ** 2).astype(np.float32)
    grad = _capcache[gk]
    glint = clamp(0.25 + 0.75 * nz[2]) * clamp(1.0 - abs(nz[0]) * 1.4)
    if tex_img is not None:
        t = np.asarray(tex_img.convert('RGBA').resize((tw, th)), np.float32) / 255
        ta = t[..., 3:4]
        shade = min(1.0, float(base.mean())) * 0.95 if mat == 'screen' else 1.0
        matc = np.clip(base + sp * 0.5, 0, 1)[None, None, :]
        rgb = matc * (1 - ta) + t[..., :3] * shade * ta + grad[..., None] * 0.12 * glint
    else:
        rgb = np.clip(base + sp * 0.5, 0, 1)[None, None, :] + grad[..., None] * 0.18 * glint
    a = np.asarray(msk, np.float32)[..., None] / 255
    arr = np.concatenate([np.clip(rgb, 0, 1), a], -1)
    return Image.fromarray((arr * 255).astype(np.uint8), 'RGBA'), mn, mx

def draw3d(frame, objs, cam, shadow=None):
    if shadow is not None:
        sx, sy, sw, sh, a = shadow
        sl = Image.new('RGBA', (int(sw * 2.2), int(sh * 3)), (0, 0, 0, 0))
        ImageDraw.Draw(sl).ellipse([sw * 0.6, sh, sw * 1.6, sh * 2], fill=(0, 0, 0, int(160 * a)))
        sl = sl.filter(ImageFilter.GaussianBlur(sh * 0.45))
        frame.alpha_composite(sl, (int(sx - sl.width / 2), int(sy - sl.height / 2)))
    # ordena objetos do mais distante para o mais próximo
    def dist(o): return -np.linalg.norm(np.array(o.get('T', (0, 0, 0)), float) - cam.pos)
    for o in sorted(objs, key=dist):
        r = render_objects([o], cam)
        if r is not None:
            img, x0, y0 = r
            frame.alpha_composite(img, (x0, y0))
        m = o['mesh']; R = o.get('R', np.eye(3)); T = np.array(o.get('T', (0, 0, 0)), float); s = o.get('s', 1.0)
        for ci, cap in enumerate(m.caps):
            nw = R @ np.array([0, 0, cap['sign']], float)
            cw = R @ np.array([0, 0, cap['z']]) * s + T
            if np.dot(nw, cam.pos - cw) <= 0: continue
            tex = o.get('tex') if cap['tex'] else None
            if tex is not None and not isinstance(tex, Image.Image):
                tex = Image.fromarray((tex * 255).astype(np.uint8), 'RGBA')
            img, mn, mx = _cap_image(cap['poly'], cap['mat'], tex, cam.R @ nw, (id(m), ci))
            corners = np.array([[mn[0], mx[1], cap['z']], [mx[0], mx[1], cap['z']], [mx[0], mn[1], cap['z']], [mn[0], mn[1], cap['z']]])
            if cap['sign'] < 0:  # vista de trás: espelha
                corners = corners[[1, 0, 3, 2]]
            Pw = (corners * s) @ R.T + T
            qx, qy, _ = cam.project(Pw)
            bx0, by0 = int(math.floor(qx.min())) - 2, int(math.floor(qy.min())) - 2
            bx1, by1 = int(math.ceil(qx.max())) + 2, int(math.ceil(qy.max())) + 2
            if bx1 <= bx0 or by1 <= by0 or bx1 < 0 or by1 < 0 or bx0 > W or by0 > H: continue
            dst = [(qx[i] - bx0, qy[i] - by0) for i in range(4)]
            coeffs = _persp_coeffs([(0, 0), (img.width, 0), (img.width, img.height), (0, img.height)], dst)
            wimg = img.transform((bx1 - bx0, by1 - by0), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
            frame.alpha_composite(wimg, (bx0, by0)) if bx0 >= 0 and by0 >= 0 and bx1 <= W and by1 <= H else _safe_paste(frame, wimg, bx0, by0)

def _safe_paste(frame, img, x, y):
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(img.width, W - x), min(img.height, H - y)
    if cx1 <= cx0 or cy1 <= cy0: return
    frame.alpha_composite(img.crop((cx0, cy0, cx1, cy1)), (x + cx0, y + cy0))

def tex_from_image(im):
    return np.asarray(im.convert('RGBA'), np.float32) / 255

# ============================== texto 3D extrudado ==============================
_t3 = {}
def text3d(text, size, top=(255, 255, 255), bot=(225, 228, 236), side=(150, 70, 10), depth=None, tracking=0):
    key = (text, size, top, bot, side, depth)
    if key in _t3: return _t3[key]
    f = font(size)
    depth = depth or max(6, int(size * 0.11))
    tw = int(f.getlength(text)) + 40; th = int(size * 1.45)
    pad = depth + 30
    Wt, Ht = tw + pad * 2, th + pad * 2
    mask = Image.new('L', (Wt, Ht), 0)
    ImageDraw.Draw(mask).text((pad + 20, pad + int(size * 1.08)), text, font=f, fill=255, anchor='ls',
                              stroke_width=max(1, size // 60), stroke_fill=255)
    out = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0))
    # sombra projetada suave
    sh = Image.new('RGBA', (Wt, Ht), (0, 0, 0, 0))
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(size * 0.08)).point(lambda v: int(v * 0.55)))
    out.alpha_composite(sh, (0, 0)) if False else None
    # extrusão (camadas laterais)
    sd = np.array(side, float)
    for i in range(depth, 0, -1):
        k = 0.55 + 0.45 * (1 - i / depth)
        col = tuple(int(c * k) for c in sd)
        layer = Image.new('RGBA', (Wt, Ht), col + (255,))
        out.paste(layer, (int(i * 0.35), i), ImageChops.offset(mask, 0, 0))
    # face frontal com degradê
    g = np.linspace(0, 1, Ht)[:, None, None]
    face = (np.array(top)[None, None, :] * (1 - g) + np.array(bot)[None, None, :] * g)
    face = np.repeat(face, Wt, 1)
    # chanfro: realce nas bordas superiores
    m = np.asarray(mask, np.float32) / 255
    bl = np.asarray(mask.filter(ImageFilter.GaussianBlur(max(1.5, size / 40))), np.float32) / 255
    gy = np.zeros_like(bl); gy[1:-1] = bl[2:] - bl[:-2]
    gx = np.zeros_like(bl); gx[:, 1:-1] = bl[:, 2:] - bl[:, :-2]
    light = np.clip((gy + gx * 0.5) * 6, -1, 1)
    face = face + light[..., None] * 70
    fimg = Image.fromarray(np.clip(np.dstack([face, m * 255]), 0, 255).astype(np.uint8), 'RGBA')
    out.alpha_composite(fimg)
    _t3[key] = (out, mask)
    return out, mask

def shine(img, mask, p, width=0.12, strength=0.85):
    """Faixa de brilho especular que passa pelo texto (p de 0 a 1)."""
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + yy * 0.6) / (w + h * 0.6)
    band = np.exp(-((u - lerp(-0.2, 1.2, p)) / width) ** 2) * strength
    a = np.asarray(img, np.float32).copy()
    mm = np.asarray(mask, np.float32) / 255
    a[..., :3] = np.clip(a[..., :3] + (band * mm)[..., None] * 255, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

def _persp_coeffs(src, dst):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp3d(img, ry=0.0, rx=0.0, rz=0.0, scale=1.0, f=2200):
    """Gira uma camada 2D no espaço 3D com perspectiva real."""
    w, h = img.size
    c = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], float) * scale
    R = rot(rx, ry, rz)
    p = c @ R.T
    z = f + p[:, 2]
    dst = np.stack([p[:, 0] * f / z, p[:, 1] * f / z], 1)
    mn = dst.min(0); mx = dst.max(0)
    ow, oh = int(mx[0] - mn[0]) + 4, int(mx[1] - mn[1]) + 4
    dst2 = dst - mn + 2
    coeffs = _persp_coeffs([(0, 0), (w, 0), (w, h), (0, h)], dst2.tolist())
    return img.transform((ow, oh), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

def put(frame, im, cx, cy, alpha=1.0):
    if alpha <= 0: return
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ============================== cenário 3D ==============================
_rng = np.random.default_rng(7)
PART = np.column_stack([_rng.uniform(-9, 9, 140), _rng.uniform(-6, 9, 140), _rng.uniform(-30, 4, 140)])
PCOL = _rng.choice([0, 1, 2], 140, p=[0.55, 0.3, 0.15])

def _glow_sprite(r, col, a=255):
    s = r * 2; yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    al = (np.clip(1 - d, 0, 1) ** 2.2 * a).astype(np.uint8)
    arr = np.zeros((s, s, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = al
    return Image.fromarray(arr, 'RGBA')
SPR = [_glow_sprite(32, (255, 170, 80)), _glow_sprite(32, (120, 170, 255)), _glow_sprite(32, (255, 255, 255))]
BIG = {'orange': _glow_sprite(600, ORANGE, 120), 'blue': _glow_sprite(600, (40, 90, 200), 140),
       'red': _glow_sprite(600, (230, 40, 40), 150), 'gold': _glow_sprite(600, (255, 190, 60), 120),
       'green': _glow_sprite(600, (30, 200, 120), 110)}

def _bggrad(top, bot):
    arr = np.zeros((H, W, 3), np.float32)
    for i in range(3): arr[..., i] = np.linspace(top[i], bot[i], H)[:, None]
    return Image.fromarray(arr.astype(np.uint8), 'RGB').convert('RGBA')
BGS = {'navy': _bggrad((14, 30, 56), (3, 8, 18)), 'red': _bggrad((52, 10, 16), (8, 2, 6)),
       'warm': _bggrad((60, 30, 14), (10, 6, 10)), 'deep': _bggrad((8, 22, 44), (2, 4, 10))}

def background(t, cam, mode='navy', glow='orange', glow2='blue', grid=True):
    fr = BGS[mode].copy()
    g = BIG[glow]; fr.alpha_composite(g, (int(W * 0.5 + 260 * math.sin(t * 0.5) - 600), int(H * 0.36 + 180 * math.cos(t * 0.4) - 600)))
    g2 = BIG[glow2]; fr.alpha_composite(g2, (int(W * 0.5 - 300 * math.cos(t * 0.35) - 600), int(H * 0.78 + 160 * math.sin(t * 0.45) - 600)))
    if grid:
        lay = Image.new('RGBA', (W // 2, H // 2), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        y = -3.2
        for x in range(-14, 15):
            P = np.array([[x, y, 3.0], [x, y, -40.0]])
            sx, sy, dz = cam.project(P)
            d.line([(sx[0] / 2, sy[0] / 2), (sx[1] / 2, sy[1] / 2)], fill=(120, 170, 255, 34), width=1)
        for zz in np.arange(3, -40, -1.5):
            P = np.array([[-14, y, zz], [14, y, zz]])
            sx, sy, dz = cam.project(P)
            a = int(46 * clamp(1 - (-zz) / 40))
            d.line([(sx[0] / 2, sy[0] / 2), (sx[1] / 2, sy[1] / 2)], fill=(120, 170, 255, a), width=1)
        lay = lay.resize((W, H), Image.BILINEAR)
        fr.alpha_composite(lay)
    P = PART.copy(); P[:, 1] += (t * 0.25) % 15 - 0; P[:, 1] = (P[:, 1] + 6) % 15 - 6
    sx, sy, dz = cam.project(P)
    for i in np.argsort(-dz):
        if dz[i] < 1: continue
        s = int(clamp(26 / dz[i], 0.05, 3) * 40)
        if s < 3: continue
        tw = 0.6 + 0.4 * math.sin(t * 2 + i)
        sp = SPR[PCOL[i]].resize((s, s), Image.BILINEAR)
        if tw < 1: sp.putalpha(sp.getchannel('A').point(lambda v: int(v * tw)))
        fr.alpha_composite(sp, (int(sx[i] - s / 2), int(sy[i] - s / 2))) if 0 <= sx[i] < W and 0 <= sy[i] < H else None
    return fr

# ============================== pós-produção ==============================
_yy2, _xx2 = np.mgrid[0:H, 0:W]
VIG = (1 - 0.55 * np.clip(((_xx2 - W / 2) / (W * 0.75)) ** 2 + ((_yy2 - H / 2) / (H * 0.72)) ** 2, 0, 1))[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(i).normal(0, 3.2, (H, W, 1)).astype(np.float32) for i in range(5)]

def post(frame, fi, bloom=0.55, ca=0.0, shake=(0, 0), zoom=1.0, flash=0.0, flash_col=(255, 255, 255), zblur=0.0, rgb_tint=None):
    im = frame.convert('RGB')
    if zoom != 1.0 or shake != (0, 0):
        zw, zh = int(W * zoom), int(H * zoom)
        z = im.resize((zw, zh), Image.BILINEAR)
        ox = (zw - W) // 2 - int(shake[0]); oy = (zh - H) // 2 - int(shake[1])
        im = z.crop((ox, oy, ox + W, oy + H))
    if zblur > 0:
        acc = np.asarray(im, np.float32); n = 1
        for k in (1, 2, 3):
            s = 1 + zblur * 0.05 * k
            zz = im.resize((int(W * s), int(H * s)), Image.BILINEAR)
            ox, oy = (zz.width - W) // 2, (zz.height - H) // 2
            acc += np.asarray(zz.crop((ox, oy, ox + W, oy + H)), np.float32); n += 1
        a = acc / n
    else:
        a = np.asarray(im, np.float32)
    if bloom > 0:
        small = Image.fromarray(np.clip((a - 150) * 1.6, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
        bl = small.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
        bl2 = small.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
        a = a + (np.asarray(bl, np.float32) * 0.9 + np.asarray(bl2, np.float32) * 0.5) * bloom
    if ca > 0:
        k = int(ca)
        a[..., 0] = np.roll(a[..., 0], k, 1); a[..., 2] = np.roll(a[..., 2], -k, 1)
    if rgb_tint is not None:
        a = a * np.array(rgb_tint, np.float32)
    a = a * VIG + GRAIN[fi % 5]
    if flash > 0:
        a = a * (1 - flash) + np.array(flash_col, np.float32) * flash
    return np.clip(a, 0, 255).astype(np.uint8)
