
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

src = Image.open(r"D:\deepseek\out\art\wall_s2.jpg").convert("RGB")
w,h = src.size
box = (int(w*0.140), int(h*0.095), int(w*0.815), int(h*0.845))
crop = src.crop(box); cw, ch = crop.size
g = np.asarray(crop.convert("L")).astype(np.float32)/255.0
bg = np.asarray(Image.fromarray((g*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(cw,ch)*0.08))).astype(np.float32)/255.0
bg = np.maximum(bg,0.25); norm = np.clip(g/bg,0,1.25)
ink = np.clip((1.0-norm)*1.35,0,1)**0.85; ink[ink<0.06]=0
A = Image.fromarray((ink*255).astype(np.uint8)).resize((cw*4,ch*4), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.1))
alpha = np.asarray(A).astype(np.float32)/255.0
W,H = cw*4, ch*4
paper = Image.new("RGBA",(W,H),(244,239,228,255)); pa=np.asarray(paper).astype(np.float32)
rng=np.random.RandomState(9); yy,xx=np.mgrid[0:H,0:W]
fib = rng.normal(0,2.2,(H,W)) + 1.6*np.sin(xx*0.13) + 1.4*np.sin(yy*0.07)
for k,f in enumerate((1.0,1.0,1.15)): pa[...,k]=np.clip(pa[...,k]+fib*f,0,255)
wash=np.clip((1.0-norm)*0.32,0,1)
Wash=Image.fromarray((wash*255).astype(np.uint8)).resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(6))
wsh=np.asarray(Wash).astype(np.float32)/255.0
for k in range(3): pa[...,k]=np.clip(pa[...,k]*(1-0.55*wsh),0,255)
img=Image.fromarray(pa.astype(np.uint8),"RGBA")
lay=np.zeros((H,W,4),np.uint8); lay[...,0],lay[...,1],lay[...,2]=26,30,28
lay[...,3]=(alpha*250).astype(np.uint8)
img=Image.alpha_composite(img, Image.fromarray(lay,"RGBA"))
d=ImageDraw.Draw(img)
sx,sy,ss=int(W*0.15),int(H*0.05),int(W*0.042)
d.rectangle([sx,sy,sx+ss,sy+ss], fill=(176,52,44,225))
d.rectangle([sx+int(ss*0.14),sy+int(ss*0.14),sx+int(ss*0.86),sy+int(ss*0.86)], outline=(250,238,232,190), width=max(1,int(W*0.0015)))
img.convert("RGB").save(r"D:\deepseek\out\scroll-assets\13_提灯龙_修复版.png")
img.convert("RGB").resize((W//2,H//2), Image.LANCZOS).save(r"D:\deepseek\out\art\scroll\final_lantern.jpg", quality=92)
print("out", img.size)
