
# -*- coding: utf-8 -*-
"""artlib: 1024px master art with dual-contrast ink mist (visible on white AND dark)."""
import os, math, random, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = r"D:\deepseek\out"
M, U = 1024, 32.0
INK   = (6, 10, 12)
JADE  = (104, 222, 214)     # cool teal, tuned to a blue wallpaper
PALE  = (198, 246, 250)
GOLD  = (226, 196, 108)
RED   = (170, 54, 48)

SRC = Image.open(os.path.join(ROOT, "brush_final3.png")).convert("RGBA")
SRC = ImageEnhance.Color(SRC).enhance(1.14)
SRC = ImageEnhance.Contrast(SRC).enhance(1.06)
BW, BH = SRC.size

def layer(): return Image.new("RGBA", (M, M), (0, 0, 0, 0))

def radial(cx, cy, r, color, a, power=2.0, ry=None):
    yy, xx = np.mgrid[0:M, 0:M]
    ry = ry or r
    f = np.clip(1.0 - np.sqrt(((xx-cx)/r)**2 + ((yy-cy)/ry)**2), 0, 1)**power
    arr = np.zeros((M,M,4), np.uint8)
    arr[...,0], arr[...,1], arr[...,2] = color
    arr[...,3] = (f*a).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

def sprite(L, ang=0.0):
    s = L*U/max(BW,BH)
    im = SRC.resize((max(1,int(BW*s)), max(1,int(BH*s))), Image.LANCZOS)
    if ang: im = im.rotate(ang, expand=True, resample=Image.BICUBIC)
    return im

def tip_off(spr):
    arr = np.asarray(spr.getchannel("A"))
    ys, xs = np.where(arr > 8)
    s = xs.astype(np.int64) + ys.astype(np.int64)
    m = s.min(); sel = s < m + 8
    return (int(np.mean(xs[sel])), int(np.mean(ys[sel])))

def contour(spr, color=INK, a=150, blur=0.6):
    m = spr.getchannel("A")
    dil = m.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(blur))
    arr = np.clip((np.asarray(dil).astype(np.float32)-np.asarray(m).astype(np.float32))*(a/80.0),0,255).astype(np.uint8)
    h,w = arr.shape
    im = np.zeros((h,w,4),np.uint8); im[...,0],im[...,1],im[...,2] = color; im[...,3] = arr
    return Image.fromarray(im,"RGBA")

def bezier(p0,p1,p2,n=200):
    return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],
             (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in (i/(n-1) for i in range(n))]

def strand_mask(pts, w0, w1, wob=0.28):
    """opaque mask of a tapered stroke with organic width wobble"""
    lay = Image.new("L", (M, M), 0); d = ImageDraw.Draw(lay); n = len(pts)
    for i,(x,y) in enumerate(pts):
        t = i/(n-1)
        base = w0*(1-t) + w1*t
        mod = 1.0 + wob*math.sin(t*9.0 + 1.3) + 0.12*math.sin(t*23.0)
        r = base*mod*0.5
        if r <= 0.15: continue
        d.ellipse([x-r,y-r,x+r,y+r], fill=255)
    return lay.filter(ImageFilter.GaussianBlur(0.35))

def dual_stroke(pts, w0, w1, core_a=120, edge_a=145, blur=0.9, halo_w=None):
    """thin ink core inside a wide pale halo -> visible on both light and dark backgrounds"""
    m = strand_mask(pts, w0, w1)
    if halo_w is None:
        edge = Image.fromarray(np.clip(np.asarray(m.filter(ImageFilter.MaxFilter(5))).astype(np.int16) -
                                       np.asarray(m).astype(np.int16), 0, 255).astype(np.uint8), "L")
    else:
        edge = strand_mask(pts, halo_w, halo_w*0.12)
    edge = edge.filter(ImageFilter.GaussianBlur(blur*1.4))
    core = m.filter(ImageFilter.GaussianBlur(blur*0.6))
    out = layer()
    e = np.zeros((M,M,4), np.uint8); e[...,0],e[...,1],e[...,2] = PALE
    e[...,3] = (np.asarray(edge).astype(np.float32)*edge_a/255.0).astype(np.uint8)
    out = Image.alpha_composite(out, Image.fromarray(e, "RGBA"))
    c = np.zeros((M,M,4), np.uint8); c[...,0],c[...,1],c[...,2] = INK
    c[...,3] = (np.asarray(core).astype(np.float32)*core_a/255.0).astype(np.uint8)
    out = Image.alpha_composite(out, Image.fromarray(c, "RGBA"))
    return out

TIP = (3.6, 3.6); DOT = (4.9, 4.9); BLEN = 27.4

