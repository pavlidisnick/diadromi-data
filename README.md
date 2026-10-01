# diadromi-data

Public data for the [Diadromi](https://play.google.com/store/apps/details?id=com.pavlidisnick.diadromi) app.

## Fuel stations

- `stations.csv`: every fuel station in Greece and Cyprus from OpenStreetMap, one row per station:
  `brand,area,street,district,lat,lon` (UTF-8, header row, sorted by `lat`). `area` is the nearest named place;
  `district` the nearest suburb and town or city, for search.
- Served at <https://pavlidisnick.github.io/diadromi-data/stations.csv>. The app checks once a day whether it changed
  and downloads it only then; nothing about the user is sent.
- Rebuilt every Monday at 03:00 UTC by `.github/workflows/stations.yml`: `build.py` queries the Overpass API,
  `check.py` checks the result (columns, at least 5,000 stations, all inside Greece and Cyprus), and the file is
  committed only when it changed. A failed run leaves the last good list published.

## Licence

`stations.csv` is a database derived from OpenStreetMap: © OpenStreetMap contributors, made available under the
[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). See `stations-ODbL.txt`.
