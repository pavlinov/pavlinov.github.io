# Research prompt — GDP series for the Europe Economic Evolution map

Copy everything below the line into a research-capable model (web access required).

---

You are compiling the economic dataset for an interactive 3-D map of Europe. Produce **one JSON
object** in the exact format specified in the attached `econ-format.md` (v2). No prose outside
the JSON except a short "Notes" section after it.

## Scope

- **Countries (40, ISO-3166 alpha-3, fixed):**
  ALB AUT BEL BGR BIH BLR CHE CYP CZE DEU DNK ESP EST FIN FRA GBR GEO GRC HRV HUN
  IRL ISL ITA LTU LUX LVA MKD MLT MNE NLD NOR POL PRT ROU RUS SRB SVK SVN SWE UKR
- **Years:** 1995–2026 inclusive (32 values per array). 2026 is a forecast for every country
  (`forecast_from: 2026`). 2025 must be an actual/first estimate where one exists.
- **Metrics:** real GDP (EUR million, chain-linked volumes, 2015 prices), real GDP per capita
  (EUR, same basis), population (million, annual average).

## Source hierarchy — use the highest available, record it per year in `src`

1. **Eurostat** `nama_10_gdp` (na_item B1GQ, unit CLV15_MEUR) and `nama_10_pc`
   (unit CLV15_EUR_HAB). Covers EU-27, IS, NO, CH, ME, MK, RS, BA, TR, MD, XK, and
   historical UK. Take values verbatim; code `ES`.
   API example:
   `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp?format=JSON&na_item=B1GQ&unit=CLV15_MEUR&geo=PL&time=2025`
2. **National statistics** for gaps Eurostat does not cover (UK: ONS real GDP series ABMI and
   mid-year population; Albania: INSTAT; Bosnia per-capita: BHAS). Code `NAT`.
3. **IMF World Economic Outlook** (latest edition; state which) for Ukraine, Russia, Belarus,
   Georgia and for all 2026 forecasts: real GDP growth `NGDP_RPCH`, population `LP`,
   nominal GDP in USD `NGDPD` (for the 2015 anchor). Code `IMF`, forecasts `FC`.
   API example: `https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH/UKR/RUS/BLR/GEO`
4. **World Bank WDI** only as a cross-check or fallback (`NY.GDP.MKTP.KD`, `SP.POP.TOTL`).

## Method for non-Eurostat countries (UKR, RUS, BLR, GEO; UK and ALB where needed)

- Anchor: `gdp_2015 = NGDPD_2015 (USD bn) × 1000 / 1.1095` (ECB 2015 average USD per EUR).
- Chain real growth: `gdp_t = gdp_{t-1} × (1 + NGDP_RPCH_t / 100)` forwards from 2015,
  `gdp_{t-1} = gdp_t / (1 + NGDP_RPCH_t / 100)` backwards to 1995.
- `pc_t = gdp_t / pop_t`. Population basis must match the GDP basis and be stated in
  `territory`: Ukraine excluding Crimea and occupied Donbas from 2014; Russia as reported by
  Rosstat/IMF for the Russian Federation (state whether Crimea is included from 2014).
- Fill `anchor` and `note` for each such country.

## Quality checks — run them and report results in "Notes"

- `pc ≈ gdp / pop` within 1 % for every country-year with all three values.
- The map's current 2024 values are Eurostat-exact; your 2024 `ES` values should match these
  spot checks: DEU pc 40150 / gdp 3352945; POL 15830 / 594143; ESP 26350 / 1287588;
  ROU 11220 / 213902. Flag any Eurostat revision that changes them.
- For UKR/RUS/BLR/GEO compare your 2024 result against World Bank constant-2015-USD GDP
  converted at 1.1095 and report the % difference (expect < 3 %).
- Year-on-year real growth implied by `gdp` must equal the growth series you chained from
  (± 0.05 pp). No series may contain a jump you cannot attribute to a documented break.

## Output rules

- Exactly the v2 JSON: `meta`, `sources`, `countries` with `name, gdp, pc, pop, src, anchor,
  territory, note` for every country; arrays of length 32; `null` for anything unsourced.
- `src` is mandatory for every year. Never infer a value silently — if you interpolate or
  back-cast, code it `IMF`/`WB`/`NAT` and explain in `note`.
- After the JSON, a "Notes" section (≤ 20 lines): data vintages used (release dates), check
  results, and any country where sources disagree by more than 2 %.
