
# -*- coding: utf-8 -*-
import sys, os, math
sys.path.insert(0, r"D:\deepseek\out")
from artlib import *
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(ROOT, "si-cursor")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "source"), exist_ok=True)

def v_normal(dot=True, frame=0, n=1):
    return core_art(dot=dot, arc=False, frame=frame, n=n, flow=1.0 if n > 1 else 0.55)

def v_help(dot=True, frame=0, n=1):
    c = core_art(dot=dot, arc=False, frame=frame, n=n, flow=0.7); d = ImageDraw.Draw(c)
    cx, cy, r = 48*U, 50*U, 12.4*U
    d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(6,10,9,242), outline=GOLD+(246,), width=max(2,int(1.3*U)))
    d.ellipse([cx-r*0.82,cy-r*0.82,cx+r*0.82,cy+r*0.82], outline=PALE+(90,), width=max(1,int(0.6*U)))
    f = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", int(20*U))
    d.text((cx, cy-0.4*U), "?", font=f, fill=PALE+(255,), anchor="mm")
    return c

def v_unavailable(dot=True, frame=0, n=1):
    c = core_art(dot=dot, arc=False, frame=frame, n=n, flow=0.35)
    grey = c.convert("LA").convert("RGBA")
    flat = Image.new("RGBA",(M,M),(0,0,0,0)); flat.paste(grey,(0,0),grey)
    c = Image.blend(c, flat, 0.5)
    d = ImageDraw.Draw(c)
    cx, cy, r = 29*U, 31*U, 17.6*U
    d.ellipse([cx-r,cy-r,cx+r,cy+r], outline=RED+(240,), width=max(3,int(3.0*U)))
    d.line([cx-r*0.65,cy+r*0.65,cx+r*0.65,cy-r*0.65], fill=RED+(240,), width=max(3,int(3.0*U)))
    return c

def v_link(dot=True, frame=0, n=1):
    # smaller pointer for links: short brush, no big ring, just a tight hotspot halo
    c = core_art(dot=dot, arc=False, frame=frame, n=n, mist=0.55, flow=0.7,
                 blen=22.5, tip=(4.2, 4.2), center=(14.6, 15.2), dotpos=(5.4, 5.4))
    cx, cy, R = 5.4*U, 5.4*U, 3.6*U
    c = Image.alpha_composite(c, radial(cx, cy, R*2.4, JADE, 85, 2.6))
    d = ImageDraw.Draw(c)
    d.arc([cx-R, cy-R, cx+R, cy+R], 200, 340, fill=PALE+(225,), width=max(1, int(0.6*U)))
    return c

def v_text(dot=False, frame=0, n=1):
    # compact I-beam: ~18px tall at 32px cursor, slim shaft
    c = layer(); x = M//2; top, bot = 9.5*U, 54.5*U
    c = Image.alpha_composite(c, radial(x, top, 6.0*U, JADE, 95, 2.2))
    c = Image.alpha_composite(c, radial(x, bot, 6.0*U, JADE, 95, 2.2))
    d = ImageDraw.Draw(c); w = 2.45*U
    d.rounded_rectangle([x-w, top, x+w, bot], radius=w, fill=(5,8,7,240))
    d.rounded_rectangle([x-w*0.38, top+2.0*U, x+w*0.38, bot-2.0*U], radius=w*0.38, fill=(52,66,60,200))
    d.rounded_rectangle([x-w, top, x+w, top+0.85*U], radius=0.42*U, fill=PALE+(225,))
    d.rounded_rectangle([x-w, bot-0.85*U, x+w, bot], radius=0.42*U, fill=PALE+(225,))
    return c

def v_precision(dot=False, frame=0, n=1):
    cx = cy = M//2; gap, ln = 5.6*U, 20.4*U
    c = radial(cx,cy,12*U,JADE,90,2.4)
    d = ImageDraw.Draw(c)
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        d.line([cx+dx*gap,cy+dy*gap,cx+dx*ln,cy+dy*ln], fill=(6,9,8,246), width=int(3.2*U))
        d.line([cx+dx*(gap+1*U),cy+dy*(gap+1*U),cx+dx*(ln-3*U),cy+dy*(ln-3*U)], fill=PALE+(135,), width=max(2,int(1.0*U)))
    r = 2.7*U; d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(6,10,9,235))
    r2 = 1.7*U; d.ellipse([cx-r2,cy-r2,cx+r2,cy+r2], fill=PALE+(252,))
    return c

