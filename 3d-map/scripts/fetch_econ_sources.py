#!/usr/bin/env python3
"""Download the raw inputs for scripts/build_econ.py into a directory (default ./raw).
Usage: python3 scripts/fetch_econ_sources.py [raw_dir]
Sources: Eurostat (nama_10_gdp, nama_10_pc, nama_10_pe, demo_gind), IMF WEO datamapper (NGDP_RPCH, NGDPD, LP),
World Bank WDI bulk CSV (NY.GDP.MKTP.KD, SP.POP.TOTL), ONS (ABMI, UKPOP). Uses curl (system trust store)."""
import os, subprocess, sys, time, zipfile
RAW = sys.argv[1] if len(sys.argv) > 1 else 'raw'
os.makedirs(RAW, exist_ok=True)
GEOS = "AL AT BE BG BA BY CH CY CZ DE DK ES EE FI FR UK GE EL HR HU IE IS IT LT LU LV MK MT ME NL NO PL PT RO RU RS SK SI SE UA".split()
g = ''.join('&geo=' + x for x in GEOS); t = ''.join('&time=%d' % y for y in range(1995, 2026))
ES = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
URLS = {
 'es_gdp.json': ES + 'nama_10_gdp?format=JSON&na_item=B1GQ&unit=CLV15_MEUR' + g + t,
 'es_pc.json': ES + 'nama_10_pc?format=JSON&na_item=B1GQ&unit=CLV15_EUR_HAB' + g + t,
 'es_pe.json': ES + 'nama_10_pe?format=JSON&na_item=POP_NC&unit=THS_PER' + g + t,
 'es_demo.json': ES + 'demo_gind?format=JSON&indic_de=AVG' + g + t,
 'imf_rpch.json': 'https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH',
 'imf_ngdpd.json': 'https://www.imf.org/external/datamapper/api/v1/NGDPD',
 'imf_lp.json': 'https://www.imf.org/external/datamapper/api/v1/LP',
 'wb_gdp_bulk.zip': 'https://api.worldbank.org/v2/en/indicator/NY.GDP.MKTP.KD?downloadformat=csv',
 'wb_pop_bulk.zip': 'https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv',
 'ons_abmi.json': 'https://www.ons.gov.uk/economy/grossdomesticproductgdp/timeseries/abmi/pn2/data',
 'ons_ukpop.json': 'https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/timeseries/ukpop/pop/data',
}
for name, url in URLS.items():
    out = os.path.join(RAW, name)
    for i in range(4):
        r = subprocess.run(['curl', '-sS', '-L', '-m', '180', '-A', 'Mozilla/5.0', '-o', out, '-w', '%{http_code}', url], capture_output=True, text=True)
        if r.stdout.strip() == '200': print('ok', name); break
        print('retry', i, name, r.stdout, r.stderr[:120]); time.sleep(5)
    else: sys.exit('failed ' + name)
for z, d in (('wb_gdp_bulk.zip', 'wbg'), ('wb_pop_bulk.zip', 'wbp')):
    zipfile.ZipFile(os.path.join(RAW, z)).extractall(os.path.join(RAW, d))
print('done ->', RAW)
