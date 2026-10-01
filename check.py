"""Checks a station list before it is published: the same rules the Diadromi app applies before using one.

python check.py stations.csv
Exits 1 when the header lacks brand/lat/lon, there are fewer than 5,000 stations, or a station lies outside
Greece and Cyprus.
"""
import csv
import sys

MIN_STATIONS = 5000
LAT = (34.5, 41.8)
LON = (19.3, 34.7)


def main(path):
    rows = list(csv.reader(open(path, encoding='utf-8', newline='')))
    if not rows:
        return 'empty file'
    header = [h.strip() for h in rows[0]]
    missing = [c for c in ('brand', 'lat', 'lon') if c not in header]
    if missing:
        return 'missing columns: %s' % ', '.join(missing)
    lat, lon = header.index('lat'), header.index('lon')
    stations = [r for r in rows[1:] if len(r) == len(header)]
    if len(stations) < MIN_STATIONS:
        return 'only %d stations' % len(stations)
    for r in stations:
        try:
            y, x = float(r[lat]), float(r[lon])
        except ValueError:
            return 'bad coordinates: %s' % r
        if not (LAT[0] <= y <= LAT[1] and LON[0] <= x <= LON[1]):
            return 'outside Greece and Cyprus: %s' % r
    print('%d stations, all good' % len(stations))
    return None


if __name__ == '__main__':
    error = main(sys.argv[1])
    if error:
        print('check failed: ' + error, file=sys.stderr)
        sys.exit(1)
