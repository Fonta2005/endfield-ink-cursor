
import os, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = r"D:\deepseek\out\scroll-assets"
art = Image.open(os.path.join(OUT,"13_提灯龙_修复版.png")).convert("RGB")
aw, ah = art.size
art = art.crop((int(aw*0.06), int(ah*0.03), int(aw*0.895), int(ah*0.97)))

M = 2048
PAPER=(243,238,227); WOOD=(52,42,36); WOOD2=(28,22,19); JADE=(104,222,214)
cx = M//2
pw = int(M*0.400); ph = int(M*0.905)
py0 = int(M*0.0475)
roll_r = int(M*0.019)
BOW = int(0.026*M)                     # bow amplitude in px
pad = BOW + 4
W2 = pw + 2*pad
px0 = cx - W2//2

pa = np.zeros((ph,W2,4), np.float32)
pa[...,0],pa[...,1],pa[...,2]=PAPER; pa[...,3]=255
rng=np.random.RandomState(4); noise=rng.normal(0,3.0,(ph,W2))
for k,f in enumerate((1.0,1.0,1.15)): pa[...,k]=np.clip(pa[...,k]+noise*f,0,255)

aw2,ah2=art.size
iw=int(pw*0.92); ih=int(iw*ah2/aw2)
big=art.resize((iw*2,ih*2),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2.0,110,3))
g=np.asarray(big.convert("L")).astype(np.float32)/255.0
g=np.clip((g-0.5)*1.10+0.5,0,1)
bg=np.asarray(Image.fromarray((g*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(iw*0.10))).astype(np.float32)/255.0
bg=np.maximum(bg,0.25)
ink=np.clip((1.0-(g/bg))*1.32,0,1)**0.88; ink[ink<0.04]=0
ink=np.asarray(Image.fromarray((ink*255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3))).astype(np.float32)/255.0
ink=ink.reshape(ih,2,iw,2).mean(axis=(1,3))
iy,ix=ink.shape
yy,xx=np.mgrid[0:iy,0:ix]
fx=np.clip(np.minimum(xx,ix-1-xx)/(ix*0.18),0,1); fy=np.clip(np.minimum(yy,iy-1-yy)/(iy*0.10),0,1)
ink*=(fx*fy)**0.6
ox=(W2-ix)//2; oy=(ph-ih)//2
reg=pa[oy:oy+iy,ox:ox+ix,:3]; reg*=(1.0-0.94*ink[...,None]); pa[oy:oy+iy,ox:ox+ix,:3]=reg

# bow, without clipping (array is wider by 2*pad)
t=np.linspace(0,1,ph); shift=(BOW*np.sin(np.pi*t)-BOW/1e9).astype(int)
warp=np.zeros_like(pa)
for y in range(ph):
    s=int(shift[y])
    if s>=0: warp[y,s:,:]=pa[y,:W2-s,:]
    else:    warp[y,:W2+s,:]=pa[y,-s:,:]
grad=np.gradient(shift.astype(np.float32))
shade=1.0+np.clip(grad,-3,3)[:,None,None]*0.006
warp[...,:3]=np.clip(warp[...,:3]*shade,0,255)
paper=Image.fromarray(np.clip(warp,0,255).astype(np.uint8),"RGBA")

master=Image.new("RGBA",(M,M),(0,0,0,0))
sh=Image.new("RGBA",(M,M),(0,0,0,0)); ds=ImageDraw.Draw(sh)
ds.rectangle([px0+14,py0+18,px0+W2+12,py0+ph+20], fill=(0,0,0,70)); sh=sh.filter(ImageFilter.GaussianBlur(20))
master.alpha_composite(sh); master.paste(paper,(px0,py0),paper)

d=ImageDraw.Draw(master)
roll_x0, roll_x1 = cx-int(M*0.282), cx+int(M*0.282)
def roller(y):
    d.rounded_rectangle([roll_x0,y-roll_r,roll_x1,y+roll_r],radius=roll_r,fill=WOOD+(255,))
    d.rounded_rectangle([roll_x0,y-roll_r,roll_x1,y-int(roll_r*0.20)],radius=roll_r//2,fill=(84,71,60,255))
    d.rounded_rectangle([roll_x0+6,y+int(roll_r*0.32),roll_x1-6,y+roll_r-2],radius=roll_r//2,fill=(36,30,25,255))
    for x in (roll_x0,roll_x1):
        d.ellipse([x-roll_r*1.28,y-roll_r*1.18,x+roll_r*1.28,y+roll_r*1.18],fill=WOOD2+(255,))
        d.ellipse([x-roll_r*0.74,y-roll_r*0.66,x+roll_r*0.74,y+roll_r*0.66],fill=(68,57,49,255))
        d.ellipse([x-roll_r*0.30,y-roll_r*0.26,x+roll_r*0.30,y+roll_r*0.26],fill=(98,84,72,255))
    for x in (roll_x0+int(M*0.060), roll_x1-int(M*0.060)):
        d.ellipse([x-9,y-9,x+9,y+9],fill=JADE+(232,)); d.ellipse([x-3,y-3,x+3,y+3],fill=(228,255,252,235))
roller(py0); roller(py0+ph)
d.line([(cx,0),(cx,py0-roll_r)],fill=(64,56,48,235),width=9)
d.ellipse([cx-16,0,cx+16,30],fill=(64,56,48,245))
master.save(os.path.join(OUT,"14_画卷_立轴_2K.png"))

def dib(img):
    w,h=img.size; px=img.load(); rows=[]
    for y in range(h-1,-1,-1):
        row=bytearray()
        for x in range(w):
            r,g,b,a=px[x,y]; row+=bytes((b,g,r,a))
        rows.append(bytes(row))
    xor=b"".join(rows); mask=bytes((((w+31)//32)*4)*h)
    return struct.pack("<IiiHHIIiiII",40,w,h*2,1,32,0,len(xor)+len(mask),0,0,0,0)+xor+mask
def build_cur(entries):
    blobs=[dib(im) for (_,_,im) in entries]; n=len(entries)
    out=bytearray(struct.pack("<HHH",0,2,n)); off=6+16*n
    for (s,(hx,hy),im),b in zip(entries,blobs):
        w,h=im.size; out+=struct.pack("<BBBBHHII",w%256,h%256,0,0,hx,hy,len(b),off); off+=len(b)
    for b in blobs: out+=b
    return bytes(out)
entries=[]
for s in (32,40,48,64,96,128,256):
    im=master.resize((s,s),Image.LANCZOS)
    if s<=64: im=im.filter(ImageFilter.UnsharpMask(0.6,85,2))
    entries.append((s,(s//2,s//2),im))
open(os.path.join(OUT,"ScrollText.cur"),"wb").write(build_cur(entries))
print("ok")