def v_handwriting(dot=True, frame=0, n=1):
    c = core_art(dot=dot, arc=False, frame=frame, n=n, flow=0.7)
    blot = layer(); db = ImageDraw.Draw(blot)
    db.ellipse([DOT[0]*U-3*U, DOT[1]*U+1*U, DOT[0]*U+4.4*U, DOT[1]*U+6.4*U], fill=INK+(120,))
    blot = blot.filter(ImageFilter.GaussianBlur(2.2))
    c = Image.alpha_composite(c, blot)
    return c

SIZES=[32,40,48,64,96,128]
STATIC=[("NormalSelect.cur", v_normal, (4,4), "normal"),
        ("HelpSelect.cur", v_help, (4,4), "help"),
        ("PrecisionSelect.cur", v_precision, (16,16), "precision"),
        ("TextSelect.cur", v_text, (16,16), "text"),
        ("Handwriting.cur", v_handwriting, (4,4), "handwriting"),
        ("Unavailable.cur", v_unavailable, (16,16), "unavailable"),
        ("LinkSelect.cur", v_link, (4,4), "link")]

for fn, f, hs, tag in STATIC:
    md = f(True); mp = f(False)
    md.save(os.path.join(OUT,"source",f"m_{tag}_dot.png"))
    mp.save(os.path.join(OUT,"source",f"m_{tag}.png"))
    entries=[]
    for s in SIZES:
        m = md if s <= 48 else mp
        entries.append((s,(int(round(hs[0]*s/32)), int(round(hs[1]*s/32))), finalize(m, s)))
    open(os.path.join(OUT,fn),"wb").write(build_cur(entries))
    print("cur", fn)

N=16
frames=[]
for i in range(N):
    fr = core_art(dot=True, arc=False, frame=i, n=N)
    fr.save(os.path.join(OUT,"source",f"anim_{i:02d}.png"))
    frames.append(finalize(fr, 64))
open(os.path.join(OUT,"NormalSelect.ani"),"wb").write(build_ani(frames, 8, (8,8)))

# busy: rotating ink ring around the brush centre
def busy_frame(i, n=10):
    c = core_art(dot=True, arc=False, frame=i, n=16)
    cx, cy = 15.5*U, 16.5*U
    lay = Image.new("L", (M,M), 0); d = ImageDraw.Draw(lay)
    R = 15.0*U; a0 = i/n*360.0
    d.arc([cx-R, cy-R*0.92, cx+R, cy+R*0.92], a0, a0+110, fill=255, width=int(2.2*U))
    d.arc([cx-R, cy-R*0.92, cx+R, cy+R*0.92], a0+175, a0+240, fill=200, width=int(1.6*U))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    pale = np.zeros((M,M,4), np.uint8); pale[...,0],pale[...,1],pale[...,2] = PALE
    pale[...,3] = (np.asarray(lay).astype(np.float32)*0.95).astype(np.uint8)
    return Image.alpha_composite(c, Image.fromarray(pale,"RGBA"))

def work_frame(i, n=8):
    c = core_art(dot=True, arc=False, frame=i*2, n=16)
    cx, cy = 15.5*U, 16.5*U
    a = i/n*math.tau
    for k in range(n):
        aa = a - k*0.34
        px, py = cx+math.cos(aa)*13.5*U, cy+math.sin(aa)*13.5*U*0.95
        rr = (3.4*U)*(1-k/n)
        if rr < 2: continue
        c = Image.alpha_composite(c, radial(px, py, rr*2.2, PALE, int(210*(1-k/n)), 2.0))
    return c

for name, fn, nf, rate in (("Busy", busy_frame, 10, 6), ("WorkinginBackground", work_frame, 8, 8)):
    fr = [finalize(fn(i), 64) for i in range(nf)]
    for i,f in enumerate(fr): f.save(os.path.join(OUT,"source",f"{name.lower()}_{i:02d}.png"))
    open(os.path.join(OUT, name + ".ani"),"wb").write(build_ani(fr, rate, (8,8)))
    print("ani", name, os.path.getsize(os.path.join(OUT, name + ".ani")))
print("BUILD OK")
