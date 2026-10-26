# diadromi-data

Public data for the [Diadromi](https://play.google.com/store/apps/details?id=com.pavlidisnick.diadromi) app.

## Fuel stations

- `stations.csv`: every fuel station in Greece and Cyprus from OpenStreetMap, one row per station:
  `brand,area,street,district,lat,lon,nomos` (UTF-8, header row, sorted by `lat`). `area` is the nearest named place;
  `district` the nearest suburb and town or city, for search; `nomos` the fuel bulletin's prefecture (Greece only), from
  OpenStreetMap's regional units joined up in `nomoi.py`.
- Served at <https://pavlidisnick.github.io/diadromi-data/stations.csv>. The app checks once a day whether it changed
  and downloads it only then; nothing about the user is sent.
- Rebuilt every Monday at 03:00 UTC by `.github/workflows/stations.yml`: `build.py` queries the Overpass API,
  `check.py` checks the result (columns, at least 5,000 stations, all inside Greece and Cyprus), and the file is
  committed only when it changed. A failed run leaves the last good list published.

## Fuel prices

- `fuel-prices.csv`: the average price of each fuel per prefecture on one day, from the Ministry of Development's
  public daily bulletin (`fuelprices.gr/files/deltia/IMERISIO_DELTIO_ANA_NOMO_DD_MM_YYYY.pdf`):
  `date,nomos,el,en,unleaded95,unleaded100,diesel,lpg` (€/litre incl. VAT, empty when the bulletin has no price),
  51 prefectures and `ΕΛΛΑΔΑ`, the national weighted average.
- Served at <https://pavlidisnick.github.io/diadromi-data/fuel-prices.csv>; the app checks it once a day.
- Refreshed by `.github/workflows/prices.yml` at 08:00 and 14:00 UTC: `prices.py` downloads the newest bulletin
  (the day's own is published the next morning), reads it with `pdftotext`, and writes the file only when at least
  45 prefectures read cleanly and every price is in its range. Source: Ministry of Development.

## Licence

`stations.csv` is a database derived from OpenStreetMap: © OpenStreetMap contributors, made available under the
[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See `stations-ODbL.txt`.
