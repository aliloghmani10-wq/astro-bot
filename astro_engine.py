import swisseph as swe
import datetime, pytz, math

for _p in ['/usr/share/swisseph','/usr/local/share/swisseph','./ephe']:
    try:
        swe.set_ephem_path(_p)
        break
    except:
        pass

PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
    'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE,
    'Pluto': swe.PLUTO, 'N.Node': swe.MEAN_NODE,
}
PLANET_SYM = {
    'Sun':'☉','Moon':'☽','Mercury':'☿','Venus':'♀','Mars':'♂',
    'Jupiter':'♃','Saturn':'♄','Uranus':'♅','Neptune':'♆',
    'Pluto':'♇','N.Node':'☊',
}
PLANET_FA = {
    'Sun':'خورشید','Moon':'ماه','Mercury':'عطارد','Venus':'زهره',
    'Mars':'مریخ','Jupiter':'مشتری','Saturn':'زحل','Uranus':'اورانوس',
    'Neptune':'نپتون','Pluto':'پلوتو','N.Node':'گره شمالی',
}
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_SYM = ['♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓']
SIGN_FA = ['حمل','ثور','جوزا','سرطان','اسد','سنبله',
           'میزان','عقرب','قوس','جدی','دلو','حوت']
SIGN_ELEM = [0,1,2,3,0,1,2,3,0,1,2,3]

def _lon2sign(lon):
    idx = int(lon // 30)
    d = lon % 30
    return idx, int(d), int((d - int(d)) * 60)

def to_julian(y, m, d, h, mi, tz='Asia/Tehran'):
    tz = pytz.timezone(tz)
    dt = tz.localize(datetime.datetime(y, m, d, h, mi))
    utc = dt.astimezone(pytz.UTC)
    return swe.julday(utc.year, utc.month, utc.day,
                      utc.hour + utc.minute/60.0 + utc.second/3600.0)

def calc_positions(jd, system='tropical'):
    if system == 'sidereal':
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    else:
        flags = swe.FLG_SWIEPH
    out = {}
    for name, pid in PLANETS.items():
        try:
            res, _ = swe.calc_ut(jd, pid, flags)
        except:
            try:
                res, _ = swe.calc_ut(jd, pid, swe.FLG_MOSEPH)
            except:
                continue
        lon = res[0]
        si, deg, mn = _lon2sign(lon)
        out[name] = {
            'lon': lon, 'si': si, 'sign': SIGNS[si],
            'sign_sym': SIGN_SYM[si], 'sign_fa': SIGN_FA[si],
            'deg': deg, 'min': mn, 'sym': PLANET_SYM[name],
            'fa': PLANET_FA[name], 'elem': SIGN_ELEM[si],
        }
    return out

def calc_houses(jd, lat, lon):
    try:
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    except:
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    houses = []
    for c in cusps:
        si, deg, mn = _lon2sign(c)
        houses.append({'lon': c, 'si': si, 'sign': SIGNS[si],
                       'sign_sym': SIGN_SYM[si], 'sign_fa': SIGN_FA[si],
                       'deg': deg, 'min': mn})
    asi, ad, am = _lon2sign(ascmc[0])
    msi, md, mm = _lon2sign(ascmc[1])
    return {
        'cusps': houses,
        'asc': {'lon': ascmc[0], 'si': asi, 'sign': SIGNS[asi],
                'sign_fa': SIGN_FA[asi], 'deg': ad, 'min': am},
        'mc':  {'lon': ascmc[1], 'si': msi, 'sign': SIGNS[msi],
                'sign_fa': SIGN_FA[msi], 'deg': md, 'min': mm},
    }

def calc_aspects(positions, orb=8):
    angles = {'Conjunction':0,'Sextile':60,'Square':90,'Trine':120,'Opposition':180}
    syms = {'Conjunction':'☌','Sextile':'⚹','Square':'□','Trine':'△','Opposition':'☍'}
    out = []
    names = list(positions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            diff = abs(positions[names[i]]['lon'] - positions[names[j]]['lon'])
            if diff > 180: diff = 360 - diff
            for aname, angle in angles.items():
                if abs(diff - angle) <= orb:
                    out.append({'p1':names[i],'p2':names[j],
                                'name':aname,'sym':syms[aname],
                                'orb':round(abs(diff-angle),2)})
                    break
    return out

def calc_transit(birth_positions):
    now = datetime.datetime.now(pytz.UTC)
    jd = swe.julday(now.year, now.month, now.day, now.hour + now.minute/60.0)
    t_pos = calc_positions(jd, 'tropical')
    angles = {'Conjunction':0,'Sextile':60,'Square':90,'Trine':120,'Opposition':180}
    aspects = []
    for tn, tp in t_pos.items():
        for bn, bp in birth_positions.items():
            diff = abs(tp['lon'] - bp['lon'])
            if diff > 180: diff = 360 - diff
            for aname, angle in angles.items():
                if abs(diff - angle) <= 3:
                    aspects.append({'tp':tn,'bp':bn,'name':aname,
                                    'orb':round(abs(diff-angle),2)})
                    break
    return t_pos, aspects

def now_jd():
    n = datetime.datetime.now(pytz.UTC)
    return swe.julday(n.year, n.month, n.day, n.hour + n.minute/60.0)
