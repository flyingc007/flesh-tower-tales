import math, random, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps
import numpy as np

random.seed(20261020)
W, H = 2560, 1440
SS = 2
RW, RH = W*SS, H*SS
OUT = '麒麟_电影概念图_03.png'

def S(*args):
    vals=tuple(int(v*SS) for v in args)
    return vals[0] if len(vals)==1 else vals


def scaled_pts(points):
    return [(int(x*SS), int(y*SS)) for x,y in points]

def catmull(points, samples=16, closed=True):
    p = list(points)
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [p[0]] + p + [p[-1]]
    out=[]
    for i in range(1, len(p)-2):
        p0,p1,p2,p3 = p[i-1],p[i],p[i+1],p[i+2]
        for j in range(samples):
            t=j/samples
            t2=t*t; t3=t2*t
            x=0.5*((2*p1[0])+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y=0.5*((2*p1[1])+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x,y))
    if not closed:
        out.append(points[-1])
    return out

def smooth_poly(draw, points, fill=None, outline=None, width=1, samples=16, closed=True):
    q=catmull(points, samples, closed)
    qq=scaled_pts(q)
    if fill is not None:
        draw.polygon(qq, fill=fill)
    if outline is not None:
        draw.line(qq + ([] if closed else []), fill=outline, width=max(1,int(width*SS)), joint='curve')
        if closed: draw.line([qq[-1], qq[0]], fill=outline, width=max(1,int(width*SS)), joint='curve')
    return qq

def bezier(p0,p1,p2,p3,n=80):
    out=[]
    for i in range(n+1):
        t=i/n; u=1-t
        x=u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0]
        y=u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]
        out.append((x,y))
    return out

def stroke(draw, pts, fill, width=1, joint='curve'):
    draw.line(scaled_pts(pts), fill=fill, width=max(1,int(width*SS)), joint=joint)

def vertical_gradient(w,h, top, bottom):
    a=np.array(top,dtype=np.float32); b=np.array(bottom,dtype=np.float32)
    t=np.linspace(0,1,h,dtype=np.float32)[:,None,None]
    arr=(a[None,None,:]*(1-t)+b[None,None,:]*t)
    arr=np.repeat(arr,w,axis=1)
    return Image.fromarray(np.uint8(np.clip(arr,0,255)), 'RGB')

def add_glow(base, mask, color, blur, opacity=1.0):
    solid=Image.new('RGBA', base.size, tuple(color[:3])+(0,))
    solid.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)).point(lambda v:int(v*opacity)))
    return Image.alpha_composite(base, solid)

def radial_glow(base, cx, cy, radius, color, opacity=150):
    layer=Image.new('RGBA', base.size, (0,0,0,0))
    pix=layer.load()
    x0=max(0,int(cx-radius)); x1=min(base.width,int(cx+radius)); y0=max(0,int(cy-radius)); y1=min(base.height,int(cy+radius))
    # Use resized radial mask for speed
    m=Image.new('L',(512,512),0); md=ImageDraw.Draw(m)
    for i in range(50,0,-1):
        rr=i/50
        a=int(opacity*(1-rr)**2)
        md.ellipse((256-256*rr,256-256*rr,256+256*rr,256+256*rr),fill=a)
    m=m.resize((x1-x0,y1-y0),Image.Resampling.BILINEAR)
    patch=Image.new('RGBA',(x1-x0,y1-y0),color+(0,))
    patch.putalpha(m)
    base.alpha_composite(patch,(x0,y0))
    return base

# ---------- sky ----------
bg = vertical_gradient(RW, RH, (5,10,17), (20,42,47)).convert('RGBA')
# atmospheric color fields
bg = radial_glow(bg, int(0.72*RW), int(0.28*RH), int(0.55*RW), (28,76,85), 88)
bg = radial_glow(bg, int(0.17*RW), int(0.86*RH), int(0.48*RW), (96,54,26), 45)
bg = radial_glow(bg, int(0.75*RW), int(0.30*RH), int(0.20*RW), (170,178,151), 65)

# star dust
stars=Image.new('RGBA',(RW,RH),(0,0,0,0)); sd=ImageDraw.Draw(stars)
for _ in range(650):
    x=random.random()*W; y=random.random()*H*0.64
    a=random.randint(12,75); r=random.choice([0.5,0.5,0.7,1.0,1.4])
    sd.ellipse((int((x-r)*SS),int((y-r)*SS),int((x+r)*SS),int((y+r)*SS)),fill=(190,220,218,a))
bg=Image.alpha_composite(bg,stars)

