from PIL import Image, ImageDraw, ImageFont
import math, os, urllib.request

C = {
    'bg':(10,10,26), 'bg2':(20,20,50), 'ring':(88,166,255),
    'ring2':(48,54,61), 'house':(72,79,88), 'asc':(247,129,102),
    'txt':(230,237,243), 'dim':(139,148,158),
    'fire':(248,81,73), 'earth':(63,185,80),
    'air':(88,166,255), 'water':(188,140,255),
    'conj':(240,230,140), 'sextile':(88,166,255),
    'square':(248,81,73), 'trine':(63,185,80), 'opp':(248,81,73),
    'gold':(212,168,67), 'gold2':(139,115,50),
    'transit':(247,129,102), 'natal':(88,166,255),
}
EC = {0:C['fire'],1:C['earth'],2:C['air'],3:C['water']}
PC = {
    'Sun':(255,215,0),'Moon':(192,192,210),'Mercury':(255,165,0),
    'Venus':(255,105,180),'Mars':(255,69,0),'Jupiter':(147,112,219),
    'Saturn':(180,140,90),'Uranus':(0,206,209),'Neptune':(65,105,225),
    'Pluto':(180,80,180),'N.Node':(200,200,200),
}
AC = {'Conjunction':C['conj'],'Sextile':C['sextile'],
      'Square':C['square'],'Trine':C['trine'],'Opposition':C['opp']}
ZS = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
PS = {'Sun':'☉','Moon':'☽','Mercury':'☿','Venus':'♀','Mars':'♂',
      'Jupiter':'♃','Saturn':'♄','Uranus':'♅','Neptune':'♆',
      'Pluto':'♇','N.Node':'☊'}

_BASE = os.path.dirname(os.path.abspath(__file__))

def _ensure_font():
    fd = os.path.join(_BASE, 'fonts')
    os.makedirs(fd, exist_ok=True)
    fp = os.path.join(fd, 'Vazirmatn-Regular.ttf')
    if not os.path.exists(fp):
        try:
            urllib.request.urlretrieve(
                'https://github.com/rastikerdar/vazirmatn/raw/main/fonts/ttf/Vazirmatn-Regular.ttf', fp)
        except:
            pass
    return fp

def _font(size):
    for p in [_ensure_font(),
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

def _sf(size):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
              _ensure_font()]:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

def _bg(sz, c1=C['bg'], c2=C['bg2']):
    img = Image.new('RGB', sz, c1)
    draw = ImageDraw.Draw(img)
    cx, cy = sz[0]//2, sz[1]//2
    mr = int(math.sqrt(cx**2+cy**2))
    for r in range(mr, 0, -6):
        t = r/mr
        col = tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))
        draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=col)
    return img

def _la(lon, asc):
    return math.radians(180-(lon-asc))

def _avoid(angles, gap=0.13):
    placed, res = [], []
    for a in angles:
        adj = a
        for p in placed:
            if abs(adj-p) < gap: adj = p + gap
        placed.append(adj)
        res.append(adj)
    return res

def _table(draw, pos, sz, font, accent):
    y0 = sz - 200
    draw.line([(40,y0-10),(sz-40,y0-10)], fill=accent, width=1)
    draw.text((50,y0), 'Planet Positions:', fill=accent, font=font)
    y0 += 30
    col, row = 0, 0
    for pn, p in pos.items():
        x = 50 + col*320
        y = y0 + row*24
        pc = PC.get(pn, C['dim'])
        txt = f"{PS.get(pn,'?')}  {p['fa']}:  {p['deg']}°{p['min']}'  {p['sign_sym']} {p['sign_fa']}"
        draw.text((x,y), txt, fill=pc, font=font)
        row += 1
        if row > 5: row = 0; col += 1

