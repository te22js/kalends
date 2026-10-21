"""Build the original Kalends Immersion district as a textured, material-batched GLB.

No DCC installation or external Python dependencies are required beyond Pillow
and numpy. Geometry is authored in meters, Y-up; the historical map remains a
schematic gameplay reconstruction. This script does not mutate simulator floors.
"""
from __future__ import annotations
import argparse
import io
import json
import math
from pathlib import Path
import random
import struct
import hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'kalends_3d/assets/environment'
SCALE=.02
ORIGIN=(800,415)
RNG=random.Random(79)

def v3(x,y,z):return np.array((x,y,z),dtype=float)
def norm(v):
    d=np.linalg.norm(v)
    return v/d if d>1e-10 else v3(0,1,0)
def world(x,z,y=0):return ((x-800)*SCALE,y,(z-415)*SCALE)

def texture(name,base,size=256):
    """Seamless procedural PBR albedo, packed occlusion/roughness/metalness.

    Pattern is original code-generated art, never an imported illustration.
    sRGB albedo and linear ORM use glTF's standard channel assignments.
    """
    rng=np.random.default_rng(sum(map(ord,name))+79)
    yy,xx=np.mgrid[0:size,0:size]
    noise=rng.normal(0,1,(size,size))
    broad=np.zeros((size,size))
    for k,weight in [(2,1),(5,.5),(13,.2),(31,.1)]:
        a=rng.random()*2*math.pi;b=rng.random()*2*math.pi
        broad+=weight*np.sin(xx*2*math.pi*k/size+a)*np.cos(yy*2*math.pi*k/size+b)
    shade=1+.055*broad+.018*noise
    if name=='stone':
        seams=((xx+((yy//64)%2)*48)%96<3)|(yy%64<3)
        shade-=seams*.16
        shade+=.018*np.sin(xx*.27+yy*.32)
    elif name=='wood':
        shade+=.11*np.sin(xx*.42+5*np.sin(yy*.026))+.04*np.sin(xx*1.7+yy*.04)
        shade-=(xx%64<3)*.2
    elif name=='terracotta':
        shade+=.035*np.sin(xx*.13)+.025*np.cos(yy*.08)
    elif name=='plaster':
        shade+=.03*np.sin(xx*.15+yy*.11)
    elif name=='cloth':
        shade+=.018*((xx%3==0)|(yy%3==0))
    albedo=np.clip(np.array(base)[None,None,:]*shade[:,:,None],0,255).astype(np.uint8)
    orm=np.zeros((size,size,3),dtype=np.uint8);orm[:,:,0]=255;orm[:,:,1]=np.clip(218+noise*5,0,255);orm[:,:,2]=0
    if name=='wood':orm[:,:,1]=185
    if name=='terracotta':orm[:,:,1]=205
    return Image.fromarray(albedo),Image.fromarray(orm)

MATERIALS=[
 ('plaster',(218,194,146),.91),('ochre',(189,143,78),.92),('red',(132,58,42),.85),
 ('stone',(133,137,129),.94),('limestone',(202,195,164),.88),('terracotta',(159,77,43),.89),
 ('tile_light',(181,97,58),.87),('tile_dark',(127,66,47),.89),('wood',(91,65,40),.78),
 ('wood_light',(143,108,64),.84),('cloth',(184,91,48),.97),('cloth_cream',(227,204,156),.97),
 ('pottery',(162,91,53),.83),('pottery_dark',(96,70,50),.9),('bronze',(100,83,44),.55),
 ('water',(48,110,107),.2),('leaf',(82,104,52),.92),('flour',(219,199,155),1),
 ('charcoal',(48,44,36),.98),('mosaic',(222,211,181),.89),('sign',(228,205,146),.9),
 ('earth',(137,117,78),1),('earth_light',(158,140,105),1),('earth_dark',(111,101,70),1),
 ('plaster_light',(235,214,176),.92),('soil',(107,86,57),.98),('fire',(247,151,39),.65),
]
MAT={name:i for i,(name,_,_) in enumerate(MATERIALS)}

class Mesh:
    def __init__(self):self.p=[];self.n=[];self.uv=[];self.i=[]
    def tri(self,a,b,c,uv=None):
        a,b,c=np.array(a),np.array(b),np.array(c);n=norm(np.cross(b-a,c-a));start=len(self.p)
        self.p.extend([a.tolist(),b.tolist(),c.tolist()]);self.n.extend([n.tolist()]*3)
        self.uv.extend(uv or [(a[0],a[2]),(b[0],b[2]),(c[0],c[2])]);self.i.extend([start,start+1,start+2])
    def quad(self,a,b,c,d,uv=None):
        uv=uv or [(0,0),(1,0),(1,1),(0,1)]
        self.tri(a,b,c,[uv[0],uv[1],uv[2]]);self.tri(a,c,d,[uv[0],uv[2],uv[3]])
    def smooth_tri(self,a,b,c,na,nb,nc,uv=None):
        start=len(self.p);self.p.extend([list(a),list(b),list(c)]);self.n.extend([list(na),list(nb),list(nc)]);self.uv.extend(uv or [(0,0),(1,0),(1,1)]);self.i.extend([start,start+1,start+2])

class Model:
    def __init__(self):self.groups={};self.pivots={};self.parents={};self.current='district';self.metadata={'doors':[],'hinges':[],'roof_groups':[],'walkable_floors':[],'notes':[]}
    def mesh(self,mat):return self.groups.setdefault((self.current,MAT[mat]),Mesh())
    def polygon(self,points,mat):
        for k in range(1,len(points)-1):self.mesh(mat).tri(points[0],points[k],points[k+1])
    def box(self,center,size,mat,bevel=0):
        # Beveled polygon extrusion, not a one-box building facade.
        x,y,z=center;w,h,d=size
        if min(w,h,d)<=0:return
        x0,x1=x-w/2,x+w/2;z0,z1=z-d/2,z+d/2
        b=min(bevel,w*.22,d*.22,h*.22)
        rim=[(x0+b,z0),(x1-b,z0),(x1,z0+b),(x1,z1-b),(x1-b,z1),(x0+b,z1),(x0,z1-b),(x0,z0+b)] if b else [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
        bot=[(xx,y-h/2,zz) for xx,zz in rim];top=[(xx,y+h/2,zz) for xx,zz in rim]
        self.polygon(top[::-1],mat);self.polygon(bot,mat)
        for i in range(len(rim)):self.mesh(mat).quad(bot[(i+1)%len(rim)],bot[i],top[i],top[(i+1)%len(rim)],[(0,0),(w,0),(w,h),(0,h)])
    def beam(self,a,b,width,depth,mat):
        a,b=np.array(a),np.array(b);direction=norm(b-a);right=norm(np.cross(direction,v3(0,1,0)))
        if abs(direction[1])>.99:right=v3(1,0,0)
        up=norm(np.cross(right,direction));r=right*width*.5;u=up*depth*.5
        points=[a-r-u,a+r-u,a+r+u,a-r+u,b-r-u,b+r-u,b+r+u,b-r+u]
        for face in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:self.mesh(mat).quad(*(points[i] for i in face[::-1]))
    def lathe(self,c,profile,mat,segments=18):
        x,y,z=c
        for j in range(len(profile)-1):
            h0,r0=profile[j];h1,r1=profile[j+1]
            slope=-(r1-r0)/(h1-h0) if abs(h1-h0)>1e-6 else 0
            for i in range(segments):
                t0=i*2*math.pi/segments;t1=(i+1)*2*math.pi/segments
                a=v3(x+r0*math.cos(t0),y+h0,z+r0*math.sin(t0));b=v3(x+r0*math.cos(t1),y+h0,z+r0*math.sin(t1));d=v3(x+r1*math.cos(t0),y+h1,z+r1*math.sin(t0));cc=v3(x+r1*math.cos(t1),y+h1,z+r1*math.sin(t1))
                n0=norm(v3(math.cos(t0),slope,math.sin(t0)));n1=norm(v3(math.cos(t1),slope,math.sin(t1)))
                m=self.mesh(mat);m.smooth_tri(a,d,cc,n0,n0,n1,[(i/segments,h0), (i/segments,h1),((i+1)/segments,h1)]);m.smooth_tri(a,cc,b,n0,n1,n1,[(i/segments,h0),((i+1)/segments,h1),((i+1)/segments,h0)])
    def arch(self,x,z,width,height,depth,mat,segments=10):
        # Actual open arch geometry; stone voussoirs border an empty opening.
        r=width*.5;spring=height-r
        self.box((x-r-.13,spring*.5,z),(.26,spring,depth),mat,.04);self.box((x+r+.13,spring*.5,z),(.26,spring,depth),mat,.04)
        for k in range(segments):
            t0=k*math.pi/segments+.009;t1=(k+1)*math.pi/segments-.009
            inner=[(x+math.cos(t)*r,spring+math.sin(t)*r) for t in [t0,t1]]
            outer=[(x+math.cos(t)*(r+.28),spring+math.sin(t)*(r+.28)) for t in [t0,t1]]
            front=[(inner[0][0],inner[0][1],z+depth*.5),(inner[1][0],inner[1][1],z+depth*.5),(outer[1][0],outer[1][1],z+depth*.5),(outer[0][0],outer[0][1],z+depth*.5)]
            back=[(a,b,z-depth*.5) for a,b,_ in front]
            self.mesh(mat).quad(*front[::-1]);self.mesh(mat).quad(*back)
            for i in range(4):self.mesh(mat).quad(front[(i+1)%4],back[(i+1)%4],back[i],front[i])
    def column(self,x,z,height=2.7):
        self.box((x,.08,z),(.62,.16,.62),'limestone',.035)
        self.lathe((x,.16,z),[(0,.24),(.08,.27),(.16,.23),(.22,.21),(height-.48,.17),(height-.4,.23),(height-.28,.26)],'limestone',20)
        for i in range(10):
            t=i*math.pi*.2;self.beam((x+.213*math.cos(t),.42,z+.213*math.sin(t)),(x+.175*math.cos(t),height-.34,z+.175*math.sin(t)),.025,.025,'plaster_light')
        self.box((x,height-.07,z),(.62,.16,.62),'limestone',.04)
    def pot(self,x,z,scale=1,mat='pottery',y=0):
        profile=[(0,.075),(.05,.1),(.12,.19),(.27,.25),(.45,.245),(.59,.16),(.64,.105),(.73,.105),(.76,.14),(.79,.14),(.79,.1),(.72,.075)]
        self.lathe((x,y,z),[(a*scale,b*scale) for a,b in profile],mat,16)
        # Raised loop handles, each formed from a curved oval strip.
        for side in (-1,1):
            last=None
            for k in range(9):
                t=k*math.pi/8;point=(x+side*(.1+.18*math.sin(t))*scale,y+(.58+.14*math.cos(t))*scale,z)
                if last:self.beam(last,point,.045*scale,.04*scale,mat)
                last=point
    def sack(self,x,z,scale=.6,y=0):
        self.lathe((x,y,z),[(0,.2*scale),(.06*scale,.3*scale),(.55*scale,.32*scale),(.68*scale,.22*scale),(.74*scale,.13*scale)],'flour',14)
        self.lathe((x,y+.74*scale,z),[(0,.14*scale),(.035*scale,.15*scale),(.06*scale,.13*scale)],'wood_light',14)
    def sign(self,x,z,text,width=1.7,height=.4,y=2.55,group=None):
        previous=self.current
        if group:self.current=group
        self.box((x,y,z),(width,height,.06),'wood',.025)
        # Texture is generated for this actual sign, preserving Latin-labelled business frontage.
        self.metadata.setdefault('signs',[]).append({'name':text,'position':[x,y,z+.041],'size':[width-.08,height-.08],**({'group':group} if group else {})})
        if group:self.parents[group+'_lettering']=group
        self.current=previous
    def roof_tile(self,x,y,z,width,length,slope=0):
        # Curved imbrex tile segment with upper and lower shells and end thickness.
        m=self.mesh(RNG.choice(['terracotta','terracotta','tile_light','tile_dark']))
        r=width*.5
        for k in range(3):
            a=k*math.pi/3;b=(k+1)*math.pi/3
            def p(t,d,offset=0):return (x+r*math.cos(t),y+r*.46*math.sin(t)+d*slope+offset,z+d)
            m.quad(p(a,0),p(b,0),p(b,length),p(a,length))
            m.quad(p(a,length,-.025),p(b,length,-.025),p(b,0,-.025),p(a,0,-.025))
            for d in (0,length):m.quad(p(a,d),p(a,d,-.025),p(b,d,-.025),p(b,d))
    def roof(self,name,x0,x1,z0,z1,height=2.8):
        old=self.current;self.current=name+'_roof';self.metadata['roof_groups'].append(self.current)
        mid=(z0+z1)*.5;rise=(z1-z0)*.18
        for xa in np.arange(x0,x1,.28):
            for z in np.arange(z0,mid,.36):self.roof_tile(float(xa),height+(z-z0)*.36,float(z),.3,.40,.36)
            for z in np.arange(mid,z1,.36):self.roof_tile(float(xa),height+rise-(z-mid)*.36,float(z),.3,.40,-.36)
        for xa in np.arange(x0,x1,.28):self.roof_tile(float(xa),height+rise+.04,mid-.14,.34,.3,0)
        self.beam((x0,height-.08,z0),(x1,height-.08,z0),.13,.13,'wood')
        self.beam((x0,height-.08,z1),(x1,height-.08,z1),.13,.13,'wood')
        self.current=old


def paving(model):
    model.current='street_paving'
    # Public floor rectangles exactly match current backend navigation.
    floors=[(0,350,1600,130),(700,480,140,330)]
    for x,z,w,d in floors:
        model.metadata['walkable_floors'].append({'location':'street','sim_rect':[x,z,w,d]})
        x0,_,z0=world(x,z);width=w*SCALE;depth=d*SCALE
        model.box((x0+width*.5,-.12,z0+depth*.5),(width,.22,depth),'soil')
        rows=max(1,round(depth/.29));step=depth/rows
        for j in range(rows):
            xa=x0;rowz=z0+j*step
            while xa<x0+width-.01:
                length=min(RNG.uniform(.42,.67),x0+width-xa)
                model.box((xa+length*.5,-.006+RNG.uniform(-.008,.008),rowz+step*.5),(max(.01,length-.025),.08,step-.02),RNG.choice(['stone','stone','limestone']),.03)
                xa+=length
        # Thin drainage channels inside the stone margin are visual, nonblocking.
        for side in (0,depth):
            for xa in np.arange(x0,x0+width,.54):model.box((float(xa)+.25,.014,z0+side),(.49,.035,.075),'charcoal',.015)
    # Curb stones remain just outside the approved public floors.
    for simy in (343,487):
        for simx in range(0,1600,33):
            if simy==487 and 685<simx<850:continue
            x,_,z=world(simx,simy)
            model.box((x,.07,z),(.62,.15,.18),'limestone',.045)


def facade(model,name,x0,x1,zfront,depth,door=None,red=False,roof=True):
    old=model.current;model.current=name
    width=x1-x0;height=2.72;back=zfront-depth
    wallmat='ochre' if red else 'plaster'
    # Continuous party/rear walls, stucco upper, coarse masonry lower; fronts split around shop openings.
    model.box(((x0+x1)*.5,height*.5,back),(width,height,.2),wallmat,.04)
    for xx in (x0,x1):model.box((xx,height*.5,(back+zfront)*.5),(.2,height,depth),wallmat,.03)
    if door is None:
        model.box(((x0+x1)*.5,height*.5,zfront),(width,height,.23),wallmat,.03)
    else:
        dc,dw=door
        left=dc-dw*.5;right=dc+dw*.5
        if left>x0:model.box(((x0+left)*.5,height*.5,zfront),(left-x0,height,.23),wallmat,.03)
        if x1>right:model.box(((right+x1)*.5,height*.5,zfront),(x1-right,height,.23),wallmat,.03)
        model.box((dc,2.58,zfront),(dw,.28,.26),wallmat,.025)
        model.beam((left-.08,2.37,zfront+.03),(right+.08,2.37,zfront+.03),.14,.18,'wood')
        for side in (left-.045,right+.045):model.box((side,1.16,zfront+.02),(.11,2.3,.27),'limestone',.025)
    for xx in np.arange(x0+.08,x1,.52):
        model.box((float(xx)+.21,.18,back+.115),(.44,.31,.05),'limestone',.035)
    # Lower painted dado and irregular exposed stonework in reserved facade margins.
    for start,end in [(x0,door[0]-door[1]*.5 if door else x1),(door[0]+door[1]*.5 if door else x1,x1)]:
        if end-start>.02:
            model.box(((start+end)*.5,.47,zfront+.127),(end-start,.8,.035),'red' if red else 'ochre')
            model.box(((start+end)*.5,.93,zfront+.15),(end-start,.08,.07),'limestone',.012)
            for xx in np.arange(start+.1,end,.46):
                if xx+.3<end:model.box((float(xx)+.15,.15,zfront+.15),(.29,.25,.08),'stone',.04)
    # Plaster cornice, visible eave beams and roof shadow line.
    for yy,ww in [(2.64,.06),(2.73,.14)]:model.box(((x0+x1)*.5,yy,zfront+.06),(width+.18,.09,ww),'limestone',.018)
    for xx in np.arange(x0+.2,x1,.55):model.box((float(xx),2.58,zfront-.08),(.11,.12,.49),'wood')
    if roof:model.roof(name,x0-.22,x1+.22,back-.2,zfront+.25,height=2.82)
    model.current=old


def bakery(model):
    x0,_,z0=world(650,80);x1,_,z1=world(970,310);dx,_,dz=world(810,350)
    model.current='bakery_floor'
    model.metadata['walkable_floors'].append({'location':'bakery','sim_rect':[665,95,290,200]})
    # Bakery floor and the mandatory doorway connector are contiguous.
    model.box(((x0+x1)*.5,-.08,(z0+z1)*.5),(x1-x0,.16,z1-z0),'mosaic')
    model.box((dx,-.065,(z1+dz)*.5),(.9,.13,dz-z1+.3),'limestone',.03)
    for simx in range(666,956,15):
        for simz in (96,286):
            x,_,z=world(simx,simz);model.box((x,.013,z),(.12,.014,.12),'red')
    # Spacious open taberna front, real inset-floor preserved for free movement.
    facade(model,'bakery_walls',x0-.05,x1+.05,z1+.10,z1-z0+.15,door=(dx,1.7),red=True,roof=False)
    model.current='bakery_details'
    model.sign(dx,z1+.26,'PISTOR FELIX',2.6,.43,2.68,group='bakery_frontage_sign')
    # Bread oven in a recessed rear alcove, beyond the authoritative floor's northern edge.
    ox=x1-.82;oz=z0-.38
    model.box((ox,.20,oz),(1.05,.4,1.1),'stone',.08)
    model.lathe((ox,.40,oz),[(0,.55),(.15,.55),(.35,.5),(.55,.37),(.67,.12)],'terracotta',24)
    model.arch(ox,oz+.49,.42,.56,.18,'limestone',8)
    model.box((ox,.60,oz+.51),(.3,.22,.02),'charcoal',.025)
    model.box((ox,.53,oz+.525),(.18,.04,.015),'fire')
    model.lathe((ox,.98,oz),[(0,.12),(.55,.12),(.6,.15),(.65,.15)],'terracotta',12)
    # Recessed storage and work shelf behind the rear edge, never on the clear floor.
    shelfx=x0+1.2;shelfz=z0-.22
    model.box((shelfx,.75,shelfz),(1.6,.13,.48),'wood',.035)
    for px in (shelfx-.65,shelfx+.65):model.box((px,.35,shelfz),(.1,.75,.36),'wood')
    for k in range(5):
        bx=shelfx-.55+k*.27
        model.lathe((bx,.83,shelfz),[(0,.12),(.035,.15),(.09,.13),(.11,.08)],'flour',12)
    for bx,bz in [(x0+.30,z0-.25),(x0+.67,z0-.25),(x0+.30,z0-.65)]:model.sack(bx,bz,.8)
    model.pot(x1+.26,z0+.7,.8)
    # Side-wall utility hooks and shelves within the non-walkable inset margin.
    for zz in (z0+.5,z0+1.6,z0+3.3):
        model.box((x0+.11,1.05,zz),(.19,.06,.45),'wood_light',.02)
        model.pot(x0+.10,zz,.26,y=1.09)
    # Roofing cutaway is separately toggled by the client on room entry.
    model.roof('bakery',x0-.26,x1+.26,z0-.45,z1+.35,2.86)
    model.current='bakery_door'
    # Authored open shutter pair outside the doorway/connector corridor.
    for side in (-1,1):
        model.current='bakery_shutter_'+('left' if side<0 else 'right')
        model.pivots[model.current]=(dx+side*.85,0,z1+.17)
        model.metadata['hinges'].append({'group':model.current,'pivot':list(model.pivots[model.current]),'axis':[0,1,0],'rest_rotation_degrees':0,'swing_degrees':side*15,'scope':'Nonblocking cosmetic shutter motion, no authoritative door-lock state.'})
        px=dx+side*1.06
        for q in range(5):model.box((px+q*.085*side,1.05,z1+.17),(.08,2.08,.10),'wood_light',.01)
        model.box((px+side*.17,.58,z1+.24),(.55,.11,.06),'wood')
        model.box((px+side*.17,1.52,z1+.24),(.55,.11,.06),'wood')
    model.metadata['doors'].append({'id':'bakery','sim_door':[810,350],'scene_door':[dx,0,dz],'scene_threshold':list(world(810,295)),'opening_width_m':1.7,'groups':['bakery_shutter_left','bakery_shutter_right']})


def canopy(model,x0,x1,z0,z1,height=2.2):
    for x in (x0,x1):
        model.lathe((x,0,z1),[(0,.055),(height,.045),(height+.08,.06)],'wood_light',8)
    for j in range(12):
        a=x0+(x1-x0)*j/12;b=x0+(x1-x0)*(j+1)/12
        for k in range(5):
            z=z0+(z1-z0)*k/5;zn=z0+(z1-z0)*(k+1)/5
            def y(q):return height+.20-.19*math.sin((q-z0)/(z1-z0)*math.pi*.8)
            model.mesh('cloth' if j%3 else 'cloth_cream').quad((a,y(z),z),(b,y(z),z),(b,y(zn),zn),(a,y(zn),zn))
        model.mesh('cloth' if j%3 else 'cloth_cream').quad((a,y(z1),z1),(b,y(z1),z1),(b,y(z1)-.19,z1),(a,y(z1)-.19,z1))
    model.beam((x0,height,z1),(x1,height,z1),.08,.08,'wood')


def fountain(model):
    # Kept beyond public floor to avoid pretending the server has a basin collider.
    x,_,z=world(510,322)
    model.current='fountain'
    model.box((x,.12,z),(1.4,.24,.93),'limestone',.09)
    for xx in (-.65,.65):model.box((x+xx,.43,z),(.14,.48,.93),'limestone',.045)
    for zz in (-.4,.4):model.box((x,.43,z+zz),(1.3,.48,.14),'limestone',.045)
    model.box((x,.38,z),(1.10,.018,.65),'water')
    model.box((x,.95,z-.47),(.69,1.36,.23),'limestone',.06)
    model.lathe((x,1.08,z-.33),[(0,.1),(.035,.14),(.07,.1)],'bronze',12)
    model.metadata['notes'].append('Fountain basin shifted to schematic north margin (510,322), beside named water point (510,415), so presentation does not add an unvalidated street obstruction.')


def frontage(model):
    # A continuous street wall establishes a real small district, rather than isolated props.
    for j,(a,b) in enumerate([(35,185),(195,350),(360,465),(525,635),(985,1135),(1145,1310),(1320,1560)]):
        front=300 if j==4 else 329
        x0,_,zfront=world(a,front);x1,_,_=world(b,front)
        center=(x0+x1)*.5
        depth=2.9+(j%2)*.55
        model.current='frontage_foundations'
        model.box((center,-.10,zfront-depth*.5),(x1-x0+.12,.20,depth+.15),'stone',.04)
        facade(model,f'frontage_{j}',x0,x1,zfront,depth,door=(center,.92),red=j%3==1)
        model.current=f'frontage_details_{j}'
        # Folded shutters, pegged planks, iron fittings.
        for side in (-1,1):
            sx=center+side*.72
            for k in range(4):model.box((sx+side*k*.09,.99,zfront+.14),(.08,1.9,.09),'wood_light',.015)
            for yy in (.32,1.48):model.box((sx+side*.13,yy,zfront+.2),(.40,.1,.08),'wood')
        for xx in (x0+.4,x1-.4):
            model.box((xx,1.79,zfront+.13),(.47,.65,.10),'wood',.015)
            for k in range(4):model.box((xx-.18+k*.12,1.8,zfront+.2),(.06,.52,.035),'wood_light',.01)
        model.sign(center,zfront+.16,['TABERNA','VINVM','OLEVM','MERCATOR','PANIS','TEXTOR','OFFICINA'][j],1.25,.29,2.45)
        if j==1:
            canopy(model,x0+.22,x1-.22,zfront+.03,zfront+.40,2.20)
            model.box((center,.42,zfront+.19),(x1-x0-.6,.84,.34),'wood_light',.045)
            for q in range(5):model.pot(x0+.4+q*(x1-x0-.8)/5,zfront+.13,.28,y=.85)
        if j in (0,2,5):
            model.pot(x0+.4,zfront+.05,.75)
            model.pot(x1-.4,zfront+.04,.58,'pottery_dark')
    fountain(model)


def south_buildings(model):
    # South rooms retain complete clear floors. Front faces sit on the public side;
    # roof groups are hideable and south (camera-facing) walls are low cutaways.
    rooms=[('fullery',220,500,330,240,385,480),('thermopolium',1060,500,330,240,1225,480),('household',570,810,400,240,770,790)]
    for name,sx,sz,sw,sd,doorx,doorz in rooms:
        x0,_,z0=world(sx,sz);x1,_,z1=world(sx+sw,sz+sd);dx,_,dz=world(doorx,doorz)
        model.current=name+'_floor';model.box(((x0+x1)*.5,-.08,(z0+z1)*.5),(x1-x0,.16,z1-z0),'mosaic')
        model.box((dx,-.065,(z0+dz)*.5),(1.0,.13,z0-dz+.3),'limestone',.025)
        model.metadata['walkable_floors'].append({'location':name,'sim_rect':[sx+15,sz+15,sw-30,sd-30]})
        model.current=name+'_walls'
        # North-facing front split for actual door, low far wall for legible cutaway.
        for a,b in [(x0,dx-.7),(dx+.7,x1)]:
            model.box(((a+b)*.5,1.3,z0),(b-a,2.6,.2),'plaster',.025)
            model.box(((a+b)*.5,.4,z0-.12),(b-a,.73,.04),'red')
        for xx in (x0,x1):model.box((xx,.48,(z0+z1)*.5),(.2,.96,z1-z0),'plaster',.03)
        model.box(((x0+x1)*.5,.3,z1),(x1-x0,.6,.2),'plaster',.03)
        model.arch(dx,z0,1.35,2.4,.24,'limestone',10)
        model.current=name+'_details'
        model.sign(dx,z0-.16,{'fullery':'FULLONICA','thermopolium':'SABINA','household':'DOMVS'}[name],1.7,.35,2.65)
        # Recessed wall-edge furnishing, outside inset floor.
        for k in range(6):model.pot(x1+.14,z0+.45+k*.58,.53,'pottery_dark' if k%2 else 'pottery')
        if name=='thermopolium':
            # Food counter is against exterior west edge: no phantom collision on the floor.
            model.box((x0-.31,.53,(z0+z1)*.5),(.58,1.06,3.2),'red',.07)
            model.box((x0-.31,1.09,(z0+z1)*.5),(.67,.09,3.3),'limestone',.04)
            for q in range(5):model.lathe((x0-.31,1.14,z0+.65+q*.52),[(0,.19),(.025,.19),(.025,.13),(-.06,.13)],'pottery_dark',16)
        if name=='fullery':
            for q in range(3):
                model.box((x0-.38,.24,z0+.7+q*.95),(.7,.48,.75),'limestone',.07)
                model.box((x0-.38,.48,z0+.7+q*.95),(.52,.018,.59),'water')
        if name=='household':
            for xx in (x0-.35,x1+.35):model.column(xx,z0+.3,2.7)
            model.box(((x0+x1)*.5,2.80,z0+.3),(x1-x0+1,.24,.8),'limestone',.05)
            model.sign(dx,z0-.20,'MENANDER',2.1,.34,2.92)
        # Only narrow side eaves avoid roofs hiding whole usable southern rooms.
        model.roof(name,x0-.20,x1+.20,z1-.48,z1+.3,2.40)
        model.metadata['doors'].append({'id':name,'sim_door':[doorx,doorz],'scene_door':[dx,0,dz],'scene_threshold':list(world(doorx,sz+15)),'opening_width_m':1.35})


def greenery(model):
    model.current='garden_edges'
    for simx,simz in [(75,315),(550,323),(1010,319),(1520,325),(685,775),(855,775)]:
        x,_,z=world(simx,simz);model.pot(x,z,.7,'pottery_dark')
        # Broad-leaf branches as shaped pointed mesh leaves rather than billboard icons.
        for i in range(7):
            t=i*2.399;start=v3(x,.48,z);tip=v3(x+math.cos(t)*.24,.75+(.15 if i%2 else 0),z+math.sin(t)*.24)
            model.beam(start,tip,.018,.018,'wood_light')
            right=norm(np.cross(tip-start,v3(0,1,0)))*.08;middle=start+(tip-start)*.7+v3(0,.08,0)
            model.mesh('leaf').tri(start,middle+right,tip);model.mesh('leaf').tri(start,tip,middle-right)


def terrain_and_backdrop(model):
    """Visual district context beyond the explicitly bounded playable floors.

    The terrain is not appended to navigation metadata and never authorizes
    travel into the noninteractive peripheral lots.
    """
    model.current='district_ground'
    xs=np.arange(-32,34,2.);zs=np.arange(-22,30,2.)
    def point(x,z):
        # Keep the ground below road/interior floor tops and close their undersides.
        y=-.18+.025*math.sin(x*.27)*math.cos(z*.33)
        return (float(x),y,float(z))
    for j in range(len(zs)-1):
        for i in range(len(xs)-1):
            x,xn=xs[i],xs[i+1];z,zn=zs[j],zs[j+1]
            mat=RNG.choices(['earth','earth_light','earth_dark'],[8,2,1])[0]
            model.mesh(mat).quad(point(x,z),point(x,zn),point(xn,zn),point(xn,z),[(x*.32,z*.32),(x*.32,zn*.32),(xn*.32,zn*.32),(xn*.32,z*.32)])
    # Foundations close cutaway building edges and give the street real mass.
    model.current='district_foundations'
    for sx,sz,sw,sd in [(650,80,320,230),(220,500,330,240),(1060,500,330,240),(570,810,400,240)]:
        x,_,z=world(sx+sw*.5,sz+sd*.5)
        model.box((x,-.11,z),(sw*SCALE+.08,.2,sd*SCALE+.08),'stone',.035)
    # Low enclosing plot walls belong to nonwalkable gaps, never across the street.
    walls=[(-14.8,1.75,-12.1,1.75),(-14.8,1.75,-14.8,8.6),(-14.8,8.6,-5.2,8.6),(1.25,7.6,4.7,7.6),(4.7,7.6,4.7,1.8),(12.4,1.8,16,1.8),(16,1.8,16,10),(12.4,10,16,10)]
    for x0,z0,x1,z1 in walls:
        model.beam((x0,.18,z0),(x1,.18,z1),.22,.55,'stone')
        model.beam((x0,.50,z0),(x1,.50,z1),.29,.10,'limestone')
    # Terracotta fragments and stone edging ground the unoccupied peripheral lots.
    model.current='lot_surface_details'
    for x,z in [(-13,3),(-12.5,6.5),(-6,7.8),(2.3,5.5),(3.8,5),(13.2,4),(14,8),(-9,-9.7),(6,-9.8)]:
        for k in range(7):
            px=x+RNG.uniform(-.42,.42);pz=z+RNG.uniform(-.4,.4)
            model.box((px,-.108,pz),(RNG.uniform(.08,.18),.035,RNG.uniform(.05,.13)),RNG.choice(['stone','tile_dark','terracotta']),.02)
    # Context buildings use authored roof planes/ridges, at a deliberately lower
    # level of detail than the playable frontage. They are opaque distant scenery.
    model.current='backdrop_buildings'
    for k,(x0,x1,zfront,depth,h) in enumerate([(-28,-18,-10.7,3.7,3.0),(-17.8,-8.6,-11.8,4.0,3.6),(-8.4,1.5,-11.2,3.5,3.3),(1.7,10.4,-11.5,4.2,3.65),(10.6,20,-10.7,4.0,3.2),(20.2,29,-11.3,4.0,3.4)]):
        center=(x0+x1)*.5
        model.box((center,h*.5-.08,zfront-depth*.5),(x1-x0,h,depth),'ochre' if k%3 else 'plaster',.055)
        for xx in np.arange(x0+.7,x1-.2,1.6):
            model.box((float(xx),1.5,zfront+.03),(.65,1.0,.10),'wood',.025)
            for q in range(3):model.box((float(xx)-.22+q*.22,1.5,zfront+.09),(.08,.86,.035),'wood_light',.012)
        # Geometric sloping roof, curved segmented ridge and chimney silhouette.
        mid=zfront-depth*.5;rise=depth*.19
        for side in (-1,1):
            edge=mid+side*(depth*.5+.28)
            points=[(x0-.24,h,edge),(x1+.24,h,edge),(x1+.24,h+rise,mid),(x0-.24,h+rise,mid)];uv=[(0,0),((x1-x0)/2,0),((x1-x0)/2,depth*.25),(0,depth*.25)]
            if side<0:points.reverse();uv.reverse()
            model.mesh('tile_dark' if k%2 else 'terracotta').quad(*points,uv)
        for xx in np.arange(x0,x1,.33):model.roof_tile(float(xx),h+rise+.025,mid-.15,.33,.32)
        model.box((center+1,h+.35,mid-.5),(.38,.85,.42),'plaster',.025)
        model.box((center+1,h+.8,mid-.5),(.52,.12,.55),'limestone',.025)
    model.metadata['notes'].append('Ground and background buildings are noninteractive visual context. They do not extend the authoritative walkable map or create new residents/business inventory.')
    model.metadata['playable_scene_bounds']={'min':[-16.4,-.25,-7.7],'max':[16.4,4,13.4]}


def market_cart(model):
    """Six actual visible sacks on a nonblocking market-apron presentation cart.

    The simulator owns the cargo outcome. The client may hide the cargo node
    after an actual story resolution; this mesh creates no economic inventory.
    """
    x,_,z=world(1020,325);model.current='market_cart'
    # Underframe, crossbeams, planked bed and iron corner straps.
    for zz in (-.22,.22):model.box((x,.43,z+zz),(1.62,.12,.09),'wood',.025)
    for xx in (-.62,.62):model.box((x+xx,.45,z),( .1,.13,.64),'wood',.02)
    for q in range(7):model.box((x-.66+q*.22,.53,z),(.205,.075,.60),'wood_light',.015)
    for xx in (-.78,.78):
        for zz in (-.29,.29):
            model.box((x+xx,.72,z+zz),(.085,.49,.085),'wood',.016)
            model.box((x+xx,.57,z+zz),(.105,.16,.105),'bronze',.01)
    # Slatted long sides and tailboard leave the separate sacks legible.
    for zz in (-.30,.30):
        for yy in (.66,.83):model.box((x,yy,z+zz),(1.62,.10,.065),'wood_light',.012)
    for yy in (.66,.83):model.box((x-.79,yy,z),(.065,.10,.59),'wood_light',.012)
    # Double axle/two-spoked-wheel assembly, with genuine annular tyre geometry.
    model.beam((x,.17,z-.38),(x,.17,z+.38),.095,.095,'wood')
    for side in (-1,1):
        wz=z+side*.35;radius=.32;inner=.267;thick=.07
        for q in range(20):
            a=q*2*math.pi/20;b=(q+1)*2*math.pi/20
            def point(t,r,depth):return (x+math.cos(t)*r,.17+math.sin(t)*r,wz+depth)
            for d in (-thick*.5,thick*.5):
                pts=[point(a,inner,d),point(b,inner,d),point(b,radius,d),point(a,radius,d)]
                if d>0:pts.reverse()
                model.mesh('wood').quad(*pts)
            model.mesh('wood').quad(point(a,radius,-thick*.5),point(b,radius,-thick*.5),point(b,radius,thick*.5),point(a,radius,thick*.5))
            model.mesh('wood').quad(point(a,inner,thick*.5),point(b,inner,thick*.5),point(b,inner,-thick*.5),point(a,inner,-thick*.5))
        for q in range(8):
            t=q*math.pi*.25
            model.beam((x,.17,wz),(x+math.cos(t)*.272,.17+math.sin(t)*.272,wz),.038,.045,'wood_light')
        model.box((x,.17,wz),(.13,.13,.11),'bronze',.035)
    # Hand shafts extend east within the same recessed market apron.
    for zz in (-.18,.18):
        model.beam((x+.62,.41,z+zz),(x+1.6,.68,z+zz),.055,.065,'wood_light')
        model.box((x+1.56,.68,z+zz),(.18,.075,.075),'wood',.018)
    model.current='market_cart_cargo';model.parents['market_cart_cargo']='market_cart'
    for xx in (-.48,0,.48):
        for zz in (-.14,.14):model.sack(x+xx,z+zz,.55,y=.58)
    model.metadata['market_cart']={'node':'market_cart','cargo_node':'market_cart_cargo','cargo_visual_count':6,'scene_position':[x,0,z],'sim_presentation_offset':[1020,325],'cargo_visibility':'Show only while authoritative story stage is unresolved or committed; hide after actual resolution. Cart remains as emptied scenery.','navigation':'Nonwalkable recessed apron. Adjacent decorative frontage is set back to y300 to avoid mesh intersection. No new walkable floor or collider.','historical_disclosure':'Original fictional market-cart reconstruction; off-floor presentation offset near Marcus, not an authoritative cart position.'}


def interior_cutaway_walls(model):
    """Authored alternate wall meshes; never fake a cutaway by scaling Y.

    Normally hidden by the client. When a room is active, its normal wall node
    is replaced by this lower camera-facing version; the floor/nav is identical.
    """
    model.metadata['room_wall_variants']={}
    def wall(center,width,depth,height,mat='plaster',paint=True):
        x,z=center
        model.box((x,height*.5,z),(width,height,depth),mat,.025)
        # Actual raised cap, stone footing and two weathered painted registers.
        model.box((x,height+.035,z),(width+.055,.07,depth+.055),'limestone',.02)
        model.box((x,.12,z),(width+.015,.22,depth+.015),'stone',.025)
        if paint:
            model.box((x,.43,z+depth*.5+.015),(width,.36,.025),'red')
            model.box((x,.67,z+depth*.5+.022),(width,.045,.042),'ochre',.007)
    rooms=[('bakery',650,80,320,230,810,1.7),('fullery',220,500,330,240,385,1.35),('thermopolium',1060,500,330,240,1225,1.35),('household',570,810,400,240,770,1.35)]
    for name,sx,sz,sw,sd,doorx,doorwidth in rooms:
        x0,_,z0=world(sx,sz);x1,_,z1=world(sx+sw,sz+sd);dx,_,_=world(doorx,sz)
        normal=name+'_walls';cut=name+'_cutaway_walls';model.current=cut
        model.metadata['room_wall_variants'][name]={'normal':normal,'cutaway':cut,'initially_visible':normal,'cutaway_default_visible':False,**({'hide_inside':['bakery_frontage_sign']} if name=='bakery' else {}),'south_height_m':.82 if name=='bakery' else .75,'side_height_m':.82,'north_height_m':2.72 if name=='bakery' else 2.6,'method':'Distinct capped mesh geometry, not runtime scaling; mutually exclusive normal/cutaway groups.'}
        for xx in (x0,x1):wall((xx,(z0+z1)*.5),.20,z1-z0,.82,paint=False)
        if name=='bakery':
            # Preserve the northern oven backdrop and lower the southern shopfront.
            # Full northern backdrop with an actual oven recess, so the modelled
            # oven is visible through the rear wall rather than buried inside it.
            ox=x1-.82
            for left,right in [(x0-.05,ox-.65),(ox+.65,x1+.05)]:wall(((left+right)*.5,z0-.05),right-left,.20,2.72,paint=False)
            model.box((ox,2.27,z0-.05),(1.30,.90,.20),'plaster',.025)
            model.box((ox,2.755,z0-.05),(1.35,.07,.255),'limestone',.02)
            model.arch(ox,z0-.04,1.05,1.63,.24,'limestone',10)
            for left,right in [(x0,dx-doorwidth*.5),(dx+doorwidth*.5,x1)]:
                wall(((left+right)*.5,z1+.10),right-left,.23,.82)
            for side in (-1,1):
                model.box((dx+side*(doorwidth*.5+.045),.49,z1+.12),(.12,.98,.27),'limestone',.025)
                model.box((dx+side*(doorwidth*.5+.045),1.025,z1+.12),(.17,.07,.32),'limestone',.02)
        else:
            # Northern entrance wall remains a useful interior backdrop, while
            # the camera-facing south wall is a capped stone/plaster parapet.
            for left,right in [(x0,dx-doorwidth*.5),(dx+doorwidth*.5,x1)]:
                wall(((left+right)*.5,z0),right-left,.20,2.6)
            model.arch(dx,z0,doorwidth,2.4,.24,'limestone',10)
            wall(((x0+x1)*.5,z1),x1-x0,.20,.75)
    model.metadata['notes'].append('Room cutaway wall variants are initially hidden and replace their corresponding normal wall group only during actual room presence. Both sets preserve identical door openings and clear floor footprints.')


def export_glb(model,path):
    buffers=bytearray();views=[];accessors=[];meshes=[];nodes=[];materials=[];images=[];textures=[]
    def chunk(data,target=None):
        while len(buffers)%4:buffers.append(0)
        offset=len(buffers);buffers.extend(data);v={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target:v['target']=target
        views.append(v);return len(views)-1
    def accessor(data,typ,component=5126,shape=None):
        arr=np.asarray(data,dtype='<f4' if component==5126 else '<u4');view=chunk(arr.tobytes(),34962 if component==5126 else 34963)
        a={'bufferView':view,'componentType':component,'count':len(data),'type':typ}
        if typ=='VEC3':a.update(min=np.min(arr,axis=0).tolist(),max=np.max(arr,axis=0).tolist())
        accessors.append(a);return len(accessors)-1
    texture_cache={}
    def image_texture(key,payload,mime):
        if key in texture_cache:return texture_cache[key]
        view=chunk(payload);images.append({'bufferView':view,'mimeType':mime,'name':key});textures.append({'source':len(images)-1,'sampler':0})
        texture_cache[key]=len(textures)-1
        return len(textures)-1
    for name,color,roughness in MATERIALS:
        category={'plaster':'plaster','ochre':'plaster','red':'plaster','plaster_light':'plaster','earth':'plaster','earth_light':'plaster','earth_dark':'plaster','stone':'stone','limestone':'stone','mosaic':'stone','wood':'wood','wood_light':'wood','terracotta':'terracotta','tile_light':'terracotta','tile_dark':'terracotta'}.get(name)
        source=ROOT/'kalends_3d/assets/materials'
        actual=category and all((source/(category+'_'+suffix+'_1k.jpg')).exists() for suffix in ['diff','nor_gl','arm'])
        if actual:
            ids={suffix:image_texture(category+'_'+suffix,(source/(category+'_'+suffix+'_1k.jpg')).read_bytes(),'image/jpeg') for suffix in ['diff','nor_gl','arm']}
            # Actual PBR material textures are CC0 Poly Haven assets (separate provenance manifest).
            factor={'plaster':[1,.91,.76,1],'ochre':[.86,.69,.42,1],'red':[.62,.22,.13,1],'plaster_light':[1,.98,.86,1],'limestone':[1,.97,.86,1],'mosaic':[1,.97,.87,1],'wood':[.78,.66,.49,1],'wood_light':[1,.9,.72,1],'earth':[.54,.45,.30,1],'earth_light':[.64,.55,.38,1],'earth_dark':[.42,.36,.23,1],'terracotta':[.67,.22,.075,1],'tile_light':[.83,.31,.115,1],'tile_dark':[.48,.125,.045,1]}.get(name,[1,1,1,1])
            materials.append({'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':ids['diff']},'baseColorFactor':factor,'metallicRoughnessTexture':{'index':ids['arm']},'roughnessFactor':roughness,'metallicFactor':1},'normalTexture':{'index':ids['nor_gl'],'scale':.32 if category=='plaster' else .55},'occlusionTexture':{'index':ids['arm'],'strength':.7},'doubleSided':False})
        else:
            basename={'cloth_cream':'cloth','pottery':'terracotta','pottery_dark':'terracotta','flour':'cloth'}.get(name,name)
            albedo,orm=texture(basename,color)
            ids=[]
            for im in (albedo,orm):
                mem=io.BytesIO();im.save(mem,format='PNG',optimize=True);ids.append(image_texture(name+('_base' if im is albedo else '_orm'),mem.getvalue(),'image/png'))
            materials.append({'name':name,'pbrMetallicRoughness':{'baseColorTexture':{'index':ids[0]},'metallicRoughnessTexture':{'index':ids[1]},'roughnessFactor':roughness,'metallicFactor':.5 if name=='bronze' else 0},'occlusionTexture':{'index':ids[1],'strength':.8},'doubleSided':name in ('cloth','cloth_cream','leaf')})
        if name=='water':materials[-1]['pbrMetallicRoughness']['baseColorFactor']=[.6,.85,.88,.8];materials[-1]['alphaMode']='BLEND'
        if name=='fire':materials[-1]['emissiveFactor']=[.45,.12,.005]
    grouped={}
    for (group,mat),mesh in sorted(model.groups.items()):
        if not mesh.p:continue
        unique={};positions=[];normals=[];uvs=[];indices=[]
        for index in mesh.i:
            key=tuple(round(float(v),6) for values in [mesh.p[index],mesh.n[index],mesh.uv[index]] for v in values)
            if key not in unique:
                unique[key]=len(positions);positions.append(mesh.p[index]);normals.append(mesh.n[index]);uvs.append(mesh.uv[index])
            indices.append(unique[key])
        if group in model.pivots:positions=(np.asarray(positions)-np.asarray(model.pivots[group])).tolist()
        primitive={'attributes':{'POSITION':accessor(positions,'VEC3'),'NORMAL':accessor(normals,'VEC3'),'TEXCOORD_0':accessor(uvs,'VEC2')},'indices':accessor(indices,'SCALAR',5125),'material':mat,'mode':4}
        grouped.setdefault(group,[]).append(primitive)
    for group,primitives in grouped.items():
        meshes.append({'name':group,'primitives':primitives});nodes.append({'name':group,'mesh':len(meshes)-1,'extras':{'kalendsGroup':group,'hideInside':group.endswith('_roof')}})
        if group in model.pivots:nodes[-1]['translation']=list(model.pivots[group])
        if group.endswith('_cutaway_walls'):nodes[-1]['extras'].update(cutawayFor=group.removesuffix('_cutaway_walls'),initiallyVisible=False)
    # Embedded lettering textures are actual geometry in the scene.
    for idx,sign in enumerate(model.metadata.get('signs',[])):
        width,height=sign['size'];image=Image.new('RGBA',(512,128),(0,0,0,0));draw=ImageDraw.Draw(image)
        try:
            from PIL import ImageFont
            font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf',48)
        except OSError:font=None
        bbox=draw.textbbox((0,0),sign['name'],font=font);tw,th=bbox[2]-bbox[0],bbox[3]-bbox[1]
        draw.text(((512-tw)/2,(128-th)/2-bbox[1]),sign['name'],font=font,fill=(236,214,157,255))
        mem=io.BytesIO();image.save(mem,format='PNG');view=chunk(mem.getvalue());images.append({'bufferView':view,'mimeType':'image/png','name':sign['name']});textures.append({'source':len(images)-1,'sampler':0});mat=len(materials)
        materials.append({'name':'lettering_'+sign['name'],'pbrMetallicRoughness':{'baseColorTexture':{'index':len(textures)-1},'metallicFactor':0,'roughnessFactor':1},'alphaMode':'BLEND','doubleSided':True})
        x,y,z=sign['position'];m=Mesh();m.quad((x-width*.5,y-height*.5,z),(x+width*.5,y-height*.5,z),(x+width*.5,y+height*.5,z),(x-width*.5,y+height*.5,z),[(0,1),(1,1),(1,0),(0,0)])
        prim={'attributes':{'POSITION':accessor(m.p,'VEC3'),'NORMAL':accessor(m.n,'VEC3'),'TEXCOORD_0':accessor(m.uv,'VEC2')},'indices':accessor(m.i,'SCALAR',5125),'material':mat}
        name=sign['group']+'_lettering' if sign.get('group') else 'sign_'+str(idx)
        meshes.append({'name':name,'primitives':[prim]});nodes.append({'name':name,'mesh':len(meshes)-1})
    # Preserve an actual parent-child cargo hierarchy for state-driven unloading.
    group_nodes={node['name']:index for index,node in enumerate(nodes)}
    for child,parent in model.parents.items():
        nodes[group_nodes[parent]].setdefault('children',[]).append(group_nodes[child])
    child_nodes={group_nodes[child] for child in model.parents}
    gltf={'asset':{'version':'2.0','generator':'Kalends original environment mesh pipeline v1'},'scene':0,'scenes':[{'nodes':[i for i in range(len(nodes)) if i not in child_nodes]}],'nodes':nodes,'meshes':meshes,'materials':materials,'images':images,'textures':textures,'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}],'buffers':[{'byteLength':len(buffers)}],'bufferViews':views,'accessors':accessors,'extras':{'worldScale':SCALE,'simOrigin':list(ORIGIN),'reconstruction':'Original schematic Roman-inspired architectural composition, not an archaeological model.'}}
    encoded=json.dumps(gltf,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary=bytes(buffers);binary+=b'\0'*((-len(binary))%4)
    payload=struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    path.write_bytes(payload)
    return gltf,{'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),'triangles':sum(len(m.i)//3 for m in model.groups.values())+len(model.metadata.get('signs',[]))*2,'unindexed_vertex_references':sum(len(m.p) for m in model.groups.values()),'indexed_vertices':sum(a['count'] for a in accessors if a['type']=='VEC3')//2,'nodes':len(nodes),'material_batches':sum(len(m['primitives']) for m in meshes),'materials':len(materials),'textures':len(textures)}


def validate_glb(path):
    """Fail the build on invalid buffer ranges, indices or nonfinite model data."""
    raw=path.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and length==len(raw)
    n,tag=struct.unpack_from('<I4s',raw,12);assert tag==b'JSON';doc=json.loads(raw[20:20+n])
    bn,btag=struct.unpack_from('<I4s',raw,20+n);assert btag==b'BIN\0';binary=raw[28+n:28+n+bn]
    assert len(binary)==bn and doc['buffers'][0]['byteLength']<=bn
    component={5126:('<f4',4),5125:('<u4',4)};counts={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def read(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dtype,size=component[a['componentType']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);count=a['count']*counts[a['type']]
        assert offset+count*size<=len(binary)
        return np.frombuffer(binary,dtype=dtype,count=count,offset=offset).reshape(a['count'],counts[a['type']])
    triangles=0;groups={}
    for mesh in doc['meshes']:
        count=0
        for prim in mesh['primitives']:
            pos=read(prim['attributes']['POSITION']);normal=read(prim['attributes']['NORMAL']);uv=read(prim['attributes']['TEXCOORD_0']);indices=read(prim['indices']).ravel()
            assert len(pos)==len(normal)==len(uv) and np.isfinite(pos).all() and np.isfinite(normal).all() and np.isfinite(uv).all()
            assert indices.max()<len(pos) and len(indices)%3==0 and 0<=prim['material']<len(doc['materials'])
            assert np.all(np.abs(np.linalg.norm(normal,axis=1)-1)<.005)
            count+=len(indices)//3
        groups[mesh['name']]=count;triangles+=count
    for image in doc['images']:
        assert image['mimeType'] in ('image/png','image/jpeg')
        view=doc['bufferViews'][image['bufferView']];assert view['byteOffset']+view['byteLength']<=len(binary)
    box=Model();box.box((0,0,0),(2,2,2),'plaster',.1)
    for mesh in box.groups.values():
        for i in range(0,len(mesh.p),3):assert np.dot(np.mean(mesh.p[i:i+3],axis=0),mesh.n[i])>.5
    return {'schema':'kalends-environment-validation-v1','glb_sha256':hashlib.sha256(raw).hexdigest(),'glb_header_and_lengths_valid':True,'all_accessor_ranges_valid':True,'all_indices_in_range':True,'all_values_finite':True,'all_normals_unit':True,'box_surface_winding_outward':True,'embedded_images':len(doc['images']),'triangles':triangles,'material_batches':sum(len(x['primitives']) for x in doc['meshes']),'group_triangles':groups,'scope':'Offline structural/model validation. Actual composition, shaders and performance require native browser inspection.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    model=Model();terrain_and_backdrop(model);paving(model);frontage(model);bakery(model);south_buildings(model);greenery(model);market_cart(model);interior_cutaway_walls(model)
    gltf,stats=export_glb(model,args.output/'pompeii_district.glb')
    allp=np.concatenate([np.asarray(m.p) for m in model.groups.values()]);stats['bounds']={'min':allp.min(axis=0).tolist(),'max':allp.max(axis=0).tolist()}
    model.metadata.update({'schema':'kalends-environment-v1','glb':'pompeii_district.glb','world_scale':SCALE,'origin':list(ORIGIN),'axis':'right-handed Y up, sim y maps to positive Z','stats':stats,'license':'Original project-authored geometry/procedural textures, no third-party source; project rights reserved pending its release terms. Embedded Poly Haven CC0 textures have separate official provenance in ../materials/materials.json; see LICENSE.txt','furniture_navigation':'All fixed props are outside approved room inset floors and public floor rectangles. Curbs/thresholds are visual margins; no new collider is claimed.','architectural_disclosure':'Roman-inspired hand-authored procedural mesh reconstruction. Business identities and commerce are fictional. Measurements are the existing schematic map, not surveyed Pompeii.'})
    (args.output/'scene_manifest.json').write_text(json.dumps(model.metadata,indent=2)+'\n')
    validation=validate_glb(args.output/'pompeii_district.glb')
    (args.output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
