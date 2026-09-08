#!/usr/bin/env python3
"""Build data/econ.json (v2) from the raw Eurostat / IMF / WB / ONS pulls made by fetch_econ_sources.py.
Usage: ECON_RAW=<raw dir> python3 scripts/build_econ.py data/econ.json docs/gdp-research-notes.md"""
import csv, json, os, sys
RAW = os.environ.get('ECON_RAW', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw'))
OUT_JSON = sys.argv[1]
OUT_NOTES = sys.argv[2]
YEARS = list(range(1995, 2032))
N = len(YEARS)
FX = 1.1095
FC_FROM = 2026
GENERATED = '2026-09-07'

# iso3 -> (eurostat geo, name)
C = {
 'ALB':('AL','Albania'),'AUT':('AT','Austria'),'BEL':('BE','Belgium'),'BGR':('BG','Bulgaria'),
 'BIH':('BA','Bosnia and Herzegovina'),'BLR':('BY','Belarus'),'CHE':('CH','Switzerland'),'CYP':('CY','Cyprus'),
 'CZE':('CZ','Czechia'),'DEU':('DE','Germany'),'DNK':('DK','Denmark'),'ESP':('ES','Spain'),'EST':('EE','Estonia'),
 'FIN':('FI','Finland'),'FRA':('FR','France'),'GBR':('UK','United Kingdom'),'GEO':('GE','Georgia'),'GRC':('EL','Greece'),
 'HRV':('HR','Croatia'),'HUN':('HU','Hungary'),'IRL':('IE','Ireland'),'ISL':('IS','Iceland'),'ITA':('IT','Italy'),
 'LTU':('LT','Lithuania'),'LUX':('LU','Luxembourg'),'LVA':('LV','Latvia'),'MKD':('MK','North Macedonia'),'MLT':('MT','Malta'),
 'MNE':('ME','Montenegro'),'NLD':('NL','Netherlands'),'NOR':('NO','Norway'),'POL':('PL','Poland'),'PRT':('PT','Portugal'),
 'ROU':('RO','Romania'),'RUS':('RU','Russia'),'SRB':('RS','Serbia'),'SVK':('SK','Slovakia'),'SVN':('SI','Slovenia'),
 'SWE':('SE','Sweden'),'UKR':('UA','Ukraine'),
}

def jl(f): return json.load(open(os.path.join(RAW, f)))
def es_series(d, geo):
    dim = d['dimension']; idx = dim['geo']['category']['index']; tidx = dim['time']['category']['index']
    nT = d['size'][-1]; gi = idx.get(geo)
    if gi is None: return {}
    # status flags
    st = d.get('status', {})
    out = {}
    for y, ti in tidx.items():
        k = str(gi*nT+ti)
        if k in d['value']: out[int(y)] = (d['value'][k], st.get(k))
    return out

ES_GDP = jl('es_gdp.json'); ES_PC = jl('es_pc.json'); ES_PE = jl('es_pe.json'); ES_DEMO = jl('es_demo.json')
IMF_G = jl('imf_rpch.json')['values']['NGDP_RPCH']; IMF_N = jl('imf_ngdpd.json')['values']['NGDPD']; IMF_LP = jl('imf_lp.json')['values']['LP']
ONS_ABMI = {int(y['year']): float(y['value']) for y in jl('ons_abmi.json')['years']}
ONS_POP = {int(y['year']): float(y['value']) for y in jl('ons_ukpop.json')['years']}
ONS_ABMI_REL = jl('ons_abmi.json')['description']['releaseDate'][:10]
ONS_POP_REL = jl('ons_ukpop.json')['description']['releaseDate'][:10]

def wb_csv(path):
    rows = list(csv.reader(open(path, encoding='utf-8-sig')))
    upd = [r for r in rows if r and r[0] == 'Last Updated Date'][0][1]
    hdr_i = [i for i, r in enumerate(rows) if r and r[0] == 'Country Name'][0]
    hdr = rows[hdr_i]; out = {}
    for r in rows[hdr_i+1:]:
        if len(r) < 5: continue
        out[r[1]] = {int(h): float(v) for h, v in zip(hdr[4:], r[4:]) if h.strip().isdigit() and v.strip()}
    return out, upd
WB_GDP, WB_UPD = wb_csv([os.path.join(RAW,'wbg',f) for f in os.listdir(os.path.join(RAW,'wbg')) if f.startswith('API_')][0])
WB_POP, _ = wb_csv([os.path.join(RAW,'wbp',f) for f in os.listdir(os.path.join(RAW,'wbp')) if f.startswith('API_')][0])

def imf_g(iso, y):
    v = IMF_G.get(iso, {}).get(str(y)); return None if v is None else float(v)
def imf_lp(iso, y):
    v = IMF_LP.get(iso, {}).get(str(y)); return None if v is None else float(v)
def wb_g(iso, y):
    s = WB_GDP.get(iso, {});
    return None if y not in s or (y-1) not in s else s[y]/s[y-1]-1
def wb_popratio(iso, y):
    s = WB_POP.get(iso, {});
    return None if y not in s or (y-1) not in s else s[y]/s[y-1]

def yi(y): return YEARS.index(y)

report = {}   # per-country diagnostics for Notes
countries = {}

def build(iso):
    geo, name = C[iso]
    gdp = [None]*N; pc = [None]*N; pop = [None]*N; src = [None]*N
    gsrc = [None]*N; psrc = [None]*N   # component sources for coding
    notes = []
    esg = es_series(ES_GDP, geo); esp = es_series(ES_PC, geo); espe = es_series(ES_PE, geo); esd = es_series(ES_DEMO, geo)
    flags = {y: f for y, (v, f) in esg.items() if f}
    chained_growth = {}   # year -> growth used (for check)

    # ---- 1. Eurostat verbatim GDP (and pc where published)
    for y, (v, f) in esg.items():
        gdp[yi(y)] = round(v, 1); gsrc[yi(y)] = 'ES'
    for y, (v, f) in esp.items():
        if gdp[yi(y)] is not None:
            pc[yi(y)] = int(round(v)); pop[yi(y)] = gdp[yi(y)]/pc[yi(y)]; psrc[yi(y)] = 'ES'
    # Eurostat national-accounts population where pc not published
    for y, (v, f) in espe.items():
        i = yi(y)
        if gdp[i] is not None and pop[i] is None:
            pop[i] = v/1000.0; psrc[i] = 'ES'

    # ---- 2. Non-Eurostat anchors
    anchor = None; territory = None
    if iso in ('RUS', 'BLR', 'GEO'):
        n15 = float(IMF_N[iso]['2015']); g15 = n15*1000/FX
        gdp[yi(2015)] = round(g15, 1); gsrc[yi(2015)] = 'IMF'
        anchor = {'year': 2015, 'gdp_usd_bn': n15, 'source': 'IMF WEO April 2026 NGDPD, converted at ECB 2015 average 1.1095 USD/EUR'}
    if iso == 'GBR':
        n15 = float(IMF_N['GBR']['2015']); g15 = n15*1000/FX
        gdp[yi(2015)] = round(g15, 1); gsrc[yi(2015)] = 'NAT'
        anchor = {'year': 2015, 'gdp_usd_bn': n15, 'source': 'IMF WEO April 2026 NGDPD, converted at ECB 2015 average 1.1095 USD/EUR; volumes chained with ONS ABMI'}
    if iso == 'UKR':
        n15 = float(IMF_N['UKR']['2015'])
        anchor = {'year': 2015, 'gdp_usd_bn': n15,
                  'source': 'Level taken verbatim from Eurostat nama_10_gdp (UA, CLV15_MEUR) for 2010-2024; the IMF NGDPD anchor (%.3f bn USD / 1.1095 = %.0f MEUR) differs from it by %+.2f%%' % (n15, n15*1000/FX, (n15*1000/FX/gdp[yi(2015)]-1)*100)}

    # ---- 3. GDP growth chaining: forward then backward from any known value
    def growth(y):
        """real growth for year y (t-1 -> t) and its source code"""
        if iso == 'GBR' and y in ONS_ABMI and (y-1) in ONS_ABMI and y <= 2025:
            return ONS_ABMI[y]/ONS_ABMI[y-1]-1, 'NAT'
        if iso == 'MLT' and y == 2000:
            # WB NY.GDP.MKTP.KD has a splice artifact (+19.7 %) at 1999->2000 for Malta; UN National Accounts
            # Main Aggregates (Download-GDPgrowth-USD-countries.xlsx, updated 2026-01-28) gives 6.69999 % and is
            # identical to WB for 1996-1999. Coded WB (no separate code exists for UN AMA).
            return 0.066999921457596034, 'WB'
        g = imf_g(iso, y)
        if g is not None: return g/100.0, ('FC' if y >= FC_FROM else 'IMF')
        w = wb_g(iso, y)
        if w is not None: return w, 'WB'
        return None, None
    # forward
    for i in range(1, N):
        if gdp[i] is None and gdp[i-1] is not None:
            g, s = growth(YEARS[i])
            if g is None: continue
            gdp[i] = round(gdp[i-1]*(1+g), 1); gsrc[i] = s; chained_growth[YEARS[i]] = g
    # backward
    for i in range(N-2, -1, -1):
        if gdp[i] is None and gdp[i+1] is not None:
            g, s = growth(YEARS[i+1])
            if g is None: continue
            gdp[i] = round(gdp[i+1]/(1+g), 1); gsrc[i] = s; chained_growth[YEARS[i+1]] = g

    # ---- 4. Population
    if iso == 'GBR':
        for y in YEARS:
            if y in ONS_POP and y <= 2025: pop[yi(y)] = ONS_POP[y]/1e6; psrc[yi(y)] = 'NAT'
    if iso in ('RUS', 'BLR', 'GEO'):
        for y in YEARS:
            v = imf_lp(iso, y)
            if v is not None and y <= 2025: pop[yi(y)] = v; psrc[yi(y)] = 'IMF'
    if iso in ('UKR', 'MNE'):
        # Eurostat demographic average population, same basis as national accounts for these geos
        for y, (v, f) in esd.items():
            i = yi(y)
            if pop[i] is None and gdp[i] is not None: pop[i] = v/1e6; psrc[i] = 'ES'
    if iso == 'ALB':
        for y, (v, f) in esd.items():
            i = yi(y)
            if pop[i] is None and gdp[i] is not None and y >= 2023: pop[i] = v/1e6; psrc[i] = 'ES'
    # chain remaining population gaps from nearest known level
    def popratio(y):
        """pop_y / pop_{y-1} and code"""
        if iso == 'MKD' and y <= 2003:
            a = esd.get(y); b = esd.get(y-1)
            if a and b: return a[0]/b[0], 'ES'
        a, b = imf_lp(iso, y), imf_lp(iso, y-1)
        if a and b: return a/b, ('FC' if y >= FC_FROM else 'IMF')
        w = wb_popratio(iso, y)
        if w: return w, 'WB'
        return None, None
    for i in range(1, N):
        if pop[i] is None and pop[i-1] is not None and gdp[i] is not None:
            r, s = popratio(YEARS[i])
            if r: pop[i] = pop[i-1]*r; psrc[i] = s
    for i in range(N-2, -1, -1):
        if pop[i] is None and pop[i+1] is not None and gdp[i] is not None:
            r, s = popratio(YEARS[i+1])
            if r: pop[i] = pop[i+1]/r; psrc[i] = s

    # ---- 5. pc, src coding, rounding
    rank = {'ES': 0, 'NAT': 1, 'IMF': 2, 'WB': 3, 'FC': 4}
    for i, y in enumerate(YEARS):
        if gdp[i] is None or pop[i] is None:
            gdp[i] = None if gdp[i] is None else gdp[i]; pc[i] = None
            src[i] = None if gdp[i] is None and pop[i] is None else (gsrc[i] or psrc[i])
            if gdp[i] is not None and pop[i] is None: src[i] = gsrc[i]
            continue
        if pc[i] is None: pc[i] = int(round(gdp[i]/pop[i]))
        s = max([gsrc[i], psrc[i]], key=lambda c: rank[c])
        if y >= FC_FROM: s = 'FC'
        src[i] = s
        pop[i] = round(pop[i], 4)
    # pop must be null where pc is null
    for i in range(N):
        if pc[i] is None: pop[i] = None
    return gdp, pc, pop, src, gsrc, psrc, anchor, esg, esp, espe, esd, chained_growth, flags

for iso in C:
    gdp, pc, pop, src, gsrc, psrc, anchor, esg, esp, espe, esd, chained, flags = build(iso)
    report[iso] = dict(gsrc=gsrc, psrc=psrc, chained=chained, flags=flags, es_years=sorted(esg), espc_years=sorted(esp), espe_years=sorted(espe))
    countries[iso] = {'name': C[iso][1], 'gdp': gdp, 'pc': pc, 'pop': pop, 'src': src, 'anchor': anchor, 'territory': None, 'note': None}

# ---- territory / notes
def yrs(lst):
    """compress a sorted year list into ranges"""
    if not lst: return ''
    out = []; s = p = lst[0]
    for y in lst[1:]:
        if y == p+1: p = y; continue
        out.append(f'{s}' if s == p else f'{s}-{p}'); s = p = y
    out.append(f'{s}' if s == p else f'{s}-{p}'); return ', '.join(out)

def code_years(iso, code, comp=None):
    r = report[iso]; arr = r[comp] if comp else countries[iso]['src']
    return [YEARS[i] for i in range(N) if arr[i] == code]

for iso, c in countries.items():
    r = report[iso]; g = r['gsrc']; p = r['psrc']
    parts = []
    es_g = [YEARS[i] for i in range(N) if g[i] == 'ES']; es_pc = r['espc_years']
    if iso in ('RUS', 'BLR', 'GEO'):
        parts.append('Outside Eurostat national accounts. Real GDP anchored on IMF WEO (April 2026) 2015 nominal GDP in USD converted at 1.1095 and chained with IMF real growth (NGDP_RPCH) 1995-2025; population IMF WEO (LP); 2026-2031 IMF projections.')
    elif iso == 'GBR':
        parts.append('Not in current Eurostat tables. 2015 level from IMF WEO nominal GDP (USD) at 1.1095; volumes chained with ONS real GDP series ABMI (chained volume measures, release %s) 1995-2025; population ONS mid-year estimates series UKPOP (release %s). 2026-2031: IMF WEO April 2026 growth and population projections.' % (ONS_ABMI_REL, ONS_POP_REL))
    elif iso == 'UKR':
        parts.append('GDP 2010-2024 verbatim from Eurostat nama_10_gdp (Ukrstat data transmitted to Eurostat); 1995-2009 back-cast with IMF WEO real growth; 2025 IMF estimate. Population: Eurostat demo_gind average population 1996-2020, extended 2021-2025 with IMF WEO population growth (reflects wartime displacement from 2022); 1995 back-cast with IMF. 2026 IMF projection. The 2014 drop (-6.5% real, and -5.5% population) is the exclusion of Crimea and occupied Donbas; 2022 is the full-scale invasion (-28.8%).')
    else:
        # generic Eurostat country
        derived_g = [YEARS[i] for i in range(N) if g[i] not in ('ES', None) and YEARS[i] < FC_FROM]
        derived_p = [YEARS[i] for i in range(N) if p[i] not in ('ES', None) and YEARS[i] < FC_FROM]
        pe_only = [YEARS[i] for i in range(N) if p[i] == 'ES' and YEARS[i] not in es_pc and YEARS[i] < FC_FROM]
        if derived_g:
            codes = sorted(set(g[yi(y)] for y in derived_g))
            parts.append('GDP %s chained from %s real growth (Eurostat volumes start %d).' % (yrs(derived_g), ' / '.join({'IMF':'IMF WEO','WB':'World Bank WDI constant-2015-USD','NAT':'national'}[c] for c in codes), min(es_g) if es_g else 0))
        if pe_only:
            src_pe = 'Eurostat nama_10_pe national-accounts population' if all(y in r['espe_years'] for y in pe_only) else 'Eurostat demo_gind average population'
            parts.append('Per-capita %s computed as GDP / %s (Eurostat does not publish CLV15 per-capita for these years).' % (yrs(pe_only), src_pe))
        if derived_p:
            codes = sorted(set(p[yi(y)] for y in derived_p))
            parts.append('Population %s chained from %s growth off the nearest Eurostat level.' % (yrs(derived_p), ' / '.join({'IMF':'IMF WEO','WB':'World Bank WDI (UN WPP)'}[c] for c in codes)))
        if not parts: parts.append('Eurostat nama_10_gdp / nama_10_pc verbatim 1995-2025; 2026-2031 IMF WEO April 2026 real-growth and population projections applied to the 2025 Eurostat values.')
        else: parts.append('2026-2031: IMF WEO April 2026 real-growth and population projections.')
    if iso == 'ALB':
        parts.append('Population 2023-2025 is Eurostat demo_gind (INSTAT, 2023-census based: 2.58 M in 2023, 2.38 M in 2024) while 2022 and earlier is the pre-census national-accounts population (2.78 M in 2022); the per-capita steps of +12% in 2023 and +13% in 2024 are this documented census break, not real growth. IMF WEO still carries the pre-census 2.75 M for 2023.')
    if iso == 'BIH':
        parts.append('Bosnia population 2010-2024 is on the 2013-census basis (BHAS via Eurostat, 3.54 M in 2010); pre-2010 Eurostat demographic figures are on the old 3.8 M basis, so population 1995-2009 is back-cast from the 2010 level with UN WPP growth instead.')
    if iso == 'MKD':
        parts.append('North Macedonia population 2000-2002 back-cast from the 2003 national-accounts level (2021-census basis) with Eurostat demo_gind growth; 1995-1999 with IMF.')
    if iso == 'MNE':
        parts.append('Montenegro: IMF growth starts 2001, World Bank constant-price GDP starts 1997; 1995-1996 GDP unavailable (null). UN National Accounts Main Aggregates growth for 1998-2000 (4.6 / -8.3 / +14.5%) disagrees with the World Bank (4.9 / -9.4 / +3.1%) used here. Population 1995-2005 Eurostat demo_gind (same basis as national accounts).')
    if iso == 'SRB':
        parts.append('Serbia: Eurostat GDP volumes exclude Kosovo throughout, but the Eurostat per-capita series for 1995-1998 divides by a population that still includes Kosovo (9.7-9.8 M vs 7.5 M from 1999), so per-capita 1995-1998 is understated by roughly 22% and steps up in 1999. Values kept verbatim as published.')
    if iso == 'MLT':
        parts.append('Malta 1995-1999: Eurostat volumes start 2000 and IMF growth starts 2001, so back-cast with World Bank constant-2015-USD growth for 1996-1999; the 1999-2000 link uses UN National Accounts Main Aggregates real growth (6.7%) because the World Bank series has a splice jump (+19.7%) in 2000. Population Eurostat nama_10_pe.')
    c['note'] = ' '.join(parts)
    c['territory'] = {
        'UKR': 'excl. Crimea and Sevastopol and the occupied parts of Donetsk and Luhansk from 2014 (Ukrstat basis); resident population from 2022 reflects wartime displacement',
        'RUS': 'Russian Federation as reported by Rosstat/IMF: incl. Crimea and Sevastopol from 2014; regions occupied since 2022 not included in the IMF population series used',
        'GEO': 'excl. Abkhazia and South Ossetia (Geostat basis)',
        'CYP': 'government-controlled area only (Eurostat basis)',
        'SRB': 'GDP excl. Kosovo (SORS/Eurostat basis); Eurostat per-capita 1995-1998 uses a population incl. Kosovo',
        'MDA': None,
    }.get(iso)

# ---- quality checks
checks = []
bad_pc = []
for iso, c in countries.items():
    for i, y in enumerate(YEARS):
        if c['gdp'][i] is not None and c['pc'][i] is not None and c['pop'][i] is not None:
            d = c['gdp'][i]/c['pop'][i]/c['pc'][i]-1
            if abs(d) > 0.01: bad_pc.append((iso, y, round(d*100, 2)))
checks.append(('pc ≈ gdp/pop within 1 %%: %s' % ('PASS for all %d country-years' % sum(1 for c in countries.values() for v in c['pc'] if v is not None) if not bad_pc else 'FAIL ' + str(bad_pc))))

spot = {'DEU': (40150, 3352945), 'POL': (15830, 594143), 'ESP': (26350, 1287588), 'ROU': (11220, 213902)}
sp = []
for iso, (pcv, gv) in spot.items():
    c = countries[iso]; i = yi(2024)
    sp.append('%s pc %d (expected %d) gdp %.0f (expected %d)%s' % (iso, c['pc'][i], pcv, c['gdp'][i], gv, '' if (c['pc'][i] == pcv and round(c['gdp'][i]) == gv) else '  <-- REVISED'))
checks.append('2024 Eurostat spot checks: ' + '; '.join(sp))

wbc = []
for iso in ('UKR', 'RUS', 'BLR', 'GEO'):
    w = WB_GDP.get(iso, {}).get(2024)
    ours = countries[iso]['gdp'][yi(2024)]
    if w is None: wbc.append('%s: WB 2024 missing' % iso); continue
    wbc.append('%s %+.2f%% (ours %.0f vs WB %.0f MEUR)' % (iso, (ours/(w/1e6/FX)-1)*100, ours, w/1e6/FX))
checks.append('2024 vs World Bank NY.GDP.MKTP.KD / 1.1095: ' + '; '.join(wbc))

# growth reproduction check on chained years
worst = 0; worst_at = None
for iso, c in countries.items():
    for y, g in report[iso]['chained'].items():
        i = yi(y)
        if c['gdp'][i] is None or c['gdp'][i-1] is None: continue
        d = abs((c['gdp'][i]/c['gdp'][i-1]-1)*100 - g*100)
        if d > worst: worst, worst_at = d, (iso, y)
checks.append('Implied vs chained growth on all chained years: max deviation %.3f pp at %s (tolerance 0.05)' % (worst, worst_at))

# jump scan
jumps = []
for iso, c in countries.items():
    for i in range(1, N):
        for k, thr in (('gdp', 0.12), ('pop', 0.03)):
            a, b = c[k][i-1], c[k][i]
            if a and b and abs(b/a-1) > thr: jumps.append('%s %s %d %+.1f%%' % (iso, k, YEARS[i], (b/a-1)*100))
checks.append('Year-on-year moves > 12 % (GDP) or > 3 % (population): ' + ('; '.join(jumps) if jumps else 'none'))

# nulls
nulls = [(iso, k, yrs([YEARS[i] for i in range(N) if c[k][i] is None])) for iso, c in countries.items() for k in ('gdp', 'pc', 'pop') if any(v is None for v in c[k])]
checks.append('Null cells: ' + ('; '.join('%s %s %s' % n for n in nulls) if nulls else 'none'))

# source-disagreement > 2%: compare our 2024 level against WB constant-2015-USD/1.1095 for all countries
dis = []
for iso, c in countries.items():
    w = WB_GDP.get(iso, {}).get(2024); o = c['gdp'][yi(2024)]
    if w and o:
        d = (o/(w/1e6/FX)-1)*100
        if abs(d) > 2: dis.append('%s %+.1f%%' % (iso, d))
checks.append('Countries whose 2024 level differs from World Bank constant-2015-USD by > 2 % (WB rebases to 2015 USD at market rates and revises less often; informational): ' + (', '.join(dis) if dis else 'none'))

# OECD Economic Outlook cross-check of the 2027 (and 2026) real-growth projections
oecd_path = os.path.join(RAW, 'oecd_eo.csv')
if os.path.exists(oecd_path):
    oecd = {}
    for r in csv.DictReader(open(oecd_path)):
        oecd.setdefault(r['REF_AREA'], {})[int(r['TIME_PERIOD'])] = float(r['OBS_VALUE'])
    diffs = []
    for iso, s_ in oecd.items():
        if iso not in countries or 2027 not in s_: continue
        imf27 = imf_g(iso, 2027); diffs.append((iso, imf27, s_[2027], imf27 - s_[2027]))
    diffs.sort(key=lambda x: -abs(x[3]))
    mad = sum(abs(x[3]) for x in diffs)/len(diffs)
    checks.append('2027 real growth, IMF WEO Apr-2026 vs OECD Economic Outlook (%d countries): mean abs. gap %.2f pp; largest: %s' % (
        len(diffs), mad, '; '.join('%s IMF %.1f / OECD %.1f' % (d[0], d[1], d[2]) for d in diffs[:6])))
# 2025 flags
prov = sorted(set(iso for iso, r in report.items() if r['flags'].get(2025) in ('p', 'e')))
checks.append('Eurostat 2025 values are flagged provisional/estimated for: ' + ', '.join(prov))

# ---- assemble
out = {
 'meta': {
  'unit_gdp': 'EUR million, chain-linked volumes, reference year 2015',
  'unit_pc': 'EUR per inhabitant, chain-linked volumes, reference year 2015',
  'unit_pop': 'million residents, annual average',
  'fx_2015_usd_per_eur': FX,
  'years': YEARS,
  'forecast_from': FC_FROM,
  'generated': GENERATED,
 },
 'sources': {
  'ES': 'Eurostat nama_10_gdp (B1GQ, CLV15_MEUR) / nama_10_pc (B1GQ, CLV15_EUR_HAB); population nama_10_pe (POP_NC) or demo_gind (AVG) where per-capita is not published. Extracted %s.' % ES_GDP['updated'][:10],
  'IMF': 'IMF World Economic Outlook, April 2026 (NGDP_RPCH real growth, LP population, NGDPD nominal USD GDP for the 2015 anchor)',
  'WB': 'World Bank WDI (NY.GDP.MKTP.KD constant 2015 USD, SP.POP.TOTL), last updated %s; used only for growth back-casts where Eurostat and IMF are silent (MLT 1995-1999, MNE 1997-1999, BIH population before 2000), and as cross-check. The Malta 1999-2000 link uses UN National Accounts Main Aggregates growth (see country note).' % WB_UPD,
  'NAT': 'national statistics office: UK Office for National Statistics (ABMI real GDP release %s; UKPOP mid-year population release %s)' % (ONS_ABMI_REL, ONS_POP_REL),
  'FC': 'forecast: IMF World Economic Outlook April 2026 projections (real growth and population) chained forward from the 2025 value (2026-2031)',
 },
 'countries': countries,
}
os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
json.dump(out, open(OUT_JSON, 'w'), ensure_ascii=False, separators=(',', ':'))

# src summary for notes
srcsum = []
for iso, c in countries.items():
    cnt = {}
    for s in c['src']:
        cnt[s] = cnt.get(s, 0)+1
    non_es = [YEARS[i] for i in range(N) if c['src'][i] not in ('ES',) and YEARS[i] < FC_FROM]
    if non_es: srcsum.append('%s: %s %s' % (iso, yrs(non_es), '/'.join(sorted(set(c['src'][yi(y)] for y in non_es if c['src'][yi(y)])))))

notes = ['# Notes — GDP research output (%s)' % GENERATED, '',
 'Output: `data/econ.json` (v2 format, 40 countries × 37 years 1995–2031, `forecast_from` 2026; 2026–2031 are IMF WEO April 2026 projections, coded `FC`).', '',
 '## Data vintages',
 '- Eurostat nama_10_gdp / nama_10_pc / nama_10_pe dataset timestamp %s; demo_gind %s. 2025 values flagged provisional (p) or estimated (e) by Eurostat.' % (ES_GDP['updated'][:16].replace('T', ' '), ES_DEMO['updated'][:10]),
 '- IMF World Economic Outlook April 2026 (datamapper API, indicators NGDP_RPCH, NGDPD, LP). 2025 = IMF estimate where national data were not final; 2026–2031 = projections (all `FC`, medium-term WEO horizon). The WEO is the only source projecting real GDP and population for all 40 countries to 2031; the OECD Economic Outlook stops at 2027 and the European Commission Spring 2026 forecast at 2027 (EU members and candidates only).',
 '- World Bank WDI bulk download, last updated %s (cross-check; growth back-cast only for MLT 1995–1999, MNE 1997–2000, and population before 2000 for BIH).' % WB_UPD,
 '- OECD Economic Outlook (sdmx.oecd.org, dataflow DSD_EO@DF_EO, GDPV_ANNPCT) used only to cross-check the 2026-2027 IMF growth projections (OECD horizon ends 2027); not used in the data.',
 '- ONS: real GDP ABMI (chained volume measures, seasonally adjusted, release %s, 2025 included); UK mid-year population UKPOP (release %s).' % (ONS_ABMI_REL, ONS_POP_REL),
 '',
 '## Check results',
] + ['- ' + c for c in checks] + [
 '',
 '## Source-coding policy',
 '- `ES` only where GDP is verbatim Eurostat and population is Eurostat (nama_10_pc per-capita, or nama_10_pe / demo_gind population). Any year with an IMF, World Bank or national input is coded by that input (IMF > WB when both). 2026–2031 are always `FC`. Non-ES years before 2026:',
] + ['  - ' + s for s in srcsum] + [
 '',
 '## Judgement calls to be aware of',
 '- Ukraine: Eurostat carries Ukrstat chain-linked volumes 2010–2024, so those years are `ES` (2014 and 2021–2024 coded `IMF` only because Eurostat has no average population for them and the IMF series is used). Eurostat’s 2015 level differs from the IMF nominal-USD anchor by 0.25 %. Eurostat’s 2014 real change is −6.5 % (constant territory) versus IMF −10 % (includes territory loss).',
 '- Albania: per-capita jumps +12 % in 2023 because Eurostat population switches to the 2023-census basis while national accounts population (used for 2022 and before) is not yet revised. Alternative: IMF pre-census population would give pc 4,905 / 5,156 / 5,400 for 2023-2025 instead of the census-based 5,235 / 5,903 / 6,194. The country note documents the break.',
 '- Serbia: Eurostat’s own per-capita series switches population basis in 1999 (Kosovo excluded from 1999, included 1995–1998), a +16 % step in pc with GDP continuous; kept verbatim, documented in the country note.',
 '- Malta 1995–1999: World Bank constant-USD GDP has a splice jump of +19.7 % at 2000; the 1999→2000 link uses UN National Accounts Main Aggregates growth (6.7 %) instead, coded `WB`. Montenegro 1998–2000: WB and UN growth disagree by up to 11 pp; WB used.',
 '- United Kingdom: no Eurostat series since Brexit; IMF USD anchor + ONS chaining. Eurostat demo_gind UK population 2025 (69.47 M) agrees with ONS UKPOP (69.49 M) within 0.03 %.',
 '- 2027–2031 are pure IMF WEO medium-term projections chained year by year (beyond 2027 the IMF converges most countries to potential growth, so the paths are smooth trend extrapolations, not forecasts of cycles); IMF population projections carry statistical revisions (e.g. Poland −0.8 % in 2026), which the ratio-chaining transfers to `pop`/`pc` as a one-year dip.',
 '- Russia: territory per Rosstat/IMF (Crimea included from 2014). IMF population (144.8 M in 2024) excludes the regions occupied since 2022.',
]
open(OUT_NOTES, 'w').write('\n'.join(notes) + '\n')
print('\n'.join(checks))
print('nulls:', nulls)
