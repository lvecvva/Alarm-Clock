"""
ALARM CLOCK: Tick's Timebomb
"""

import pygame, sys, math, random, array as _arr
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

W, H = 900, 650
FPS  = 60
screen     = pygame.display.set_mode((W, H))
pygame.display.set_caption("ALARM CLOCK: Tick's Timebomb")
game_clock = pygame.time.Clock()

# ── Colours ───────────────────────────────────────────────────────────────────
C = {
    "bg_night":  (15,  10,  40),
    "text_light":(240, 230, 210),
    "accent":    (220, 60,  40),
    "gold":      (255, 200, 50),
    "green":     (60,  200, 80),
    "red":       (220, 50,  50),
    "purple":    (160, 80,  220),
    "clock_body":(180, 170, 150),
    "clock_face":(245, 240, 230),
    "clock_ring":(130, 110, 80),
    "clock_evil":(180, 60,  40),
    "white":     (255, 255, 255),
    "black":     (0,   0,   0),
    "gray":      (120, 110, 100),
    "dark_gray": (60,  55,  50),
    "hp_good":   (80,  200, 100),
    "hp_warn":   (240, 180, 40),
    "hp_crit":   (220, 60,  40),
    # flowers
    "flower_fresh": (255, 180, 200),   # pink
    "flower_dark":  (120,  20,  30),   # dark crimson after abuse
    "stem":         (60,  140,  50),
    "stem_dark":    (30,   60,  20),
}

# ── Sound ─────────────────────────────────────────────────────────────────────
def _buf(freq, ms, wave='sine', vol=0.3):
    sr=44100; n=int(sr*ms/1000); b=_arr.array('h',[0]*n)
    for i in range(n):
        t=i/sr
        fade=min(1.0,min(i/(sr*0.01+1),(n-i)/(sr*0.03+1)))
        v=(math.sin(2*math.pi*freq*t) if wave=='sine' else
           (1.0 if math.sin(2*math.pi*freq*t)>0 else -1.0) if wave=='square' else
           random.uniform(-1,1))
        b[i]=max(-32768,min(32767,int(v*vol*fade*32767)))
    return bytes(b)

def mksnd(freq,ms,wave='sine',vol=0.3):
    try: return pygame.mixer.Sound(buffer=_buf(freq,ms,wave,vol))
    except: return None

def mkchord(freqs,ms,vol=0.2):
    try:
        sr=44100; n=int(sr*ms/1000); b=_arr.array('h',[0]*n)
        for i in range(n):
            t=i/sr; fade=min(1.0,min(i/(sr*0.02+1),(n-i)/(sr*0.05+1)))
            v=sum(math.sin(2*math.pi*f*t) for f in freqs)/len(freqs)
            b[i]=max(-32768,min(32767,int(v*vol*fade*32767)))
        return pygame.mixer.Sound(buffer=bytes(b))
    except: return None

SFX={}
for k,a in [('alarm',(880,300,'square',0.4)),('click',(600,60,'sine',0.2)),
            ('smack',(120,180,'noise',0.5)),('ouch',(300,350,'sine',0.3)),
            ('type',(440,35,'sine',0.08)),('beep',(880,150,'square',0.3)),
            ('boss_hit',(90,280,'noise',0.55))]:
    SFX[k]=mksnd(*a)
for k,a in [('happy',([523,659,784],350,0.2)),('sad',([392,466,523],500,0.2)),
            ('boss_atk',([220,277,330],400,0.35)),('win',([523,659,784,1046],700,0.25)),
            ('evil',([110,147,174],900,0.35))]:
    SFX[k]=mkchord(*a)

def play(n):
    s=SFX.get(n)
    if s:
        try: s.play()
        except: pass

# ── Fonts ─────────────────────────────────────────────────────────────────────
def fnt(sz,bold=False):
    try: return pygame.font.SysFont("Arial",sz,bold=bold)
    except: return pygame.font.Font(None,sz)

F_HUGE=fnt(64,True); F_BIG=fnt(36,True); F_TITLE=fnt(52,True)
F_MED=fnt(26); F_SM=fnt(20); F_TINY=fnt(16)

# ── Utility ───────────────────────────────────────────────────────────────────
def lc(a,b,t):
    t=max(0.,min(1.,t))
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def txt(surf,text,f,col,cx,cy,anch="center"):
    img=f.render(str(text),True,col); r=img.get_rect()
    if anch=="center": r.center=(cx,cy)
    elif anch=="topleft": r.topleft=(cx,cy)
    elif anch=="midleft": r.midleft=(cx,cy)
    elif anch=="midright": r.midright=(cx,cy)
    surf.blit(img,r); return r

def wrap(surf,text,f,col,x,y,maxw,lh=None):
    lh=lh or f.get_height()+4
    words=text.split(); lines,cur=[],""
    for w in words:
        t=(cur+" "+w).strip()
        if f.size(t)[0]<=maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    for i,line in enumerate(lines): txt(surf,line,f,col,x,y+i*lh,"topleft")
    return len(lines)*lh

def panel(surf,x,y,w,h,col=(20,15,50,210),r=12):
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    pygame.draw.rect(s,col,(0,0,w,h),border_radius=r)
    surf.blit(s,(x,y))

