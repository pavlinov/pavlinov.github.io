# Notes — GDP research output (2026-09-07)

Output: `data/econ.json` (v2 format, 40 countries × 32 years 1995–2026, `forecast_from` 2026).

## Data vintages
- Eurostat nama_10_gdp / nama_10_pc / nama_10_pe dataset timestamp 2026-09-07 11:00; demo_gind 2026-07-21. 2025 values flagged provisional (p) or estimated (e) by Eurostat.
- IMF World Economic Outlook April 2026 (datamapper API, indicators NGDP_RPCH, NGDPD, LP). 2025 = IMF estimate where national data were not final; 2026 = projection (all `FC`).
- World Bank WDI bulk download, last updated 2026-07-13 (cross-check; growth back-cast only for MLT 1995–1999, MNE 1997–2000, and population before 2000 for BIH).
- ONS: real GDP ABMI (chained volume measures, seasonally adjusted, release 2026-08-12, 2025 included); UK mid-year population UKPOP (release 2025-11-27).

## Check results
- pc ≈ gdp/pop within 1 %: PASS for all 1278 country-years
- 2024 Eurostat spot checks: DEU pc 40150 (expected 40150) gdp 3352945 (expected 3352945); POL pc 15830 (expected 15830) gdp 594143 (expected 594143); ESP pc 26350 (expected 26350) gdp 1287588 (expected 1287588); ROU pc 11220 (expected 11220) gdp 213902 (expected 213902)
- 2024 vs World Bank NY.GDP.MKTP.KD / 1.1095: UKR +0.19% (ours 71150 vs WB 71014 MEUR); RUS -0.49% (ours 1453881 vs WB 1461042 MEUR); BLR -0.39% (ours 55872 vs WB 56091 MEUR); GEO +0.01% (ours 22704 vs WB 22701 MEUR)
- Implied vs chained growth on all chained years: max deviation 0.002 pp at ('MNE', 2006) (tolerance 0.05)
- Year-on-year moves > 12 % (GDP) or > 3 % (population): ALB gdp 1999 +12.3%; ALB pop 2023 -7.2%; ALB pop 2024 -7.7%; BGR gdp 1997 -14.1%; BGR pop 2001 -3.4%; BIH gdp 1996 +62.2%; BIH pop 1996 +4.3%; BIH gdp 1997 +22.9%; BIH gdp 1998 +13.8%; EST gdp 1997 +13.1%; EST gdp 2009 -14.6%; GEO pop 1996 -3.6%; GEO pop 1997 -3.6%; GEO gdp 2007 +12.6%; HRV pop 2001 -3.8%; HRV gdp 2021 +12.6%; IRL pop 2007 +3.1%; IRL gdp 2015 +24.6%; IRL gdp 2021 +16.6%; LTU gdp 2009 -14.8%; LVA gdp 2006 +12.8%; LVA gdp 2009 -16.0%; MLT gdp 2017 +13.0%; MLT pop 2018 +3.6%; MLT pop 2019 +4.2%; MLT gdp 2021 +13.3%; MLT pop 2023 +4.1%; MNE gdp 2020 -15.0%; MNE gdp 2021 +13.0%; ROU pop 2002 -3.2%; SRB pop 1999 -22.9%; UKR gdp 2009 -15.1%; UKR pop 2014 -5.5%; UKR gdp 2022 -28.8%; UKR pop 2022 -15.8%
- Null cells: MNE gdp 1995-1996; MNE pc 1995-1996; MNE pop 1995-1996
- Countries whose 2024 level differs from World Bank constant-2015-USD by > 2 % (WB rebases to 2015 USD at market rates and revises less often; informational): MLT -2.7%
- Eurostat 2025 values are flagged provisional/estimated for: BEL, BGR, CYP, DEU, ESP, FRA, GRC, HRV, HUN, LUX, MKD, MNE, PRT, ROU, SRB

## Source-coding policy
- `ES` only where GDP is verbatim Eurostat and population is Eurostat (nama_10_pc per-capita, or nama_10_pe / demo_gind population). Any year with an IMF, World Bank or national input is coded by that input (IMF > WB when both). 2026 is always `FC`. Non-ES years before 2026:
  - ALB: 2025 IMF
  - BIH: 1995-2009, 2025 IMF/WB
  - BLR: 1995-2025 IMF
  - GBR: 1995-2025 NAT
  - GEO: 1995-2025 IMF
  - MKD: 1995-1999 IMF
  - MLT: 1995-1999 WB
  - MNE: 1995-2005 IMF/WB
  - RUS: 1995-2025 IMF
  - UKR: 1995-2009, 2014, 2021-2025 IMF

## Judgement calls to be aware of
- Ukraine: Eurostat carries Ukrstat chain-linked volumes 2010–2024, so those years are `ES` (2014 and 2021–2024 coded `IMF` only because Eurostat has no average population for them and the IMF series is used). Eurostat’s 2015 level differs from the IMF nominal-USD anchor by 0.25 %. Eurostat’s 2014 real change is −6.5 % (constant territory) versus IMF −10 % (includes territory loss).
- Albania: per-capita jumps +12 % in 2023 because Eurostat population switches to the 2023-census basis while national accounts population (used for 2022 and before) is not yet revised. Alternative: IMF pre-census population would give pc 4,905 / 5,156 / 5,400 for 2023-2025 instead of the census-based 5,235 / 5,903 / 6,194. The country note documents the break.
- Serbia: Eurostat’s own per-capita series switches population basis in 1999 (Kosovo excluded from 1999, included 1995–1998), a +16 % step in pc with GDP continuous; kept verbatim, documented in the country note.
- Malta 1995–1999: World Bank constant-USD GDP has a splice jump of +19.7 % at 2000; the 1999→2000 link uses UN National Accounts Main Aggregates growth (6.7 %) instead, coded `WB`. Montenegro 1998–2000: WB and UN growth disagree by up to 11 pp; WB used.
- United Kingdom: no Eurostat series since Brexit; IMF USD anchor + ONS chaining. Eurostat demo_gind UK population 2025 (69.47 M) agrees with ONS UKPOP (69.49 M) within 0.03 %.
- Russia: territory per Rosstat/IMF (Crimea included from 2014). IMF population (144.8 M in 2024) excludes the regions occupied since 2022.