# ═══════════ TROPICAL / SIDEREAL ═══════════
def draw_circular(name, positions, houses, aspects, mode='tropical', date_str=''):
    SZ = 1400
    CX, CY = SZ//2, SZ//2+20
    RO, RS, RH, RP, RA = 560, 505, 430, 370, 290

    if mode == 'sidereal':
        acc, acc2 = C['gold'], C['gold2']
        bg1, bg2 = (18,14,8), (35,28,15)
        label = 'Sidereal (Lahiri)'
    else:
        acc, acc2 = C['ring'], C['ring2']
        bg1, bg2 = C['bg'], C['bg2']
        label = 'Tropical'

    img = _bg((SZ,SZ), bg1, bg2)
    draw = ImageDraw.Draw(img)
    ft = _font(32); fs = _font(18); fsign = _sf(26)
    fp = _sf(22); fd = _font(13); fi = _font(15)
    asc_lon = houses['asc']['lon'] if houses else 0

    draw.text((CX,35), name, fill=C['txt'], font=ft, anchor='mt')
    draw.text((CX,75), f'{label} Natal Chart', fill=acc2, font=fs, anchor='mt')
    if date_str:
        draw.text((CX,100), date_str, fill=C['dim'], font=_font(14), anchor='mt')

    for r,col,w in [(RO,acc,3),(RS,acc2,1),(RH,acc2,2),(RA,acc2,1)]:
        draw.ellipse([CX-r,CY-r,CX+r,CY+r], outline=col, width=w)

    for i in range(12):
        a1 = _la(asc_lon+i*30, asc_lon)
        a2 = _la(asc_lon+(i+1)*30, asc_lon)
        si = (houses['asc']['si']+i)%12 if houses else i
        ec = EC[si%4]
        for r in range(RS+2, RO-2, 3):
            for s in range(25):
                ang = a1+(a2-a1)*(s/25)
                x1 = CX+r*math.cos(ang); y1 = CY-r*math.sin(ang)
                x2 = CX+(r+3)*math.cos(ang); y2 = CY-(r+3)*math.sin(ang)
                faint = tuple(min(255,int(c*0.15+bg1[j]*0.85)) for j,c in enumerate(ec))
                draw.line([(x1,y1),(x2,y2)], fill=faint, width=3)

    for i in range(12):
        ang = _la(asc_lon+i*30, asc_lon)
        draw.line([(CX+RH*math.cos(ang),CY-RH*math.sin(ang)),
                   (CX+RO*math.cos(ang),CY-RO*math.sin(ang))], fill=acc2, width=1)

    for i in range(12):
        mid = _la(asc_lon+i*30+15, asc_lon)
        rm = (RS+RO)//2
        si = (houses['asc']['si']+i)%12 if houses else i
        draw.text((CX+rm*math.cos(mid), CY-rm*math.sin(mid)),
                  ZS[si], fill=EC[si%4], font=fsign, anchor='mm')

    if houses:
        for i, cusp in enumerate(houses['cusps']):
            ang = _la(cusp['lon'], asc_lon)
            x1 = CX+RA*math.cos(ang); y1 = CY-RA*math.sin(ang)
            if i in (0,9):
                x2 = CX+(RO+15)*math.cos(ang); y2 = CY-(RO+15)*math.sin(ang)
                draw.line([(x1,y1),(x2,y2)], fill=C['asc'], width=3)
            else:
                x2 = CX+RH*math.cos(ang); y2 = CY-RH*math.sin(ang)
                draw.line([(x1,y1),(x2,y2)], fill=C['house'], width=1)
        for lbl, key in [('ASC','asc'),('MC','mc')]:
            ang = _la(houses[key]['lon'], asc_lon)
            draw.text((CX+(RO+35)*math.cos(ang), CY-(RO+35)*math.sin(ang)),
                      lbl, fill=C['asc'], font=fi, anchor='mm')

    pa = {n: _la(p['lon'], asc_lon) for n,p in positions.items()}
    for asp in aspects:
        if asp['p1'] in pa and asp['p2'] in pa:
            r_a = RA*0.9
            x1 = CX+r_a*math.cos(pa[asp['p1']]); y1 = CY-r_a*math.sin(pa[asp['p1']])
            x2 = CX+r_a*math.cos(pa[asp['p2']]); y2 = CY-r_a*math.sin(pa[asp['p2']])
            draw.line([(x1,y1),(x2,y2)], fill=AC.get(asp['name'],C['dim']), width=1)

    sp = sorted(positions.items(), key=lambda x: x[1]['lon'])
    raw = [_la(p['lon'], asc_lon) for _,p in sp]
    adj = _avoid(raw)
    for idx,(pn,pos) in enumerate(sp):
        ang = adj[idx]; pc = PC.get(pn, C['txt'])
        px = CX+RH*math.cos(ang); py = CY-RH*math.sin(ang)
        sx = CX+RP*math.cos(ang); sy = CY-RP*math.sin(ang)
        draw.line([(px,py),(sx,sy)], fill=C['house'], width=1)
        draw.ellipse([px-4,py-4,px+4,py+4], fill=pc)
        draw.ellipse([sx-16,sy-16,sx+16,sy+16], fill=(20,20,40), outline=pc, width=2)
        draw.text((sx,sy), PS.get(pn,'?'), fill=pc, font=fp, anchor='mm')
        draw.text((sx,sy+22), f"{pos['deg']}°{pos['min']}'", fill=C['dim'], font=fd, anchor='mm')

    _table(draw, positions, SZ, fi, acc)
    return img