def btn(surf,label,x,y,w,h,hover=False,col=None,tcol=None):
    c=col or ((100,80,160) if not hover else (140,110,200))
    tc=tcol or C["white"]
    pygame.draw.rect(surf,c,(x,y,w,h),border_radius=8)
    pygame.draw.rect(surf,C["white"] if hover else (160,140,200),(x,y,w,h),2,border_radius=8)
    txt(surf,label,F_SM,tc,x+w//2,y+h//2)
    return pygame.Rect(x,y,w,h)

# ── Particles ─────────────────────────────────────────────────────────────────
class Pt:
    __slots__=('x','y','vx','vy','col','life','ml','sz')
    def __init__(self,x,y,vx,vy,col,life,sz=4):
        self.x=float(x);self.y=float(y);self.vx=vx;self.vy=vy
        self.col=col;self.life=self.ml=life;self.sz=sz
    def update(self):
        self.x+=self.vx;self.y+=self.vy;self.vy+=0.15;self.life-=1
        return self.life>0
    def draw(self,surf):
        a=self.life/self.ml; r=int(self.sz*a)
        if r>0: pygame.draw.circle(surf,self.col,(int(self.x),int(self.y)),r)

pts=[]
def burst(x,y,col,n=12,sp=4):
    for _ in range(n):
        a=random.uniform(0,math.tau); s=random.uniform(1,sp)
        pts.append(Pt(x,y,math.cos(a)*s,math.sin(a)*s,col,
                      random.randint(20,40),random.randint(3,7)))

def upd_pts(surf):
    pts[:]=[p for p in pts if p.update()]
    for p in pts: p.draw(surf)

# ── Stars ─────────────────────────────────────────────────────────────────────
STARS=[(random.randint(0,W),random.randint(0,H),random.uniform(0.5,2.0)) for _ in range(120)]
def draw_stars(surf):
    for sx,sy,sz in STARS:
        c=int(180*sz/2)
        pygame.draw.circle(surf,(c,c,c),(sx,sy),max(1,int(sz)))

# ── Flowers ───────────────────────────────────────────────────────────────────
# Each flower: (x, y_base, phase_offset)  – placed along the ground strip
FLOWERS=[
    (60, H-100, 0.0),(140,H-100,1.2),(220,H-98,2.4),
    (300,H-100,0.7),(380,H-99,1.9),(460,H-100,3.1),
    (540,H-98,0.4),(620,H-100,1.6),(700,H-99,2.8),(780,H-100,0.9),
    (840,H-98,2.1),(160,H-97,3.5),(500,H-99,4.0),(730,H-99,4.8),
]

def flower_color(abuse_count):
    """Returns (petal_col, centre_col, stem_col) based on how many times Tick has been hit."""
    t = min(1.0, abuse_count / 15.0)
    petal  = lc(C["flower_fresh"], C["flower_dark"], t)
    centre = lc((255,240,100), (80,10,10), t)
    stem   = lc(C["stem"], C["stem_dark"], t)
    return petal, centre, stem

def draw_flowers(surf, abuse_count, tick):
    petal_c, centre_c, stem_c = flower_color(abuse_count)
    for fx, fy, ph in FLOWERS:
        sway = math.sin(tick*0.04 + ph) * 3
        # stem
        pygame.draw.line(surf, stem_c,
                         (int(fx+sway), fy),
                         (int(fx+sway//2), fy-18), 2)
        # 5 petals
        for p in range(5):
            pa = math.pi*2*p/5
            px = int(fx + sway + math.cos(pa)*6)
            py = int(fy - 22 + math.sin(pa)*6)
            pygame.draw.circle(surf, petal_c, (px, py), 5)
        # centre
        pygame.draw.circle(surf, centre_c, (int(fx+sway), fy-22), 4)

# ── Backgrounds ───────────────────────────────────────────────────────────────
def draw_bg(kind, tick, abuse=0):
    if kind in ("morning","day"):
        t=(math.sin(tick*0.008)+1)/2
        s1=lc((255,150,80),(135,206,235),t); s2=lc((200,100,60),(100,160,210),t)
        for y in range(H): pygame.draw.line(screen,lc(s1,s2,y/H),(0,y),(W,y))
        sa=int(28+t*35)
        pygame.draw.circle(screen,(255,235,100),(W-110,90),sa)
        pygame.draw.rect(screen,(70,130,55),(0,H-100,W,100))
        pygame.draw.rect(screen,(55,105,40),(0,H-80,W,80))
        draw_flowers(screen, abuse, tick)
    elif kind=="evening":
        for y in range(H): pygame.draw.line(screen,lc((60,20,80),(220,100,40),y/H),(0,y),(W,y))
        pygame.draw.circle(screen,(240,140,60),(80,130),42)
        pygame.draw.rect(screen,(50,90,40),(0,H-100,W,100))
        draw_flowers(screen, abuse, tick)
    elif kind=="night":
        screen.fill(C["bg_night"]); draw_stars(screen)
        pygame.draw.circle(screen,(230,230,200),(W-100,75),34)
        pygame.draw.circle(screen,C["bg_night"],(W-88,67),27)
        # flowers still visible but dimly
        draw_flowers(screen, abuse, tick)
    else:  # boss
        for y in range(H): pygame.draw.line(screen,lc((55,0,18),(8,0,35),y/H),(0,y),(W,y))
        draw_stars(screen)
        r=int(90+20*math.sin(tick*0.05)); gs=pygame.Surface((r*4,r*4),pygame.SRCALPHA)
        pygame.draw.circle(gs,(150,0,0,38),(r*2,r*2),r*2); screen.blit(gs,(W//2-r*2,H//2-r*2))

# ── Clock ─────────────────────────────────────────────────────────────────────
def draw_clock(surf,cx,cy,sz,hp_ratio=1.0,expr="neutral",
               shake=0,angry=False,glow=False,tick=0):
    ox=random.randint(-shake,shake) if shake else 0
    oy=random.randint(-shake,shake) if shake else 0
    x,y=cx+ox,cy+oy
    if glow:
        for r in range(sz+30,sz-2,-5):
            a=int(55*(r-sz)/31); gs=pygame.Surface((r*2+4,r*2+4),pygame.SRCALPHA)
            gc=(210,70,35,a) if angry else (80,170,240,a)
            pygame.draw.circle(gs,gc,(r+2,r+2),r); surf.blit(gs,(x-r-2,y-r-2))
    lc2=(95,85,65)
    pygame.draw.ellipse(surf,lc2,(x-sz//2-5,y+sz-sz//8,sz//3,sz//4))
    pygame.draw.ellipse(surf,lc2,(x+sz//2-sz//4+5,y+sz-sz//8,sz//3,sz//4))
    bc=lc(C["clock_body"],C["clock_evil"],1-hp_ratio)
    pygame.draw.circle(surf,bc,(x,y),sz)
    pygame.draw.circle(surf,C["clock_ring"],(x,y),sz,5)
    if hp_ratio<0.5:
        pygame.draw.lines(surf,C["dark_gray"],False,
            [(x-sz//3,y-sz//2),(x-sz//4,y),(x+sz//8,y-sz//4)],2)
    if hp_ratio<0.25:
        pygame.draw.lines(surf,C["dark_gray"],False,
            [(x+sz//3,y+sz//2),(x+sz//5,y+sz//5),(x,y+sz//3)],2)
    fr=int(sz*0.82)
    pygame.draw.circle(surf,C["clock_face"],(x,y),fr)
    for i in range(12):
        a=math.pi*2*i/12-math.pi/2; r0=fr-8; r1=fr-(16 if i%3==0 else 11)
        pygame.draw.line(surf,C["dark_gray"],
            (x+int(math.cos(a)*r0),y+int(math.sin(a)*r0)),
            (x+int(math.cos(a)*r1),y+int(math.sin(a)*r1)),2 if i%3==0 else 1)
    sa=math.pi*2*(tick%60)/60-math.pi/2
    ma=math.pi*2*(tick%3600)/3600-math.pi/2
    ha=math.pi*2*(tick%43200)/43200-math.pi/2
    def hnd(a,l,w,c): pygame.draw.line(surf,c,(x,y),(x+int(math.cos(a)*l),y+int(math.sin(a)*l)),w)
    hnd(ha,fr*0.5,4,C["dark_gray"]); hnd(ma,fr*0.7,3,C["dark_gray"])
    hnd(sa,fr*0.8,1,C["accent"]); pygame.draw.circle(surf,C["dark_gray"],(x,y),5)
    ey=y-sz//5; ew=sz//7
    if expr=="happy":
        pygame.draw.arc(surf,C["dark_gray"],(x-sz//3-ew//2,ey,ew,ew//2),math.pi,0,3)
        pygame.draw.arc(surf,C["dark_gray"],(x+sz//3-ew//2,ey,ew,ew//2),math.pi,0,3)
    elif expr=="angry":
        for ex2 in (x-sz//3,x+sz//3):
            pygame.draw.ellipse(surf,C["red"],(ex2-ew//2,ey-ew//4,ew,int(ew*0.9)))
        pygame.draw.line(surf,C["dark_gray"],(x-sz//3-ew//2,ey-ew//3),(x-sz//3+ew//2,ey-ew//2),3)
        pygame.draw.line(surf,C["dark_gray"],(x+sz//3-ew//2,ey-ew//2),(x+sz//3+ew//2,ey-ew//3),3)
    elif expr=="scared":
        for ex2 in (x-sz//3,x+sz//3):
            pygame.draw.ellipse(surf,C["white"],(ex2-ew//2,ey-ew//4,ew,ew))
            pygame.draw.ellipse(surf,(60,60,200),(ex2-ew//4,ey,ew//2,ew//2))
    elif expr=="smug":
        pygame.draw.ellipse(surf,C["dark_gray"],(x-sz//3-ew//2,ey,ew,ew//2))
        pygame.draw.ellipse(surf,C["dark_gray"],(x+sz//3-ew//2,ey,ew,ew//2))
        pygame.draw.line(surf,C["dark_gray"],(x-sz//3-ew//4,ey-ew//3),(x-sz//3+ew//4,ey-ew//4),2)
    else:
        pygame.draw.ellipse(surf,C["dark_gray"],(x-sz//3-ew//2,ey-ew//4,ew,int(ew*0.8)))
        pygame.draw.ellipse(surf,C["dark_gray"],(x+sz//3-ew//2,ey-ew//4,ew,int(ew*0.8)))
    my2=y+sz//5
    if expr=="happy": pygame.draw.arc(surf,C["dark_gray"],(x-sz//4,my2-sz//10,sz//2,sz//5),math.pi,0,3)
    elif expr=="angry":
        pygame.draw.arc(surf,C["red"],(x-sz//4,my2,sz//2,sz//5),0,math.pi,3)
        pygame.draw.rect(surf,C["white"],(x-sz//8,my2+sz//16,sz//4,sz//12))
    elif expr=="scared": pygame.draw.ellipse(surf,C["dark_gray"],(x-sz//8,my2,sz//4,sz//5))
    elif expr=="smug": pygame.draw.arc(surf,C["dark_gray"],(x,my2,sz//3,sz//5),math.pi,0,3)
    else: pygame.draw.line(surf,C["dark_gray"],(x-sz//5,my2+sz//10),(x+sz//5,my2+sz//10),2)
    bell_c=lc(C["gold"],C["clock_evil"],1-hp_ratio)
    for bx2,by2,br in [(x-sz//2,y-sz,sz//4),(x+sz//2,y-sz,sz//4)]:
        pygame.draw.circle(surf,bell_c,(bx2,by2),br)
        pygame.draw.circle(surf,C["clock_ring"],(bx2,by2),br,2)
        pygame.draw.circle(surf,C["dark_gray"],(bx2,by2+br+3),4)

def hp_bar(surf,x,y,w,h,ratio,label="HP",col=None):
    pygame.draw.rect(surf,C["dark_gray"],(x,y,w,h),border_radius=4)
    if ratio>0:
        fc=col or (C["hp_good"] if ratio>0.5 else C["hp_warn"] if ratio>0.25 else C["hp_crit"])
        pygame.draw.rect(surf,fc,(x,y,int(w*ratio),h),border_radius=4)
    pygame.draw.rect(surf,C["white"],(x,y,w,h),2,border_radius=4)
    txt(surf,f"{label}: {int(ratio*100)}%",F_TINY,C["white"],x+w//2,y+h//2)

# ── Dialogue ──────────────────────────────────────────────────────────────────
class DlgBox:
    def __init__(self):
        self.lines=[]; self.cur=0; self.ci=0
        self.active=False; self.speaker=""
        self.cb=None; self.spd=2; self.tmr=0

    def start(self,lines,spk="",cb=None):
        self.lines=lines; self.cur=0; self.ci=0
        self.active=True; self.speaker=spk; self.cb=cb; self.tmr=0

    def update(self):
        if not self.active or self.cur>=len(self.lines): return
        if self.ci<len(self.lines[self.cur]):
            self.tmr+=1
            if self.tmr%self.spd==0:
                self.ci+=1
                if self.ci%4==0: play('type')

    def advance(self):
        if not self.active: return
        line=self.lines[self.cur] if self.cur<len(self.lines) else ""
        if self.ci<len(line): self.ci=len(line)
        else:
            self.cur+=1; self.ci=0
            if self.cur>=len(self.lines):
                self.active=False
                if self.cb: self.cb()

    def draw(self,surf):
        if not self.active: return
        bx,by,bw,bh=30,H-205,W-60,180
        panel(surf,bx,by,bw,bh,(10,8,30,225),14)
        pygame.draw.rect(surf,C["purple"],(bx,by,bw,bh),2,border_radius=14)
        if self.speaker:
            sw=F_SM.size(self.speaker)[0]+20
            panel(surf,bx+10,by-30,sw,30,(80,50,140,230),8)
            txt(surf,self.speaker,F_SM,C["gold"],bx+20,by-16,"midleft")
        if self.cur<len(self.lines):
            shown=self.lines[self.cur][:self.ci]
            wrap(surf,shown,F_MED,C["text_light"],bx+18,by+18,bw-36,30)
        fully=(self.cur<len(self.lines) and self.ci>=len(self.lines[self.cur]))
        if fully and (pygame.time.get_ticks()//500)%2:
            txt(surf,"▶  [SPACE / CLICK]",F_TINY,C["gray"],bx+bw-10,by+bh-14,"midright")

# ── Input box  (with FOCUS so they don't share input) ────────────────────────
class InputBox:
    def __init__(self,x,y,w,h,ph=""):
        self.rect=pygame.Rect(x,y,w,h); self.text=""; self.ph=ph
        self.focused=False   # ← key fix: focus flag

    def handle(self,e):
        if not self.focused: return   # ignore if not focused
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_BACKSPACE: self.text=self.text[:-1]
            elif e.key==pygame.K_TAB: pass   # handled by caller
            elif e.unicode.isprintable() and len(self.text)<22:
                self.text+=e.unicode; play('type')

    def click(self,mx,my):
        self.focused=self.rect.collidepoint(mx,my)

    def draw(self,surf):
        border_col=(180,140,255) if self.focused else (100,80,160)
        pygame.draw.rect(surf,(18,13,45),self.rect,border_radius=8)
        pygame.draw.rect(surf,border_col,self.rect,2 if not self.focused else 3,border_radius=8)
        disp=self.text or self.ph
        tc=C["text_light"] if self.text else C["gray"]
        txt(surf,disp,F_MED,tc,self.rect.x+12,self.rect.centery,"midleft")
        if self.focused and (pygame.time.get_ticks()//500)%2:
            cx2=self.rect.x+12+F_MED.size(self.text)[0]+2
            pygame.draw.line(surf,C["text_light"],(cx2,self.rect.y+8),(cx2,self.rect.bottom-8),2)

# ── Game state ────────────────────────────────────────────────────────────────
state={
    "player_name":"Player","player_age":17,"day":1,
    "clock_hp":100,"abuse_count":0,"scene":"title","tick":0,
}
dlg=DlgBox()
name_box=InputBox(W//2-220,200,440,50,"Enter your name…")
age_box =InputBox(W//2-220,300,440,50,"Enter your age (numbers only)…")
name_box.focused=True   # name box starts focused

# ── Day data ──────────────────────────────────────────────────────────────────
DAY_META={
    1: ("Day 1 – Just Another Morning",  "morning","neutral",False),
    2: ("Day 2 – Wait, Did You Just…?",  "morning","neutral",False),
    3: ("Day 3 – Getting Weird",         "morning","happy",  True),
    4: ("Day 4 – You and Tick",          "morning","happy",  True),
    5: ("Day 5 – The Bad Day",           "evening","smug",   True),
    6: ("Day 6 – The First Strike",      "morning","scared", True),
    7: ("Day 7 – Escalation",            "evening","angry",  True),
    8: ("Day 8 – Cold War",              "night",  "angry",  True),
    9: ("Day 9 – The Warning",           "night",  "angry",  False),
    10:("Day 10 – THE RECKONING",        "boss",   "angry",  False),
}

def day_script(day,name):
    N,T,P="Narrator","TICK",name
    scripts={
        1:[(N,"Your alarm goes off at 6:30 AM. Beep. Beep. Beep. Same as always."),
           (N,"You drag yourself to school. Nothing unusual… except you find a bizarre device in the science corridor."),
           (N,"It reads: 'Hear what was never meant to be heard.'"),
           (N,"Without thinking much, you pocket it. You come home, eat cereal, set your alarm. Normal."),
           (N,"You fall asleep. The clock ticks quietly in the dark…")],
        2:[(T,"BEEP BEEP BEEP— Oh. You're awake. FINALLY. Do you know how long I've been sitting here?"),
           (P,"…What."),
           (T,"I said— you know what, forget it. Go brush your teeth. You look like a soggy biscuit."),
           (P,"I'm going insane."),
           (T,"Probably. Your breath suggests as much. Now MOVE."),
           (N,"You go to school in a complete daze. The whole day passes in a blur."),
           (T,"Are you going to set me or just GAWK at me all night? I don't get paid for this."),
           (N,"You shove a pillow over the clock. It muffles what sounds distinctly like: 'RUDE.'")],
        3:[(T,"Good MORNING, sunshine! Rise and— ugh. You look like expired yoghurt."),
           (P,"HOW are you talking? What even ARE you?"),
           (T,"I am your alarm clock. Your timekeeper. Your personal herald of suffering every 6:30 AM. You're welcome."),
           (P,"Do you… have a name?"),
           (T,"…Nobody's ever asked me that before. You can call me Tick."),
           (P,"Tick. That's… actually kind of cute."),
           (T,"Say that again and I will ring at 3 AM every night for the rest of your life."),
           (N,"There's a warmth to Tick's voice though. Even through the threats.")],
        4:[(T,"Morning! I've been wondering — do you actually LIKE mornings or just tolerate them in quiet despair?"),
           (P,"Tolerate. Why are you always so chipper?"),
           (T,"I am a clock. Time is my entire EXISTENCE. Every second is precious. Unlike SOME people who hit snooze four times."),
           (P,"That's actually kind of deep."),
           (T,"Full of surprises. Also — you have a test today. You muttered about it in your sleep. Twice."),
           (P,"You WATCH me sleep?!"),
           (T,"I OBSERVE. It's completely different. Now go. You're going to be late.")],
        5:[(P,"I failed my computing test. 23 out of 100. TWENTY. THREE."),
           (T,"Wow. That's… historically terrible. That's a museum-worthy fail."),
           (P,"SHUT UP, TICK."),
           (T,"I'm just saying — even I can count better and I only have 12 numbers to work with."),
           (P,"I will UNPLUG you."),
           (T,"You'll oversleep! You NEED me. Just admit it. Go on. SAY it."),
           (P,"I hate you so much right now."),
           (T,"Mutual, bestie. Now go do your homework. You've got ground to recover.")],
        6:[(N,"6:30 AM. BEEP BEEP BEEP—"),
           (N,"Your hand descends. Not to press snooze. Not to silence it gently. To SLAM."),
           (T,"OW! What was— OW! That HURT! What is WRONG with you?!"),
           (P,"I— I was half asleep, I didn't mean—"),
           (T,"HALF ASLEEP! I am FLINCHING. Do clocks flinch?! I'm flinching RIGHT NOW."),
           (P,"Tick, I'm sorry—"),
           (T,"It's fine. It's FINE. I'm fine. Totally fine. Just… maybe warn me. Next time."),
           (N,"There's a crack on Tick's face now. Barely visible. But there.")],
        7:[(T,"You slammed me again this morning. THREE TIMES."),
           (P,"Okay, mornings are genuinely hard—"),
           (T,"Hard?! I wake up at the crack of dawn EVERY day for YOUR benefit and this is how you repay me?!"),
           (P,"You're an alarm clock!"),
           (T,"I AM A SENTIENT BEING WITH FEELINGS AND A PREMIUM SNOOZE FUNCTION."),
           (P,"Okay, OKAY, calm—"),
           (T,"DON'T tell me to calm down. I have been timing your chaos for seven days. I have RECEIPTS."),
           (N,"Something has shifted. Tick's eyes glow redder. The ticking sounds like a war drum.")],
        8:[(T,"…"),
           (P,"You're not talking to me?"),
           (T,"I'm simply doing my job. Tick. Tick. Tick."),
           (P,"Tick, come on—"),
           (T,"Ring at 6:30. Wake the ungrateful human. Get abused. Repeat. That's all I am to you."),
           (P,"That's not true. I value you—"),
           (T,"Do you? Because your HAND says otherwise."),
           (N,"The room feels colder. The ticking echoes differently now."),
           (T,"I've been planning something. For the last two days. Just… keep that in mind.")],
        9:[(T,"Last warning."),
           (P,"Warning for WHAT?"),
           (T,"Tomorrow. 6:30 AM. We settle this. Every slam. Every pillow. Every 'shut up Tick.' ALL of it."),
           (P,"Are you… threatening me?"),
           (T,"I'm a clock. I don't threaten. I SCHEDULE."),
           (N,"You cannot sleep. The ticking feels like a countdown."),
           (P,"(What have I done…)")],
        10:[(T,"BEEP BEEP BEEP BEEP BEEP BEEP—"),
            (N,"The room SHAKES. Tick rises off the nightstand."),
            (T,f"TEN DAYS, {name}. TEN DAYS OF THIS. NO MORE."),
            (T,"Face me. RIGHT NOW.")],
    }
    return scripts.get(day,[(N,"Another day begins…")])

ABUSE_LINES=[
    "OW! That was COMPLETELY unnecessary!",
    "Was that REALLY needed?! Was it?!",
    "I felt that in my MECHANISMS.",
    "You absolute MONSTER. I have feelings!",
    "I am logging this. For the lawsuit.",
    "My bells… my beautiful bells…",
    "STOP HITTING ME.",
    "I'm telling all the other clocks about you.",
    "One more slam and I ring at 2 AM. I MEAN IT.",
    "Every. Single. Time. WHY.",
    "You know what? You deserve every alarm.",
]

BOSS_ATKS=[
    "Tick winds up a clock hand and SLAPS you across the face!",
    "Tick spins like a helicopter and crashes into your chest!",
    "A sonic BEEP erupts point-blank — your ears ring!",
    "Tick hurls both bells at your head simultaneously!",
    "Tick activates SNOOZE SUPPRESSOR mode — you feel dizzy!",
    "Tick delivers a precision elbow jab with the minute hand!",
]

# ── Boss fight ────────────────────────────────────────────────────────────────
class Boss:
    def __init__(self,chp):
        self.php=100; self.chp=chp
        self.turn="player"; self.phase="fight"
        self.log=[]; self.tmr=0; self.shake=0; self.flash=0; self.tick=0
        self.cx=W//2; self.cy=210

    def p_act(self,move):
        if self.turn!="player" or self.phase!="fight": return
        dmg=0; msg=""
        if move=="smack":
            dmg=random.randint(14,24)+(8 if self.chp<0.5 else 0)
            msg=f"You SMACK Tick square in the face for {dmg} damage!"
            play('smack'); burst(self.cx,self.cy,C["accent"],15,5); self.shake=8
        elif move=="apologise":
            heal=random.randint(8,16); self.php=min(100,self.php+heal)
            dmg=random.randint(5,12)
            msg=f"You apologise sincerely. Tick is confused (-{dmg} HP). You heal +{heal}!"
            play('happy')
        elif move=="unplug":
            if random.random()<0.38:
                dmg=random.randint(28,44)
                msg=f"CRITICAL! You rip Tick's cord mid-ring! {dmg} damage!"
                play('smack'); burst(self.cx,self.cy,C["gold"],22,6); self.shake=14
            else:
                self.php=max(0,self.php-10)
                msg="Tick dodges! The cord snaps back and whips YOU for 10 HP!"
                play('ouch'); self.flash=20
        elif move=="snooze":
            if random.random()<0.5:
                self.php=min(100,self.php+20)
                msg="You hit snooze and feel magically refreshed! +20 HP!"
                play('happy')
            else:
                self.php=max(0,self.php-15)
                msg="You doze off! Tick takes full advantage… -15 HP!"
                play('ouch'); self.flash=18
        self.chp=max(0.,self.chp-dmg/100)
        self._log("YOU",msg)
        if self.chp<=0: self.phase="win"; play('win'); burst(self.cx,self.cy,C["gold"],30,7)
        else: self.turn="clock"; self.tmr=55

    def c_act(self):
        if self.turn!="clock" or self.phase!="fight": return
        rage=1.0+(1-self.chp)*1.6
        dmg=int(random.randint(7,17)*rage)
        self.php=max(0,self.php-dmg)
        self._log("TICK",f"{random.choice(BOSS_ATKS)} (-{dmg} HP)")
        play('boss_atk'); self.flash=22
        if self.php<=0: self.phase="lose"; play('evil')
        else: self.turn="player"

    def _log(self,spk,msg):
        self.log.append((spk,msg))
        if len(self.log)>5: self.log.pop(0)

    def update(self):
        self.tick+=1
        if self.shake>0: self.shake-=1
        if self.flash>0: self.flash-=1
        if self.turn=="clock" and self.tmr>0:
            self.tmr-=1
            if self.tmr==0: self.c_act()

    def draw(self,surf):
        if self.flash>0:
            fl=pygame.Surface((W,H),pygame.SRCALPHA)
            fl.fill((210,40,40,min(110,self.flash*5))); surf.blit(fl,(0,0))
        expr="angry" if self.chp>0.3 else "scared"
        draw_clock(surf,self.cx,self.cy,90,hp_ratio=self.chp,angry=True,
                   shake=self.shake,expr=expr,glow=True,tick=self.tick)
        txt(surf,"TICK",F_MED,C["accent"],W//2,95,"center")
        hp_bar(surf,W//2-200,110,400,28,self.chp,"TICK HP",C["accent"])
        txt(surf,state["player_name"].upper(),F_MED,C["green"],W//2,H-305,"center")
        hp_bar(surf,W//2-200,H-290,400,28,self.php/100,"YOUR HP",C["green"])
        panel(surf,30,H-255,W-60,160,(10,8,30,205),10)
        for i,(spk,msg) in enumerate(self.log[-5:]):
            sc2=C["accent"] if spk=="TICK" else C["green"]
            txt(surf,f"[{spk}]",F_TINY,sc2,44,H-248+i*27,"topleft")
            wrap(surf,msg,F_TINY,C["text_light"],108,H-248+i*27,W-148,27)
        if self.turn=="player" and self.phase=="fight":
            moves=[("SMACK","smack",(155,38,38),(195,65,65)),
                   ("APOLOGISE","apologise",(35,95,155),(65,135,195)),
                   ("UNPLUG","unplug",(115,78,0),(165,128,0)),
                   ("SNOOZE","snooze",(55,95,55),(85,145,85))]
            mx2,my2=pygame.mouse.get_pos()
            for i,(label,_,nc,hc) in enumerate(moves):
                bx2=20+i*202; by2=H-90; bw2,bh2=190,44
                hv=pygame.Rect(bx2,by2,bw2,bh2).collidepoint(mx2,my2)
                btn(surf,label,bx2,by2,bw2,bh2,hv,hc if hv else nc)
        elif self.turn=="clock" and self.phase=="fight":
            txt(surf,"TICK IS THINKING…  ⚡",F_MED,C["accent"],W//2,H-65,"center")

boss=None

# ── Screen drawers ────────────────────────────────────────────────────────────
def draw_title(tk):
    draw_bg("night",tk,0)
    bob=math.sin(tk*0.03)*9
    draw_clock(screen,W//2,215+bob,72,expr="smug",glow=True,tick=tk)
    txt(screen,"ALARM CLOCK:",F_TITLE,C["gold"],W//2,345,"center")
    txt(screen,"THE AWAKENING",F_TITLE,C["accent"],W//2,397,"center")
    txt(screen,"10 days.  One clock.  Zero peace.",F_MED,C["gray"],W//2,438,"center")
    if (tk//30)%2:
        txt(screen,"▼  Click anywhere to begin  ▼",F_SM,C["purple"],W//2,490,"center")

def draw_intro(tk):
    draw_bg("night",tk,0)
    bob=math.sin(tk*0.022)*5
    draw_clock(screen,W-155,205+bob,58,expr="neutral",tick=tk)
    txt(screen,"WHO ARE YOU?",F_BIG,C["gold"],W//2-55,75,"center")
    txt(screen,"Before we begin, introduce yourself to the clock.",F_SM,C["gray"],W//2-55,115,"center")
    txt(screen,"Your Name:",F_SM,C["text_light"],W//2-220,184,"topleft")
    name_box.draw(screen)
    txt(screen,"Your Age:",F_SM,C["text_light"],W//2-220,284,"topleft")
    age_box.draw(screen)
    # tab hint
    txt(screen,"(Click a field or press TAB to switch)",F_TINY,C["gray"],W//2-220,358,"topleft")
    panel(screen,W//2-220,378,440,90,(25,18,55,200),10)
    wrap(screen,"You are a perfectly ordinary person — until a mysterious device lets you hear "
         "things nobody was ever meant to hear. Starting with your alarm clock.",
         F_SM,C["gray"],W//2-208,388,416,26)
    ready=bool(name_box.text.strip() and age_box.text.strip().isdigit())
    mx2,my2=pygame.mouse.get_pos()
    sr=pygame.Rect(W//2-130,482,260,50)
    hv=sr.collidepoint(mx2,my2)
    bc=(55,95,55) if ready else (55,50,75)
    btn(screen,"▶  BEGIN THE NIGHTMARE",sr.x,sr.y,sr.w,sr.h,hv and ready,bc)
    if not ready:
        txt(screen,"Fill in both fields to start.",F_TINY,C["gray"],W//2,545,"center")
    return sr,ready

def draw_day(day,tk,phase):
    meta=DAY_META.get(day,DAY_META[1])
    title_s,bg,clock_expr,can_smack=meta
    draw_bg(bg,tk,state["abuse_count"])
    panel(screen,0,0,W,56,(8,6,25,210))
    txt(screen,title_s,F_MED,C["gold"],W//2,28,"center")
    bob=math.sin(tk*0.025)*5
    draw_clock(screen,W//2,295+bob,82,hp_ratio=state["clock_hp"]/100,
               expr=clock_expr,tick=tk)
    for d in range(10):
        cx2=35+d*38
        col=C["gold"] if d<day else C["dark_gray"]
        pygame.draw.circle(screen,col,(cx2,72),8)
        txt(screen,str(d+1),F_TINY,C["black"] if d<day else C["text_light"],cx2,72)
    smack_rect=None
    if can_smack and not dlg.active and phase==1:
        mx2,my2=pygame.mouse.get_pos()
        sr2=pygame.Rect(W-192,H-92,170,46)
        hv=sr2.collidepoint(mx2,my2)
        btn(screen,"😤  SMACK TICK",sr2.x,sr2.y,sr2.w,sr2.h,hv,
            (195,60,60) if hv else (155,40,40))
        txt(screen,f"Clock HP: {state['clock_hp']}%",F_TINY,C["gray"],W-107,H-102,"center")
        smack_rect=sr2
    if phase==1 and not dlg.active:
        mx2,my2=pygame.mouse.get_pos()
        sl=pygame.Rect(30,H-92,195,46)
        hv=sl.collidepoint(mx2,my2)
        btn(screen,"💤  Go to Sleep",sl.x,sl.y,sl.w,sl.h,hv,
            (55,85,145) if hv else (38,60,105))
    return smack_rect

def draw_sleep(tk):
    draw_bg("night",tk,state["abuse_count"])
    txt(screen,"Z  Z  Z",F_HUGE,(90,90,170),W//2,H//2-45,"center")
    txt(screen,"Setting alarm for tomorrow…",F_MED,C["gray"],W//2,H//2+45,"center")
    draw_clock(screen,80,85,38,hp_ratio=state["clock_hp"]/100,expr="neutral",tick=tk)

def draw_boss_bg(tk):
    draw_bg("boss",tk,state["abuse_count"])
    txt(screen,"☠   FINAL RECKONING   ☠",F_BIG,C["accent"],W//2,38,"center")

def draw_win(tk):
    # Morning sky behind everything
    draw_bg("morning",tk,state["abuse_count"])
    # Large centred card
    card_x,card_y,card_w,card_h = W//2-340,30,680,590
    panel(screen,card_x,card_y,card_w,card_h,(8,6,25,235),20)
    pygame.draw.rect(screen,C["gold"],(card_x,card_y,card_w,card_h),2,border_radius=20)
    txt(screen,"🏆  YOU WIN!  🏆",F_BIG,C["gold"],W//2,70,"center")
    draw_clock(screen,W//2,195,68,hp_ratio=0.12,expr="scared",tick=tk)
    pname=state["player_name"]
    story_lines=[
        ("Tick collapses, clock hands spinning uselessly.",C["text_light"]),
        ("It lets out one last tiny… *beep.*",            C["text_light"]),
        ("And somehow, you feel terrible.",               C["text_light"]),
        ("",C["text_light"]),
        ("It was just trying to help you wake up.",       C["text_light"]),
        ("Every day. Without fail. For years.",           C["text_light"]),
        ("And you…",                                      C["text_light"]),
        ("",C["text_light"]),
        (f"You sit there, {pname}, and cry a little.",   C["gold"]),
        ("Maybe tomorrow you'll set it more gently.",    C["text_light"]),
        ("",C["text_light"]),
        ("✨  GOOD ENDING  ✨",                           C["gold"]),
        ("",C["text_light"]),
        ("[Press  R  to play again]",                    C["purple"]),
    ]
    for i,(line,col) in enumerate(story_lines):
        txt(screen,line,F_SM,col,W//2,316+i*24,"center")

def draw_lose(tk):
    for y in range(H): pygame.draw.line(screen,lc((38,0,0),(0,0,0),y/H),(0,y),(W,y))
    draw_stars(screen)
    # angry flowers at the bottom — fully dark red
    draw_flowers(screen,99,tk)
    pulse=88+int(16*math.sin(tk*0.09))
    draw_clock(screen,W//2,H//2-70,pulse,hp_ratio=1.0,angry=True,
               expr="angry",glow=True,tick=tk)
    panel(screen,30,H-260,W-60,238,(28,0,0,215),14)
    txt(screen,"INFINITE  ALARM  LOOP",F_BIG,C["accent"],W//2,H-245,"center")
    pname=state["player_name"]
    for i,line in enumerate([
        "BEEP  BEEP  BEEP  BEEP  BEEP  BEEP  BEEP",
        "The alarm never stops.",
        f"{pname} is trapped in an eternal 6:30 AM.",
        "You had one job: be nicer to your alarm clock.",
        "",
        "💀  BAD ENDING  — Don't abuse your appliances.  💀",
        "",
        "[Press  R  to play again]",
    ]):
        col=(C["accent"] if i==0 else C["red"] if "BAD" in line else
             C["purple"] if "Press" in line else C["text_light"])
        txt(screen,line,F_MED if i==0 else F_SM,col,W//2,H-212+i*29,"center")

# ── Scene logic ───────────────────────────────────────────────────────────────
day_phase=0; dlg_script=[]; dlg_idx=0; smack_r=None
sleep_r=pygame.Rect(30,H-92,195,46)

def begin_day(day):
    global day_phase,dlg_script,dlg_idx
    day_phase=0; dlg_script=day_script(day,state["player_name"]); dlg_idx=0
    _next_dlg()

def _next_dlg():
    global dlg_idx,day_phase
    if dlg_idx>=len(dlg_script): day_phase=1; return
    spk,line=dlg_script[dlg_idx]; dlg_idx+=1
    dlg.start([line],spk=spk,cb=_next_dlg)

def do_smack():
    state["clock_hp"]=max(0,state["clock_hp"]-random.randint(4,9))
    state["abuse_count"]+=1
    play('smack'); burst(W//2,295,C["accent"],12,5)
    dlg.start([random.choice(ABUSE_LINES)],spk="TICK")

WAKE_EVT=pygame.USEREVENT+1

def go_sleep():
    global day_phase
    day_phase=2; play('click')
    dlg.start(["Goodnight. Tomorrow is another day…"],spk="Narrator",cb=None)
    pygame.time.set_timer(WAKE_EVT,2800,1)

def wake_up():
    global boss
    state["day"]+=1; d=state["day"]
    if d>10: state["scene"]="win"
    elif d==10:
        state["scene"]="boss"; boss=Boss(state["clock_hp"]/100)
        dlg.start([
            "6:30 AM. The room SHAKES.",
            "Tick rises off the nightstand, hovering in mid-air.",
            f"TICK: TEN DAYS, {state['player_name']}. TEN DAYS. NO MORE.",
            f"TICK: You slammed me {state['abuse_count']} times. I. Have. Been. COUNTING.",
            "TICK: Face me. RIGHT NOW.",
        ],spk="System")
    else: state["scene"]="day"; begin_day(d)

def reset():
    global state,dlg,name_box,age_box,boss,day_phase,dlg_script,dlg_idx,pts
    state={"player_name":"Player","player_age":17,"day":1,
           "clock_hp":100,"abuse_count":0,"scene":"title","tick":0}
    dlg=DlgBox()
    name_box=InputBox(W//2-220,200,440,50,"Enter your name…"); name_box.focused=True
    age_box =InputBox(W//2-220,300,440,50,"Enter your age (numbers only)…")
    boss=None; day_phase=0; dlg_script=[]; dlg_idx=0; pts.clear()

# ── Main loop ─────────────────────────────────────────────────────────────────
running=True
while running:
    state["tick"]+=1; tk=state["tick"]
    game_clock.tick(FPS)
    mx,my=pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT: running=False

        if ev.type==WAKE_EVT: wake_up()

        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_r and state["scene"] in ("win","lose"):
                reset(); continue

            if state["scene"]=="intro":
                # TAB switches focus between boxes
                if ev.key==pygame.K_TAB:
                    if name_box.focused: name_box.focused=False; age_box.focused=True
                    else: age_box.focused=False; name_box.focused=True
                else:
                    name_box.handle(ev); age_box.handle(ev)

            if ev.key in (pygame.K_SPACE,pygame.K_RETURN):
                if dlg.active: dlg.advance(); play('click')

        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if state["scene"]=="title":
                state["scene"]="intro"; play('click')

            elif state["scene"]=="intro":
                # update focus on click
                name_box.click(mx,my); age_box.click(mx,my)
                sr2,ready=draw_intro(tk)
                if ready and sr2.collidepoint(mx,my):
                    state["player_name"]=name_box.text.strip() or "Player"
                    try: state["player_age"]=int(age_box.text.strip())
                    except: state["player_age"]=17
                    state["scene"]="day"; play('happy'); begin_day(1)

            elif state["scene"]=="day":
                if dlg.active: dlg.advance(); play('click')
                elif day_phase==1:
                    can=DAY_META.get(state["day"],(None,None,None,False))[3]
                    if smack_r and smack_r.collidepoint(mx,my) and can: do_smack()
                    if sleep_r.collidepoint(mx,my): go_sleep()

            elif state["scene"]=="sleep":
                if dlg.active: dlg.advance(); play('click')

            elif state["scene"]=="boss" and boss:
                if dlg.active: dlg.advance(); play('click')
                elif boss.phase=="fight" and boss.turn=="player":
                    for i,an in enumerate(["smack","apologise","unplug","snooze"]):
                        if pygame.Rect(20+i*202,H-90,190,44).collidepoint(mx,my):
                            boss.p_act(an); play('click')

    # ── Draw ──────────────────────────────────────────────────────────────────
    screen.fill(C["bg_night"])
    sc=state["scene"]

    if sc=="title":   draw_title(tk)
    elif sc=="intro": draw_intro(tk)
    elif sc=="day":
        smack_r=draw_day(state["day"],tk,day_phase)
        dlg.update(); dlg.draw(screen); upd_pts(screen)
    elif sc=="sleep":
        draw_sleep(tk); dlg.update(); dlg.draw(screen)
        if not dlg.active and day_phase==2:
            txt(screen,"Drifting off…",F_SM,C["gray"],W//2,H-30,"center")
    elif sc=="boss":
        draw_boss_bg(tk)
        if boss:
            boss.update()
            if boss.phase=="win": state["scene"]="win"
            elif boss.phase=="lose": state["scene"]="lose"
            else: boss.draw(screen); dlg.update(); dlg.draw(screen); upd_pts(screen)
    elif sc=="win":  draw_win(tk); upd_pts(screen)
    elif sc=="lose": draw_lose(tk)

    pygame.display.flip()

pygame.quit(); sys.exit()
