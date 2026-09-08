# Embedding the map

The map is a single static page hosted at
`https://pavlinov.github.io/3d-map/europe-economic-map-textured.html` and can be embedded in any site
with an iframe. The **`</>` button** in the map's toolbar generates the snippet and copies it to the clipboard.

## Snippet (responsive, 16:10)

```html
<div style="position:relative;width:100%;max-width:1400px;aspect-ratio:16 / 10;margin:0 auto">
  <iframe src="https://pavlinov.github.io/3d-map/europe-economic-map-textured.html?embed=1"
    title="Europe Economic Evolution — interactive 3D GDP map, 1995–2031"
    style="position:absolute;inset:0;width:100%;height:100%;border:0;border-radius:12px"
    loading="lazy" allowfullscreen></iframe>
</div>
```

## URL parameters

| Parameter | Values | Effect |
|---|---|---|
| `embed=1` | — | Embed mode: hides the keyboard hint, shows an "Open full map ↗" link. Also enabled automatically inside an iframe. |
| `metric` | `pc` (default), `gdp`, `growth` | Initial metric |
| `year` | `1995`…last year | Initial year (default: last year) |
| `sel` | ISO-3166 alpha-3, e.g. `UKR` | Initially pinned country (default `DEU`) |
| `labels=0` | — | Hide country codes |
| `flat=1` | — | Do not extrude by value |
| `crimea` | `UKR` (default), `RUS` | Which country Crimea is drawn as part of (also switchable in the legend). GDP figures are national statistics and do not change. |

Example: `…/europe-economic-map-textured.html?metric=gdp&year=2010&sel=UKR&embed=1`

The "Copy link" button in the embed panel produces a shareable URL with the current view; untick
"Start from the current view" for a plain link.