# moon
moon_layer=Image.new('RGBA',(RW,RH),(0,0,0,0)); md=ImageDraw.Draw(moon_layer)
mx,my,mr=1960,430,215
for rr,a in [(mr*1.7,15),(mr*1.35,25),(mr*1.12,38),(mr,255)]:
    md.ellipse((int((mx-rr)*SS),int((my-rr)*SS),int((mx+rr)*SS),int((my+rr)*SS)),fill=(210,218,199,a))
# moon texture
moon_tex=Image.new('RGBA',(int(mr*2*SS),int(mr*2*SS)),(0,0,0,0)); mtd=ImageDraw.Draw(moon_tex)
for _ in range(110):
    rr=random.uniform(8,55); xx=random.uniform(15,2*mr-15); yy=random.uniform(15,2*mr-15)
    if (xx-mr)**2+(yy-mr)**2 < (mr-10)**2:
        mtd.ellipse(((xx-rr)*SS,(yy-rr)*SS,(xx+rr)*SS,(yy+rr)*SS),fill=(126,137,126,random.randint(5,15)))
mask=Image.new('L',moon_tex.size,0); ImageDraw.Draw(mask).ellipse((5*SS,5*SS,(2*mr-5)*SS,(2*mr-5)*SS),fill=255)
moon_tex.putalpha(ImageChops.multiply(moon_tex.getchannel('A'),mask))
moon_layer.alpha_composite(moon_tex,(int((mx-mr)*SS),int((my-mr)*SS)))
bg=Image.alpha_composite(bg,moon_layer)