# ═══════════ DIAMOND ═══════════
def draw_diamond(name, positions, houses, aspects, date_str=''):
    SZ = 1400; CX, CY = SZ//2, SZ//2+20; H = 480
    img = _bg((SZ,SZ), (8,16,12), (16,32,24))
    draw = ImageDraw.Draw(img)
    ft = _font(32); fs = _font(18); fsign = _sf(28)
    fp = _sf(24); fd = _font(14); fh = _font(16); fi = _font(15)
    acc = (80,220,160); acc2 = (40,110,80)
    asc_si = houses['asc']['si'] if houses else 0

    draw.text((CX,35), name, fill=C['txt'], font=ft, anchor='mt')
    draw.text((CX,75), 'Diamond Chart (North Indian)', fill=acc2, font=fs, anchor='mt')
    if date_str:
        draw.text((CX,100), date_str, fill=C['dim'], font=_font(14), anchor='mt')

    T=(CX,CY-H); R=(CX+H,CY); B=(CX,CY+H); L=(CX-H,CY)
    MTR=((T[0]+R[0])//2,(T[1]+R[1])//2)
    MBR=((R[0]+B[0])//2,(R[1]+B[1])//2)
    MBL=((B[0]+L[0])//2,(B[1]+L[1])//2)
    MTL=((L[0]+T[0])//2,(L[1]+T[1])//2)

    draw.polygon([T,R,B,L], outline=acc)
    for p1,p2 in [(T,MBL),(T,MBR),(R,MTL),(R,MBL),(B,MTL),(B,MTR),(L,MTR),(L,MBR)]:
        draw.line([p1,p2], fill=acc2, width=2)
    draw.polygon([T,R,B,L], outline=acc)

    hc = {
        1:(CX,CY-H*0.58), 2:(CX+H*0.32,CY-H*0.32),
        3:(CX+H*0.58,CY-H*0.08), 4:(CX+H*0.58,CY+H*0.08),
        5:(CX+H*0.32,CY+H*0.32), 6:(CX,CY+H*0.58),
        7:(CX-H*0.32,CY+H*0.32), 8:(CX-H*0.58,CY+H*0.08),
        9:(CX-H*0.58,CY-H*0.08), 10:(CX-H*0.32,CY-H*0.32),
        11:(CX-H*0.12,CY-H*0.42), 12:(CX+H*0.12,CY-H*0.42),
    }
    hp = {i:[] for i in range(1,13)}
    for pn,pos in positions.items():
        hn = ((pos['si']-asc_si)%12)+1
        hp[hn].append(pn)

    for hn in range(1,13):
        cx_h, cy_h = hc[hn]
        si = (asc_si+hn-1)%12
        draw.text((cx_h-35,cy_h-30), str(hn), fill=C['dim'], font=fh)
        draw.text((cx_h+20,cy_h-30), ZS[si], fill=EC[si%4], font=fsign)
        for pi,pn in enumerate(hp[hn]):
            pos = positions[pn]; pc = PC.get(pn, C['txt'])
            yy = cy_h+5+pi*32
            draw.ellipse([cx_h-14,yy-14,cx_h+14,yy+14], fill=(15,25,20), outline=pc, width=2)
            draw.text((cx_h,yy), PS.get(pn,'?'), fill=pc, font=fp, anchor='mm')
            draw.text((cx_h+22,yy), f"{pos['deg']}°{pos['min']}'", fill=C['dim'], font=fd, anchor='lm')

    _table(draw, positions, SZ, fi, acc)
    return img

# ═══════════ TRANSIT ═══════════
def draw_transit(name, bpos, tpos, tasp, houses, date_str=''):
    SZ = 1400; CX, CY = SZ//2, SZ//2+20
    RO,RT,RS,RH,RB,RA = 560,520,470,410,360,280
    img = _bg((SZ,SZ), (18,10,20), (35,20,40))
    draw = ImageDraw.Draw(img)
    ft=_font(32); fs=_font(18); fsign=_sf(26); fp=_sf(20); fi=_font(15); fd=_font(13)
    asc_lon = houses['asc']['lon'] if houses else 0

    draw.text((CX,35), f'{name} — Transit', fill=C['transit'], font=ft, anchor='mt')
    draw.text((CX,75), 'Current Transits over Natal', fill=C['dim'], font=fs, anchor='mt')
    if date_str:
        draw.text((CX,100), date_str, fill=C['dim'], font=_font(14), anchor='mt')

    for r,col,w in [(RO,C['transit'],3),(RT,C['house'],1),(RS,C['ring2'],1),(RH,C['ring2'],2),(RA,C['ring2'],1)]:
        draw.ellipse([CX-r,CY-r,CX+r,CY+r], outline=col, width=w)

    for i in range(12):
        ang = _la(asc_lon+i*30, asc_lon)
        draw.line([(CX+RH*math.cos(ang),CY-RH*math.sin(ang)),
                   (CX+RO*math.cos(ang),CY-RO*math.sin(ang))], fill=C['ring2'], width=1)

    for i in range(12):
        mid = _la(asc_lon+i*30+15, asc_lon)
        rm = (RS+RO)//2
        si = (houses['asc']['si']+i)%12 if houses else i
        draw.text((CX+rm*math.cos(mid),CY-rm*math.sin(mid)),
                  ZS[si], fill=EC[si%4], font=fsign, anchor='mm')

    ba = {n:_la(p['lon'],asc_lon) for n,p in bpos.items()}
    ta = {n:_la(p['lon'],asc_lon) for n,p in tpos.items()}
    for asp in tasp:
        if asp['tp'] in ta and asp['bp'] in ba:
            x1=CX+RA*0.95*math.cos(ta[asp['tp']]); y1=CY-RA*0.95*math.sin(ta[asp['tp']])
            x2=CX+RA*0.75*math.cos(ba[asp['bp']]); y2=CY-RA*0.75*math.sin(ba[asp['bp']])
            draw.line([(x1,y1),(x2,y2)], fill=AC.get(asp['name'],C['dim']), width=1)

    sb = sorted(bpos.items(), key=lambda x:x[1]['lon'])
    ab = _avoid([_la(p['lon'],asc_lon) for _,p in sb])
    for idx,(pn,pos) in enumerate(sb):
        ang=ab[idx]; sx=CX+RB*math.cos(ang); sy=CY-RB*math.sin(ang)
        px=CX+RH*math.cos(ang); py=CY-RH*math.sin(ang)
        draw.line([(px,py),(sx,sy)], fill=C['house'], width=1)
        draw.ellipse([px-3,py-3,px+3,py+3], fill=C['natal'])
        draw.ellipse([sx-14,sy-14,sx+14,sy+14], fill=(15,15,30), outline=C['natal'], width=2)
        draw.text((sx,sy), PS.get(pn,'?'), fill=C['natal'], font=fp, anchor='mm')

    st = sorted(tpos.items(), key=lambda x:x[1]['lon'])
    at = _avoid([_la(p['lon'],asc_lon) for _,p in st])
    for idx,(pn,pos) in enumerate(st):
        ang=at[idx]; sx=CX+RT*math.cos(ang); sy=CY-RT*math.sin(ang)
        draw.ellipse([sx-14,sy-14,sx+14,sy+14], fill=(30,15,15), outline=C['transit'], width=2)
        draw.text((sx,sy), PS.get(pn,'?'), fill=C['transit'], font=fp, anchor='mm')

    draw.ellipse([50,SZ-100,66,SZ-84], fill=C['natal'])
    draw.text((75,SZ-92), '= Natal', fill=C['dim'], font=fi, anchor='lm')
    draw.ellipse([200,SZ-100,216,SZ-84], fill=C['transit'])
    draw.text((225,SZ-92), '= Transit', fill=C['dim'], font=fi, anchor='lm')

    draw.text((50,SZ-220), 'Active Transits:', fill=C['transit'], font=fi)
    for i,asp in enumerate(tasp[:10]):
        txt = f"{PS.get(asp['tp'],'')} {asp['tp']}  {asp['name']}  {PS.get(asp['bp'],'')} {asp['bp']}  (orb {asp['orb']}°)"
        draw.text((50,SZ-195+i*20), txt, fill=C['dim'], font=fd)
    return img