def haze(cx, cy, phase=0.0, strength=1.0):
    """soft ink aura: dark veil + pale jade ring, works on both backgrounds"""
    c = layer()
    for (ox, oy, rr, aa) in ((-6*U, -5*U, 6.5*U, 8), (7*U, 6*U, 7.0*U, 7)):
        c = Image.alpha_composite(c, radial(cx+ox, cy+oy, rr, INK, int(aa*strength), 2.2))
        c = Image.alpha_composite(c, radial(cx+ox+1.2*U, cy+oy+1.2*U, rr*0.7, PALE, int(aa*0.9*strength), 2.4))
    ring = layer()
    # jade ring: big soft disc minus smaller one
    big = np.asarray(radial(cx, cy, 20.0*U, PALE, 255, 2.0)).astype(np.float32)[...,3]/255.0
    inner = np.asarray(radial(cx, cy, 13.5*U, PALE, 255, 1.4)).astype(np.float32)[...,3]/255.0
    ringa = np.clip(big*0.55 - inner*0.75, 0, 1) * (0.42*strength)
    arr = np.zeros((M,M,4), np.uint8); arr[...,0],arr[...,1],arr[...,2] = PALE
    arr[...,3] = (ringa*255).astype(np.uint8)
    c = Image.alpha_composite(c, Image.fromarray(arr,"RGBA"))
    return c.filter(ImageFilter.GaussianBlur(1.2))

def mist_strands(frame=0, n=1, cx=None, cy=None, strength=1.0):
    cx = cx or 15.5*U; cy = cy or 16.5*U
    c = layer()
    specs = [(9.6, 2.0, 1.10, 0.0, 1), (12.8, 1.6, 0.90, 2.2, -1),
             (7.2, 1.4, 0.70, 4.6, -1)]
    for i,(R, arc, wsc, ph, dirn) in enumerate(specs):
        a0 = (frame/n*math.tau*dirn if n > 1 else 0) + ph
        pts=[]
        for k in range(110):
            th = a0 + k/109.0*arc
            rr = R*U*(1.0 + 0.12*math.sin(th*1.8+i))
            pts.append((cx+math.cos(th)*rr, cy+math.sin(th)*rr*0.95))
        amp = 1.0 if n == 1 else (0.55+0.45*math.sin(frame/n*math.tau + i*2.0))
        c = Image.alpha_composite(c, dual_stroke(pts, 0.42*U*wsc, 0.05*U,
                                                 core_a=int(150*amp*strength),
                                                 edge_a=int(150*amp*strength), blur=0.65,
                                                 halo_w=1.35*U*wsc))
    return c

def flow_light(spr, px, py, tx, ty, blen, frame, n, strength=1.0):
    """bright band travelling along the jade handle, masked to the handle pixels only"""
    sa = np.asarray(spr).astype(np.float32)
    al = sa[...,3]
    r_, g_, b_ = sa[...,0], sa[...,1], sa[...,2]
    jm = ((g_ > r_+14) & (g_ > b_+4) & (g_ > 88) & (al > 110)).astype(np.float32)
    jm = np.asarray(Image.fromarray((jm*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32)/255.0
    h, w = jm.shape
    MASK = np.zeros((M, M), np.float32)
    MASK[py:py+h, px:px+w] = jm

    ux, uy = 0.755, 0.655
    yy, xx = np.mgrid[0:M, 0:M].astype(np.float32)
    T = ((xx-tx)*ux + (yy-ty)*uy) / (blen*U)

    c = (frame/n)*1.30 - 0.12
    band = np.exp(-((T-c)**2)/(2*0.105**2))
    band2 = np.exp(-((T-(c-0.22))**2)/(2*0.040**2))*0.6
    base = 0.14 + 0.08*math.sin(frame/n*math.tau*2)
    inten = np.clip((band + band2 + base)*MASK, 0, 1) * strength
    arr = np.zeros((M, M, 4), np.uint8)
    arr[...,0] = 196; arr[...,1] = 255; arr[...,2] = 246
    arr[...,3] = (inten*225).astype(np.uint8)
    return Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(0.5))

def core_art(dot=True, arc=True, frame=0, n=1, mist=1.0, blen=None, tip=None, center=None, dotpos=None, flow=0.0):
    blen = blen or BLEN
    tip = tip or TIP
    center = center or (15.5, 16.5)
    dotpos = dotpos or DOT
    tx, ty = tip[0]*U, tip[1]*U
    spr = sprite(blen); ox, oy = tip_off(spr); px, py = int(tx)-ox, int(ty)-oy
    c = layer()
    c = Image.alpha_composite(c, haze(center[0]*U, center[1]*U, strength=mist))
    c = Image.alpha_composite(c, mist_strands(frame, n, cx=center[0]*U, cy=center[1]*U, strength=mist))
    c.alpha_composite(contour(spr), (px, py))
    if arc:
        p = bezier((tx+6.6*U, ty+10.2*U), (33*U, 3.6*U), (58*U, 30*U), 320)
        c = Image.alpha_composite(c, dual_stroke(p, 1.35*U, 0.25*U, core_a=70, edge_a=120, blur=0.8))
    c.alpha_composite(spr, (px, py))
    if flow > 0:
        c = Image.alpha_composite(c, flow_light(spr, px, py, tx, ty, blen, frame, n, flow))
    c = Image.alpha_composite(c, radial(dotpos[0]*U, dotpos[1]*U, 5.2*U, PALE, 90, 2.6))
    if dot:
        d = ImageDraw.Draw(c); r = 1.35*U
        d.ellipse([dotpos[0]*U-r, dotpos[1]*U-r, dotpos[0]*U+r, dotpos[1]*U+r], fill=(6,10,9,238))
        r2 = 0.8*U
        d.ellipse([dotpos[0]*U-r2, dotpos[1]*U-r2, dotpos[0]*U+r2, dotpos[1]*U+r2], fill=PALE+(248,))
    return c

# ---------- export ----------
def srgb2lin(x): return np.where(x <= 0.04045, x/12.92, ((x+0.055)/1.055)**2.4)
def lin2srgb(x): return np.where(x <= 0.0031308, x*12.92, 1.055*np.power(np.clip(x,0,None),1/2.4)-0.055)

def resize_hq(img, s):
    arr = np.asarray(img).astype(np.float32)/255.0
    rgb = srgb2lin(arr[...,:3]); a = arr[...,3:4]; pre = rgb*a
    ch = [np.asarray(Image.fromarray(pre[...,i].astype(np.float32), "F").resize((s,s), Image.LANCZOS)).astype(np.float32) for i in range(3)]
    al = np.clip(np.asarray(Image.fromarray(a[...,0].astype(np.float32), "F").resize((s,s), Image.LANCZOS)).astype(np.float32), 0, 1)
    pre2 = np.stack(ch, -1)
    rgb2 = np.where(al[...,None] > 1e-4, pre2/np.maximum(al[...,None],1e-4), 0)
    out = np.dstack([lin2srgb(np.clip(rgb2,0,1)), al])
    return Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8), "RGBA")