# distant mountains helper
def ridge_layer(base, baseline, amp, color, roughness, seed, blur=0):
    rng=random.Random(seed)
    pts=[(0,H+20)]
    for x in range(-50,W+80,24):
        y=baseline + amp*math.sin(x/190+seed) + amp*0.45*math.sin(x/73+seed*2) + rng.uniform(-roughness,roughness)
        pts.append((x,y))
    pts += [(W+20,H+20)]
    layer=Image.new('RGBA',(RW,RH),(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ld.polygon(scaled_pts(pts),fill=color)
    if blur: layer=layer.filter(ImageFilter.GaussianBlur(blur*SS))
    return Image.alpha_composite(base,layer)

bg=ridge_layer(bg,930,95,(15,31,35,215),12,1,1.8)
bg=ridge_layer(bg,1020,120,(10,24,28,225),16,2,1.0)
bg=ridge_layer(bg,1110,80,(6,15,20,245),12,3,0.5)

# cloud sea layers
clouds=Image.new('RGBA',(RW,RH),(0,0,0,0)); cd=ImageDraw.Draw(clouds)
for layer_i,(cy,alpha,blurv) in enumerate([(910,30,18),(985,36,14),(1060,42,11),(1130,50,8)]):
    lg=Image.new('RGBA',(RW,RH),(0,0,0,0)); ld=ImageDraw.Draw(lg)
    for i in range(95):
        x=random.uniform(-150,W+150); y=cy+random.uniform(-70,65)
        rw=random.uniform(90,460); rh=random.uniform(18,74)
        col=(122+(layer_i*8),155+(layer_i*5),155,random.randint(8,alpha))
        ld.ellipse(((x-rw)*SS,(y-rh)*SS,(x+rw)*SS,(y+rh)*SS),fill=col)
    lg=lg.filter(ImageFilter.GaussianBlur(blurv*SS))
    clouds=Image.alpha_composite(clouds,lg)
bg=Image.alpha_composite(bg,clouds)

# light rays from moon / upper right
rays=Image.new('RGBA',(RW,RH),(0,0,0,0)); rd=ImageDraw.Draw(rays)
for i in range(13):
    a=random.uniform(-2.55,-1.9)
    spread=random.uniform(0.02,0.06)
    p0=(mx*SS,my*SS)
    p1=((mx+math.cos(a-spread)*3000)*SS,(my-math.sin(a-spread)*3000)*SS)
    p2=((mx+math.cos(a+spread)*3000)*SS,(my-math.sin(a+spread)*3000)*SS)
    rd.polygon([p0,p1,p2],fill=(193,213,190,random.randint(3,10)))
rays=rays.filter(ImageFilter.GaussianBlur(22*SS))
bg=Image.alpha_composite(bg,rays)

# distant temple silhouette on left cliff
temple=Image.new('RGBA',(RW,RH),(0,0,0,0)); td=ImageDraw.Draw(temple)
# cliff
cliff=[(0,1040),(90,1010),(180,1028),(250,980),(330,1010),(390,1110),(470,1160),(410,1240),(0,1260)]
td.polygon(scaled_pts(cliff),fill=(4,11,14,255))
# temple base
td.rectangle(S(165,935,410,1080),fill=(5,12,14,255))
for i,(ww,hh,yy) in enumerate([(260,110,920),(210,95,860),(160,82,805),(115,70,758)]):
    x=215+(260-ww)/2
    td.rectangle(S(x,yy+hh, x+ww,yy+hh+38),fill=(5,12,14,255))
    # curved roof
    roof=[(x-24,yy+hh+8),(x+ww*0.2,yy+hh-12),(x+ww*0.5,yy+hh-25),(x+ww*0.8,yy+hh-12),(x+ww+24,yy+hh+8),(x+ww*0.82,yy+hh+18),(x+ww*0.18,yy+hh+18)]
    td.polygon(scaled_pts(roof),fill=(3,8,10,255))
    # lit windows
    for j in range(3):
        wx=x+ww*(0.32+j*0.16); wy=yy+hh+12
        td.rectangle(S(wx,wy,wx+12,wy+20),fill=(218,135,57,185))
# temple glow
glow=temple.filter(ImageFilter.GaussianBlur(11*SS))
bg=Image.alpha_composite(bg,glow)
bg=Image.alpha_composite(bg,temple)

# generic branches / foreground framing, left and right
frame=Image.new('RGBA',(RW,RH),(0,0,0,0)); fd=ImageDraw.Draw(frame)
for side in ['L','R']:
    if side=='L':
        for i in range(8):
            p=[(-60,1180+i*45),(110,1040+i*35),(220,970+i*40),(380,900+i*52)]
            stroke(fd,p,(2,7,8,230),13-i*0.7)
            stroke(fd,p,(12,26,26,160),2)
    else:
        for i in range(7):
            p=[(W+50,1210+i*38),(2270,1080+i*35),(2140,1010+i*46),(1990,940+i*55)]
            stroke(fd,p,(2,7,8,230),11-i*0.7)
            stroke(fd,p,(12,26,26,150),1.5)
bg=Image.alpha_composite(bg,frame)

# ---------- Qilin silhouette ----------
# Body, neck, head masks
body_pts=[(1115,684),(1220,642),(1390,642),(1545,672),(1680,732),(1770,810),(1782,892),(1715,965),(1585,1015),(1450,1032),(1320,1012),(1210,980),(1150,910),(1118,840),(1080,780)]
neck_pts=[(914,515),(985,485),(1055,510),(1120,575),(1192,660),(1238,758),(1200,858),(1125,890),(1055,833),(1002,738),(954,650)]
head_pts=[(946,390),(1015,390),(1030,430),(998,464),(1012,500),(975,534),(925,555),(866,550),(812,525),(778,505),(762,481),(780,461),(832,453),(854,420),(900,404)]
# legs
leg_front_1=[(1140,840),(1190,846),(1215,940),(1197,1055),(1205,1170),(1190,1275),(1210,1295),(1170,1302),(1150,1278),(1145,1170),(1115,1050),(1098,930)]
leg_front_2=[(1238,850),(1282,860),(1305,950),(1300,1068),(1325,1175),(1360,1260),(1376,1288),(1338,1300),(1318,1275),(1280,1185),(1250,1070),(1218,960)]
leg_rear_1=[(1590,920),(1650,910),(1680,990),(1668,1080),(1664,1170),(1635,1270),(1650,1298),(1610,1305),(1585,1280),(1610,1195),(1595,1100),(1575,1015)]
leg_rear_2=[(1710,900),(1752,905),(1770,980),(1758,1060),(1788,1150),(1818,1245),(1838,1280),(1800,1290),(1778,1262),(1748,1170),(1718,1080),(1690,1000)]
leg_masks=[leg_front_1,leg_front_2,leg_rear_1,leg_rear_2]

qmask=Image.new('L',(RW,RH),0); qmd=ImageDraw.Draw(qmask)
for pts in [body_pts,neck_pts,head_pts]+leg_masks:
    qmd.polygon(scaled_pts(catmull(pts,18,True)),fill=255)
# soften near edges only slightly
qmask_soft=qmask.filter(ImageFilter.GaussianBlur(0.35*SS))

# separation halo behind the creature
halo=Image.new('RGBA',(RW,RH),(0,0,0,0)); had=ImageDraw.Draw(halo)
had.ellipse(S(760,530,1950,1220),fill=(0,5,8,105))
halo=halo.filter(ImageFilter.GaussianBlur(75*SS))
bg=Image.alpha_composite(bg,halo)

# body gradient, carved from dark jade with moonlit upper planes
qfill=Image.new('RGBA',(RW,RH),(0,0,0,0))
arr=np.zeros((RH,RW,3),dtype=np.float32)
yy=np.linspace(0,1,RH,dtype=np.float32)[:,None,None]
arr[:,:,0]=42+112*(1-yy[:,:,0])
arr[:,:,1]=56+119*(1-yy[:,:,0])
arr[:,:,2]=48+96*(1-yy[:,:,0])
qfill=Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB').convert('RGBA')
qfill.putalpha(qmask_soft)
bg=Image.alpha_composite(bg,qfill)

# sculpted body light: shoulder, neck and haunch
muscle=Image.new('RGBA',(RW,RH),(0,0,0,0)); msd=ImageDraw.Draw(muscle)
for box,col in [((1190,690,1510,1040),(64,166,154,92)),((1020,520,1220,870),(78,174,160,78)),((1510,700,1760,990),(182,162,101,42)),((1210,760,1410,940),(213,174,104,38))]:
    msd.ellipse(S(*box),fill=col)
muscle=muscle.filter(ImageFilter.GaussianBlur(35*SS))
muscle.putalpha(ImageChops.multiply(muscle.getchannel('A'),qmask_soft))
bg=Image.alpha_composite(bg,muscle)

# directional body shading
xn=np.linspace(0,1,RW,dtype=np.float32)[None,:]
yn=np.linspace(0,1,RH,dtype=np.float32)[:,None]
sh=np.clip(0.06+0.26*xn+0.18*yn,0,0.46)
shadow=Image.new('RGBA',(RW,RH),(3,13,15,0))
shadow.putalpha(Image.fromarray(np.uint8(sh*255),'L'))
shadow.putalpha(ImageChops.multiply(shadow.getchannel('A'),qmask_soft))
bg=Image.alpha_composite(bg,shadow)

# muscular and skeletal contours
anatomy=Image.new('RGBA',(RW,RH),(0,0,0,0)); and_=ImageDraw.Draw(anatomy)
stroke(and_,bezier((1120,850),(1250,900),(1420,1015),(1650,950),80),(2,14,17,105),5)
stroke(and_,bezier((1260,700),(1380,735),(1430,860),(1360,955),70),(12,39,40,90),3)
stroke(and_,bezier((1540,680),(1640,755),(1700,855),(1630,965),70),(4,19,22,120),4)
stroke(and_,bezier((1240,785),(1325,805),(1390,875),(1420,995),60),(220,190,125,45),2)
stroke(and_,bezier((1470,720),(1550,770),(1600,840),(1610,950),60),(220,190,125,34),2)
anatomy.putalpha(ImageChops.multiply(anatomy.getchannel('A'),qmask_soft))
bg=Image.alpha_composite(bg,anatomy)

# luminous dorsal fins along the spine
fins=Image.new('RGBA',(RW,RH),(0,0,0,0)); fnd=ImageDraw.Draw(fins)
back=catmull([(1195,653),(1360,638),(1530,678),(1695,744),(1770,804)],18,False)
for i in range(13):
    idx=int((0.10+0.70*i/12)*(len(back)-1)); x,y=back[idx]
    h=22+18*math.sin(i*1.7)**2+random.uniform(-4,8)
    w=24+random.uniform(-5,6)
    p=[(x-w*0.62,y+5),(x,y-h),(x+w*0.62,y+4)]
    fnd.polygon(scaled_pts(p),fill=(199,170,103,82))
    stroke(fnd,[(x,y-h),(x+w*0.62,y+4)],(242,207,137,120),1.2)
bg=Image.alpha_composite(bg,fins.filter(ImageFilter.GaussianBlur(0.7*SS)))

# subtle body texture: scanned fur strokes clipped by mask
texture=Image.new('RGBA',(RW,RH),(0,0,0,0)); txd=ImageDraw.Draw(texture)
for _ in range(2200):
    x=random.uniform(1070,1780); y=random.uniform(620,1040)
    ln=random.uniform(12,80); ang=random.uniform(-0.6,0.6)
    p=[(x,y),(x+ln*math.cos(ang),y+ln*math.sin(ang)*0.35),(x+ln*1.5,y+ln*math.sin(ang)*0.55)]
    stroke(txd,p,(108,181,173,random.randint(12,42)),random.uniform(0.6,1.7))
texture.putalpha(ImageChops.multiply(texture.getchannel('A'),qmask_soft))
bg=Image.alpha_composite(bg,texture)

# scales on neck and shoulder, clipped
scales=Image.new('RGBA',(RW,RH),(0,0,0,0)); scd=ImageDraw.Draw(scales)
for row in range(24):
    yy=475+row*17
    for col in range(30):
        xx=960+col*22+(row%2)*11
        rw=12+random.uniform(-2,2); rh=7+random.uniform(-1,2)
        a=int(50+70*(xx/1900))
        scd.arc(((xx-rw)*SS,(yy-rh)*SS,(xx+rw)*SS,(yy+rh)*SS), 200, 340, fill=(111,172,169,a), width=max(1,int(0.8*SS)))
        if random.random()<0.35:
            scd.arc(((xx-rw+2)*SS,(yy-rh+2)*SS,(xx+rw-2)*SS,(yy+rh-2)*SS), 215, 325, fill=(219,187,117,a//2), width=max(1,int(0.55*SS)))
scales.putalpha(ImageChops.multiply(scales.getchannel('A'),qmask_soft))
bg=Image.alpha_composite(bg,scales)

# rim light paths (blur + crisp)
rim=Image.new('RGBA',(RW,RH),(0,0,0,0)); rd=ImageDraw.Draw(rim)
for pts,col,w in [
    (body_pts,(244,194,107,225),7),
    (neck_pts,(131,231,216,230),6),
    (head_pts,(235,201,131,235),5),
]:
    q=catmull(pts,20,True); qq=scaled_pts(q)
    rd.line(qq+[qq[0]],fill=col,width=int(w*SS),joint='curve')
rim_blur=rim.filter(ImageFilter.GaussianBlur(8*SS))
bg=Image.alpha_composite(bg,rim_blur)
bg=Image.alpha_composite(bg,rim.filter(ImageFilter.GaussianBlur(1.2*SS)))

# leg inner light
leglight=Image.new('RGBA',(RW,RH),(0,0,0,0)); lld=ImageDraw.Draw(leglight)
for i,pts in enumerate(leg_masks):
    q=catmull(pts,12,True); qq=scaled_pts(q)
    lld.line(qq+[qq[0]],fill=(170,150,90,36),width=int(2*SS),joint='curve')
    lld.line(qq[int(len(qq)*0.6):]+[qq[0]],fill=(66,128,132,70),width=int(2*SS),joint='curve')
bg=Image.alpha_composite(bg,leglight.filter(ImageFilter.GaussianBlur(1*SS)))

# hooves
hoof=Image.new('RGBA',(RW,RH),(0,0,0,0)); hd=ImageDraw.Draw(hoof)
hooves=[(1160,1288,40,22),(1322,1282,42,24),(1600,1286,42,22),(1788,1274,44,22)]
for x,y,w,h in hooves:
    hd.ellipse(((x-w/2)*SS,(y-h/2)*SS,(x+w/2)*SS,(y+h/2)*SS),fill=(233,186,104,235))
    hd.ellipse(((x-w/2+4)*SS,(y-h/2+4)*SS,(x+w/2-4)*SS,(y+h/2-2)*SS),fill=(21,25,25,255))
    hd.arc(((x-w/2)*SS,(y-h/2)*SS,(x+w/2)*SS,(y+h/2)*SS),185,345,fill=(255,218,150,180),width=int(1.2*SS))
bg=Image.alpha_composite(bg,hoof)

# head details
face=Image.new('RGBA',(RW,RH),(0,0,0,0)); fd=ImageDraw.Draw(face)
# jaw/mouth
jaw=bezier((795,480),(845,515),(905,522),(955,500),80)
stroke(fd,jaw,(3,8,9,245),5)
stroke(fd,[(x,y+2) for x,y in jaw],(180,137,78,80),1.2)
# nostril
stroke(fd,[(746,472),(765,466),(778,474)],(229,179,93,210),2.2)
# eye socket + amber eye
fd.ellipse(S(820,423,856,446),fill=(2,7,8,255))
fd.ellipse(S(826,427,851,444),fill=(238,155,42,255))
fd.ellipse(S(831,430,847,442),fill=(255,213,96,255))
fd.ellipse(S(838,429,843,443),fill=(17,12,8,255))
# eye glow
eye_glow=Image.new('L',(RW,RH),0); egd=ImageDraw.Draw(eye_glow); egd.ellipse(S(815,418,860,450),fill=220)
bg=add_glow(bg,eye_glow,(255,168,52,255),7*SS,0.95)
bg=Image.alpha_composite(bg,face)
# brow ridge
stroke(fd,[(806,416),(829,405),(858,410),(872,421)],(204,174,109,160),3)
# cheek scales
for i in range(7):
    x=842+i*13; y=463+i*3
    fd.arc(S(x,y,x+18,y+11),200,340,fill=(124,184,171,110),width=int(0.8*SS))
# fangs
fd.polygon(scaled_pts([(800,486),(808,498),(812,486)]),fill=(229,217,183,225))
fd.polygon(scaled_pts([(830,492),(838,504),(842,491)]),fill=(229,217,183,205))

# nose bridge ornate ridge
ridge=bezier((770,462),(815,430),(885,395),(951,396),100)
stroke(fd,ridge,(229,190,112,110),4)
stroke(fd,[(x,y-2) for x,y in ridge],(99,190,183,55),1)
for t in [0.18,0.36,0.55,0.72,0.86]:
    i=int(t*(len(ridge)-1)); x,y=ridge[i]
    fd.polygon(scaled_pts([(x-7,y-4),(x,y-18),(x+7,y-4),(x,y+2)]),fill=(219,183,112,135))

# ear
ear=[(985,406),(1036,375),(1048,399),(1022,432),(997,438)]
smooth_poly(fd,ear,fill=(8,20,22,255),outline=(208,168,101,130),width=2,samples=12)
stroke(fd,[(1002,409),(1022,394),(1033,391)],(140,84,58,100),1.5)

# whiskers
wh=Image.new('RGBA',(RW,RH),(0,0,0,0)); whd=ImageDraw.Draw(wh)
for i in range(15):
    sy=480+i*2.2
    p0=(770,sy)
    p1=(690-i*3,500+i*7)
    p2=(600-i*7,470+i*18)
    p3=(470-i*10,520+i*26)
    q=bezier(p0,p1,p2,p3,70)
    stroke(whd,q,(229,194,126,random.randint(45,105)),random.uniform(0.7,1.7))
bg=Image.alpha_composite(bg,wh.filter(ImageFilter.GaussianBlur(0.8*SS)))
bg=Image.alpha_composite(bg,wh)

# central horn and nose horn
horn=Image.new('RGBA',(RW,RH),(0,0,0,0)); hnd=ImageDraw.Draw(horn)
stroke(hnd,[(853,420),(870,374),(890,337),(906,318)],(236,194,115,225),7)
stroke(hnd,[(870,374),(898,358),(922,348)],(221,183,108,180),4)
stroke(hnd,[(892,340),(917,330),(942,326)],(219,181,108,150),3)
stroke(hnd,[(772,474),(753,447),(744,423)],(223,188,116,170),3)
bg=Image.alpha_composite(bg,horn.filter(ImageFilter.GaussianBlur(0.8*SS)))
bg=Image.alpha_composite(bg,horn)

# antlers recursive
antlers=Image.new('RGBA',(RW,RH),(0,0,0,0)); ad=ImageDraw.Draw(antlers)
def antler(x,y,ang,length,width,depth):
    if depth<=0 or length<14:
        return
    x2=x+math.cos(ang)*length; y2=y+math.sin(ang)*length
    mx=(x+x2)/2+math.cos(ang+math.pi/2)*random.uniform(-10,10)
    my=(y+y2)/2+math.sin(ang+math.pi/2)*random.uniform(-10,10)
    q=bezier((x,y),(mx,my),(mx,my),(x2,y2),20)
    stroke(ad,q,(226,197,145,180),width)
    stroke(ad,q,(80,106,100,100),max(1,width-2))
    if depth>1:
        antler(x2,y2,ang-random.uniform(0.42,0.78),length*random.uniform(0.52,0.68),width*0.72,depth-1)
        antler(x2,y2,ang+random.uniform(0.38,0.72),length*random.uniform(0.48,0.65),width*0.68,depth-1)
# main beams
for start,ang,L,dep in [((946,393),-1.50,105,4),((922,380),-1.78,115,4),((974,405),-1.28,92,3)]:
    antler(start[0],start[1],ang,L,7,dep)
bg=Image.alpha_composite(bg,antlers.filter(ImageFilter.GaussianBlur(4*SS)))
bg=Image.alpha_composite(bg,antlers)

# mane: long strands around neck/head, windblown left
mane=Image.new('RGBA',(RW,RH),(0,0,0,0)); mnd=ImageDraw.Draw(mane)
mane_glow=Image.new('RGBA',(RW,RH),(0,0,0,0)); mgd=ImageDraw.Draw(mane_glow)
starts=[]
for i in range(46):
    t=i/45
    x=940+40*math.sin(t*8)+random.uniform(-22,22)
    y=420+t*240+random.uniform(-28,28)
    starts.append((x,y))
for i in range(280):
    sx,sy=random.choice(starts)
    sy+=random.uniform(-30,30)
    amp=random.uniform(60,230)
    q=[
      (sx,sy),
      (sx-40-random.uniform(0,80),sy+random.uniform(-20,70)),
      (sx-120-random.uniform(0,180),sy+random.uniform(-70,100)),
      (sx-amp-random.uniform(20,230),sy+random.uniform(-80,140)),
    ]
    curve=bezier(*q,50)
    col=random.choice([(143,208,194,random.randint(20,70)),(217,177,102,random.randint(15,55)),(38,100,106,random.randint(30,100)),(6,24,28,random.randint(40,110))])
    stroke(mnd,curve,col,random.uniform(0.6,2.4))
    if random.random()<0.18:
        stroke(mgd,[(x,y) for x,y in curve[-12:]],(255,203,120,random.randint(20,55)),random.uniform(1,3))
mane=mane.filter(ImageFilter.GaussianBlur(0.55*SS))
bg=Image.alpha_composite(bg,mane_glow.filter(ImageFilter.GaussianBlur(5*SS)))
bg=Image.alpha_composite(bg,mane)
bg=Image.alpha_composite(bg,mane_glow)

# fur edge strokes along back/neck
fur=Image.new('RGBA',(RW,RH),(0,0,0,0)); furd=ImageDraw.Draw(fur)
back_line=catmull([(1000,555),(1060,650),(1120,740),(1190,640),(1390,640),(1580,690),(1740,785)],14,False)
for i in range(220):
    t=random.random(); idx=min(len(back_line)-1,int(t*(len(back_line)-1))); x,y=back_line[idx]
    ln=random.uniform(8,34); ang=random.uniform(-2.1,-0.8)
    q=bezier((x,y),(x+ln*0.3,y+ln*0.15),(x+ln*0.7,y+ln*0.25),(x+ln,y+ln*0.5),12)
    stroke(furd,q,(65,137,139,random.randint(18,65)),random.uniform(0.6,1.8))
    if random.random()<0.24: stroke(furd,q,(228,188,113,random.randint(12,38)),random.uniform(0.5,1.3))
bg=Image.alpha_composite(bg,fur)

# tail: plume sweeping right
tail=Image.new('RGBA',(RW,RH),(0,0,0,0)); tld=ImageDraw.Draw(tail)
tail_glow=Image.new('RGBA',(RW,RH),(0,0,0,0)); tgd=ImageDraw.Draw(tail_glow)
for i in range(170):
    t=random.random()
    x0=1740+60*t; y0=830+90*t+random.uniform(-25,25)
    q=[(x0,y0),(x0+80+random.uniform(0,120),y0-40-random.uniform(0,80)),(x0+180+random.uniform(0,170),y0-120-random.uniform(0,150)),(x0+300+random.uniform(0,220),y0-100-random.uniform(0,240))]
    curve=bezier(*q,45)
    col=random.choice([(17,55,59,random.randint(35,110)),(41,113,111,random.randint(20,80)),(196,159,91,random.randint(12,45)),(6,19,22,random.randint(45,100))])
    stroke(tld,curve,col,random.uniform(0.8,3.0))
    if random.random()<0.16: stroke(tgd,[(x,y) for x,y in curve[-18:]],(255,195,104,28),random.uniform(1,3))
bg=Image.alpha_composite(bg,tail.filter(ImageFilter.GaussianBlur(0.7*SS)))
bg=Image.alpha_composite(bg,tail_glow.filter(ImageFilter.GaussianBlur(5*SS)))

# hoof flame wisps
flame=Image.new('RGBA',(RW,RH),(0,0,0,0)); fld=ImageDraw.Draw(flame)
for hx,hy in [(1160,1288),(1322,1282),(1600,1286),(1788,1274)]:
    for k in range(12):
        dx=random.uniform(-35,35); h=random.uniform(35,100)
        q=bezier((hx+dx,hy),(hx+dx-20,hy-h*0.35),(hx+dx+18,hy-h*0.65),(hx+dx+random.uniform(-35,35),hy-h),30)
        stroke(fld,q,(244,176,81,random.randint(20,70)),random.uniform(0.8,2.5))
bg=Image.alpha_composite(bg,flame.filter(ImageFilter.GaussianBlur(4*SS)))
bg=Image.alpha_composite(bg,flame)

# foreground rock and mist
fg=Image.new('RGBA',(RW,RH),(0,0,0,0)); fgd=ImageDraw.Draw(fg)
rock=[(850,1300),(950,1250),(1050,1270),(1110,1240),(1200,1290),(1300,1255),(1410,1280),(1500,1245),(1600,1270),(1690,1230),(1810,1280),(1940,1290),(2040,1440),(760,1440)]
fgd.polygon(scaled_pts(rock),fill=(3,9,11,255))
for i in range(20):
    x=random.uniform(850,1980); y=random.uniform(1270,1410); rw=random.uniform(30,160); rh=random.uniform(8,35)
    fgd.ellipse(((x-rw)*SS,(y-rh)*SS,(x+rw)*SS,(y+rh)*SS),fill=(random.randint(12,25),random.randint(27,40),random.randint(29,42),random.randint(20,70)))
# ground rim
fgd.line(scaled_pts([(850,1300),(950,1250),(1050,1270),(1110,1240),(1200,1290),(1300,1255),(1410,1280),(1500,1245),(1600,1270),(1690,1230),(1810,1280),(1940,1290)]),fill=(184,144,78,100),width=int(2*SS),joint='curve')
bg=Image.alpha_composite(bg,fg)

# low mist
mist=Image.new('RGBA',(RW,RH),(0,0,0,0)); mid=ImageDraw.Draw(mist)
for i in range(90):
    x=random.uniform(-200,W+200); y=random.uniform(1180,1335); rw=random.uniform(80,340); rh=random.uniform(12,60)
    mid.ellipse(((x-rw)*SS,(y-rh)*SS,(x+rw)*SS,(y+rh)*SS),fill=(129,166,162,random.randint(5,22)))
bg=Image.alpha_composite(bg,mist.filter(ImageFilter.GaussianBlur(16*SS)))

# embers
embers=Image.new('RGBA',(RW,RH),(0,0,0,0)); ed=ImageDraw.Draw(embers)
for i in range(130):
    x=random.uniform(600,2200); y=random.uniform(360,1300); r=random.uniform(0.6,3.2)
    a=random.randint(30,130)
    ed.ellipse(((x-r)*SS,(y-r)*SS,(x+r)*SS,(y+r)*SS),fill=(245,164,70,a))
bg=Image.alpha_composite(bg,embers.filter(ImageFilter.GaussianBlur(3*SS)))
bg=Image.alpha_composite(bg,embers.filter(ImageFilter.GaussianBlur(0.5*SS)))

# subtle top mist/haze
haze=Image.new('RGBA',(RW,RH),(0,0,0,0)); hzd=ImageDraw.Draw(haze)
for i in range(12):
    x=random.uniform(-300,W+300); y=random.uniform(100,800); rw=random.uniform(300,800); rh=random.uniform(60,220)
    hzd.ellipse(((x-rw)*SS,(y-rh)*SS,(x+rw)*SS,(y+rh)*SS),fill=(74,111,111,random.randint(2,8)))
bg=Image.alpha_composite(bg,haze.filter(ImageFilter.GaussianBlur(40*SS)))

# ---------- finish / cinematic grade ----------
img=bg.convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
arr=np.asarray(img).astype(np.float32)/255.0
# gentle teal/orange split tone
lum=arr.mean(axis=2,keepdims=True)
shadow=np.clip((0.58-lum)/0.58,0,1); high=np.clip((lum-0.45)/0.55,0,1)
arr=arr + shadow*np.array([-0.010,0.012,0.020],dtype=np.float32) + high*np.array([0.035,0.012,-0.012],dtype=np.float32)
# filmic S-curve
arr=np.clip(arr,0,1); arr=arr*arr*(3-2*arr)*0.72+arr*0.28
# vignette
xx=np.linspace(-1,1,W,dtype=np.float32)[None,:]; yy=np.linspace(-1,1,H,dtype=np.float32)[:,None]
vig=np.clip(1-0.33*(xx*xx*0.72+yy*yy*0.85),0.48,1)[:,:,None]
arr*=vig
img=Image.fromarray(np.uint8(np.clip(arr,0,1)*255),'RGB')

# bloom highlights
arrf=np.asarray(img).astype(np.float32)/255.0
bright=np.clip((arrf.max(axis=2)-0.63)/0.37,0,1)
bloom=(arrf*np.clip(bright[:,:,None],0,1)*255).astype(np.uint8)
bloom=Image.fromarray(bloom,'RGB').filter(ImageFilter.GaussianBlur(14))
img=ImageChops.screen(img,bloom.point(lambda v:int(v*0.36)))

# grain
arr=np.asarray(img).astype(np.int16)
rng=np.random.default_rng(20261020)
noise=rng.normal(0,3.0,(H,W,1)).repeat(3,axis=2)
arr=np.clip(arr+noise.astype(np.int16),0,255).astype(np.uint8)
img=Image.fromarray(arr,'RGB')

# subtle chromatic aberration at edges
r,g,b=img.split()
r=ImageChops.offset(r,-1,0); b=ImageChops.offset(b,1,0)
img=Image.merge('RGB',(r,g,b))

# paper/canvas microtexture
tex=rng.normal(0,1.2,(H//2,W//2,1)).repeat(3,axis=2)
tex=np.uint8(np.clip(128+tex,0,255))
tex=Image.fromarray(tex,'RGB').resize((W,H),Image.Resampling.BILINEAR)
img=Image.blend(img,ImageChops.add(img,tex,-128),0.035)
img.save(OUT,quality=95)
print(OUT)
print(img.size)





