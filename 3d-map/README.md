# Europe Economic Evolution — interactive 3D map

Textured, interactive 3D isometric map of 39 European and neighbouring countries
(including European Russia, Belarus, Georgia and Turkey), showing GDP per capita
(PPP, constant 2021 international $) from 1995 to 2027.

- 1995–2025: World Bank series via Our World in Data (fetched live, cached locally)
- 2026–2027: IMF World Economic Outlook, April 2026, real GDP per capita growth projections
- Detail card: IMF outlook table (real growth, nominal GDP, GDP per capita) for 2025–2027

Live page: https://pavlinov.github.io/3d-map/interactive-3d-map-europe-gdp-index.html

## Embed on your website

Click the `</>` button in the bottom bar of the live page to copy a snippet, or paste this:

```html
<iframe src="https://pavlinov.github.io/3d-map/interactive-3d-map-europe-gdp-index.html?embed=1"
  width="100%" height="640" style="border:0;border-radius:12px"
  loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
  title="Europe Economic Evolution — interactive 3D GDP map"></iframe>
```

### URL parameters

| Parameter | Values | Effect |
|---|---|---|
| `embed` | `1` | Compact chrome for iframes, "Open full map" link, zoom activates after a click |
| `year` | `1995`–`2027` | Initial year on the timeline |
| `mode` | `level` (default) or `index` | GDP per capita, or growth index with 1995 = 100 |
| `country` | ISO-3 code, e.g. `POL` | Country selected in the detail card |

Example: `…/interactive-3d-map-europe-gdp-index.html?embed=1&year=2027&mode=index&country=POL`

## Controls

Drag to orbit, scroll to zoom, `R` resets the view, `Space` plays the timeline,
`←`/`→` step one year, `Esc` closes the embed dialog.