def add_outline(img, color=INK, a=110):
    al = img.getchannel("A")
    edge = np.clip(np.asarray(al.filter(ImageFilter.MaxFilter(3))).astype(np.int16) - np.asarray(al).astype(np.int16), 0, 255).astype(np.uint8)
    lay = np.zeros((img.size[1], img.size[0], 4), np.uint8)
    lay[...,0],lay[...,1],lay[...,2] = color
    lay[...,3] = (edge.astype(np.float32)*a/255.0).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(lay,"RGBA"), img)

def finalize(master, s, boost=0):
    r = resize_hq(master, s)
    r = add_outline(r, INK, 100)
    if s <= 48: r = r.filter(ImageFilter.UnsharpMask(0.55, 60+boost, 2))
    else: r = r.filter(ImageFilter.UnsharpMask(0.85, 30, 2))
    return r

def dib(img):
    w,h = img.size; px = img.load(); rows=[]
    for y in range(h-1,-1,-1):
        row=bytearray()
        for x in range(w):
            r,g,b,a = px[x,y]; row += bytes((b,g,r,a))
        rows.append(bytes(row))
    xor=b"".join(rows); mask=bytes((((w+31)//32)*4)*h)
    return struct.pack("<IiiHHIIiiII",40,w,h*2,1,32,0,len(xor)+len(mask),0,0,0,0)+xor+mask

def build_cur(entries):
    blobs=[dib(im) for (_,_,im) in entries]
    n=len(entries); out=bytearray(struct.pack("<HHH",0,2,n)); off=6+16*n
    for (s,(hx,hy),im),b in zip(entries,blobs):
        w,h=im.size
        out += struct.pack("<BBBBHHII", w%256,h%256,0,0,hx,hy,len(b),off); off+=len(b)
    for b in blobs: out += b
    return bytes(out)

def build_ani(frames, rate, hotspot):
    n=len(frames)
    ic=[build_cur([(f.size[0], hotspot, f)]) for f in frames]
    w,h=frames[0].size
    anih=struct.pack("<IIIIIIIII",36,n,n,w,h,32,1,rate,1)
    body=b"anih"+struct.pack("<I",36)+anih
    body+=b"rate"+struct.pack("<I",4*n)+struct.pack("<%dI"%n,*([rate]*n))
    body+=b"seq "+struct.pack("<I",4*n)+struct.pack("<%dI"%n,*range(n))
    fram=b"".join(b"icon"+struct.pack("<I",len(x))+x for x in ic)
    body+=b"LIST"+struct.pack("<I",len(fram)+4)+b"fram"+fram
    return b"RIFF"+struct.pack("<I",len(body)+4)+b"ACON"+body
