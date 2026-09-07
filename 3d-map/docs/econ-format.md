# ECON data format (v2)

The map (`europe-economic-map-textured.html`) embeds one JSON object as `const ECON = …`.
This document defines the v2 shape that research output must follow. Arrays are aligned to
`meta.years`; every metric array has exactly `years.length` entries; unknown = `null`.

```jsonc
{
  "meta": {
    "unit_gdp": "EUR million, chain-linked volumes, reference year 2015",
    "unit_pc":  "EUR per inhabitant, chain-linked volumes, reference year 2015",
    "unit_pop": "million residents, annual average",
    "fx_2015_usd_per_eur": 1.1095,      // ECB 2015 average, used to anchor non-euro-area series
    "years": [1995, 1996, "...", 2026],
    "forecast_from": 2026,              // first year that is a forecast for every country
    "generated": "YYYY-MM-DD"
  },
  "sources": {                          // codes used in each country's src[]
    "ES":  "Eurostat nama_10_gdp (CLV15_MEUR) / nama_10_pc (CLV15_EUR_HAB)",
    "IMF": "IMF World Economic Outlook, <edition>",
    "WB":  "World Bank WDI (NY.GDP.MKTP.KD, SP.POP.TOTL)",
    "NAT": "national statistics office (name it in the country note)",
    "FC":  "forecast (name the forecaster in the country note)"
  },
  "countries": {
    "DEU": {
      "name": "Germany",
      "gdp": [ ... ],                   // EUR million, 2015 prices
      "pc":  [ ... ],                   // EUR, 2015 prices
      "pop": [ ... ],                   // million; must satisfy pc ≈ gdp / pop within 1%
      "src": [ "ES", "ES", "...", "FC" ], // one code per year, mandatory
      "anchor": null,                   // only for non-Eurostat series, see below
      "territory": null,                // e.g. "excl. Crimea and occupied Donbas from 2014"
      "note": null                      // free text shown on the country card
    },
    "UKR": {
      "name": "Ukraine",
      "gdp": [ ... ], "pc": [ ... ], "pop": [ ... ],
      "src": [ "IMF", "...", "FC" ],
      "anchor": { "year": 2015, "gdp_usd_bn": 90.98, "source": "IMF WEO NGDPD" },
      "territory": "excl. Crimea and occupied Donbas from 2014; resident population from 2022 reflects displacement",
      "note": "Outside Eurostat national accounts; volumes chained from IMF real growth …"
    }
  }
}
```

## Rules

1. **Basis is Eurostat's**: real volumes at 2015 prices in EUR. For Eurostat countries copy the
   values as published (do not rescale). For non-Eurostat countries chain real GDP growth
   (national currency, constant prices) forwards and backwards from a 2015 anchor:
   `gdp_2015 = GDP_2015_current_USD × 1000 / 1.1095`, then `gdp_t = gdp_{t-1} × (1 + g_t)`.
2. `pc = gdp × 1e6 / (pop × 1e6)` rounded to whole euros. If a source publishes per-capita
   volumes directly (Eurostat does), use those and let `pop` be the implied population.
3. One `src` code per year. `ES` only for values taken verbatim from Eurostat. Anything
   derived is `IMF`/`WB`/`NAT`; any year ≥ `forecast_from` is `FC`.
4. `null`, never a guess, when a value cannot be sourced.
5. Country set is fixed to the map's 40 ISO-3166 alpha-3 codes; do not add or drop.

## Loading in the map

The renderer derives what it needs at load time:

```js
const est = d.src.map((s,i)=>s!=='ES'?i:-1).filter(i=>i>=0);   // dashed/“est.” years
```
Keep `data/econ.json` as the source of truth and inline it with `node scripts/build-econ.js`
(the page is opened via `file://`, where `fetch()` of a sibling file is blocked). The script
validates array lengths and rewrites the `const ECON_V2 = …` line in the HTML.
