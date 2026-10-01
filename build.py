"""Builds stations.csv and stations-ODbL.txt from OpenStreetMap, for the Diadromi app.

python build.py [--cache DIR] [--retry-wait SECONDS]
With --cache, fuel.json and places.json in DIR are used if present, and saved there when downloaded.
Each Overpass query is tried 3 times (Overpass often answers 504); the files are written only at the end,
so a failed run leaves the last good list in place.
"""
import argparse
import csv
import datetime
import io
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'stations.csv')
LICENCE = os.path.join(ROOT, 'stations-ODbL.txt')
LICENCE_TEXT = '''stations.csv: fuel stations and place names from OpenStreetMap
© OpenStreetMap contributors. Downloaded {date} through the Overpass API.
This database is made available under the Open Database License (ODbL) 1.0:
https://opendatacommons.org/licenses/odbl/1-0/
Built by build.py in https://github.com/pavlidisnick/diadromi-data
'''
TRIES = 3
AREA = '(area["ISO3166-1"="GR"][admin_level=2];area["ISO3166-1"="CY"][admin_level=2];)->.a;'
QUERIES = {
    'fuel.json': '[out:json][timeout:180];' + AREA + 'nwr["amenity"="fuel"](area.a);out center tags;',
    'places.json': '[out:json][timeout:240];' + AREA +
                   'node["place"~"^(city|town|village|suburb|neighbourhood|quarter)$"](area.a);out tags center;',
}
AREA_MAX_M = 5000
SUBURB_MAX_M = 5000
TOWN_MAX_M = 15000
GRID = 20  # cells per degree (0.05°)


def fetch(name, cache, retry_wait):
    path = os.path.join(cache, name) if cache else None
    if path and os.path.isfile(path):
        return json.load(open(path, encoding='utf-8'))
    req = urllib.request.Request(
        'https://overpass-api.de/api/interpreter',
        data=urllib.parse.urlencode({'data': QUERIES[name]}).encode(),
        headers={'User-Agent': 'Diadromi-data/1.0 (https://github.com/pavlidisnick/diadromi-data)',
                 'Accept': 'application/json'},
    )
    for attempt in range(1, TRIES + 1):
        try:
            raw = urllib.request.urlopen(req, timeout=300).read()
            json.loads(raw)
            break
        except Exception as e:  # 504s, timeouts, a cut-off answer
            print('%s: try %d failed: %s' % (name, attempt, e), flush=True)
            if attempt == TRIES:
                raise
            time.sleep(retry_wait)
    if path:
        os.makedirs(cache, exist_ok=True)
    if path:
        open(path, 'wb').write(raw)
    return json.loads(raw)


def point(e):
    return (e['lat'], e['lon']) if 'lat' in e else (e['center']['lat'], e['center']['lon'])


def metres(a, b):
    x = (b[1] - a[1]) * math.cos(math.radians(a[0]))
    y = b[0] - a[0]
    return math.hypot(x, y) * 111_320


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache')
    ap.add_argument('--retry-wait', type=int, default=600)
    args = ap.parse_args()
    fuel = fetch('fuel.json', args.cache, args.retry_wait)['elements']
    places = [p for p in fetch('places.json', args.cache, args.retry_wait)['elements'] if p.get('tags', {}).get('name')]
    grid = defaultdict(list)
    for p in places:
        grid[(int(p['lat'] * GRID), int(p['lon'] * GRID))].append(p)

    def nearest(q, max_m, kinds=None):
        best = None
        k = (int(q[0] * GRID), int(q[1] * GRID))
        reach = max(2, math.ceil(max_m / 111_320 * GRID) + 1)
        for i in range(-reach, reach + 1):
            for j in range(-reach, reach + 1):
                for p in grid[(k[0] + i, k[1] + j)]:
                    if kinds and p['tags'].get('place') not in kinds:
                        continue
                    d = metres(q, (p['lat'], p['lon']))
                    if d <= max_m and (best is None or d < best[0]):
                        best = (d, p['tags']['name'])
        return best[1].strip() if best else ''

    rows = []
    for e in fuel:
        t = e.get('tags', {})
        lat, lon = point(e)
        brand = (t.get('brand') or t.get('name') or '').strip()
        area = nearest((lat, lon), AREA_MAX_M)
        # Wider names only for search (spec §10): the nearest suburb and the nearest town or city,
        # e.g. «Ανάληψη» and «Θεσσαλονίκη» around «Φάληρο».
        wider = [nearest((lat, lon), SUBURB_MAX_M, ('suburb',)), nearest((lat, lon), TOWN_MAX_M, ('town', 'city'))]
        district = ', '.join(dict.fromkeys(w for w in wider if w and w != area))
        rows.append([brand, area, t.get('addr:street', '').strip(), district, '%.5f' % lat, '%.5f' % lon])
    rows.sort(key=lambda r: (float(r[4]), float(r[5])))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['brand', 'area', 'street', 'district', 'lat', 'lon'])
    w.writerows(rows)
    open(OUT, 'w', encoding='utf-8', newline='').write(buf.getvalue())
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    open(LICENCE, 'w', encoding='utf-8', newline='\n').write(LICENCE_TEXT.format(date=today))
    print('%d stations, %d with a brand, %d with an area, %d with a district, %d bytes' %
          (len(rows), sum(1 for r in rows if r[0]), sum(1 for r in rows if r[1]), sum(1 for r in rows if r[3]),
           len(buf.getvalue().encode())))


if __name__ == '__main__':
    sys.exit(main())
