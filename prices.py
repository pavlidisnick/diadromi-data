"""Builds fuel-prices.csv from the Ministry of Development's daily bulletin of average fuel prices per prefecture.

python prices.py [--pdf FILE] [--date YYYY-MM-DD]
Downloads the newest bulletin (today's is usually published the next morning, so it tries today and the 7 days
before), reads it with pdftotext (poppler-utils) and writes fuel-prices.csv. With --pdf, reads that file instead.
The file is written only when the bulletin read cleanly, so a failed run leaves the last good prices in place.

The bulletin is a public file on fuelprices.gr: no account, key or request is needed to download it.
"""
import argparse
import csv
import datetime
import io
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

from nomoi import GREECE, GREECE_NAMES, NOMOI

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'fuel-prices.csv')
URL = 'https://www.fuelprices.gr/files/deltia/IMERISIO_DELTIO_ANA_NOMO_{d:%d_%m_%Y}.pdf'
DAYS_BACK = 7
MIN_NOMOI = 45

# The bulletin's columns, left to right; a missing one is always at the end (heating oil out of season, or a
# prefecture without LPG). Each price must fall in its range (€/litre), or the row is dropped.
FUELS = ['unleaded95', 'unleaded100', 'diesel', 'lpg', 'heating']
RANGES = {'unleaded95': (1.0, 3.5), 'unleaded100': (1.0, 3.8), 'diesel': (0.9, 3.5), 'lpg': (0.4, 2.0), 'heating': (0.6, 2.5)}
PRICE = re.compile(r'\d,\d{3}')


def download():
    """The newest bulletin's bytes and its date; None if none of the last days' is published."""
    today = datetime.date.today()
    for back in range(DAYS_BACK + 1):
        day = today - datetime.timedelta(days=back)
        req = urllib.request.Request(URL.format(d=day), headers={'User-Agent': 'Diadromi-data/1.0 (https://github.com/pavlidisnick/diadromi-data)'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                # A missing day answers 200 with a small HTML error page, not a 404.
                if r.headers.get_content_type() == 'application/pdf' and body.startswith(b'%PDF'):
                    return body, day
        except Exception as e:
            print('%s: %s' % (day, e))
    return None


def text(pdf_bytes):
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, 'bulletin.pdf')
        open(pdf, 'wb').write(pdf_bytes)
        return subprocess.run(['pdftotext', '-enc', 'UTF-8', '-layout', pdf, '-'], check=True, capture_output=True).stdout.decode('utf-8')


def parse(txt):
    """Bulletin name → {fuel: price}, for every row whose prices all fall in their ranges."""
    rows = {}
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith('ΝΟΜΟΣ '):
            name = re.split(r'\s{2,}', line)[0][len('ΝΟΜΟΣ '):].strip()
        elif line.startswith('ΠΑΝΕΛΛΗΝΙΟΣ'):
            name = GREECE
        else:
            continue
        values = [float(p.replace(',', '.')) for p in PRICE.findall(line)]
        if not values or len(values) > len(FUELS):
            continue
        prices = dict(zip(FUELS, values))
        if all(RANGES[f][0] <= v <= RANGES[f][1] for f, v in prices.items()) and (name in NOMOI or name == GREECE):
            rows[name] = prices
        else:
            print('skipped: %s' % line)
    return rows


def write(rows, day):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['date', 'nomos', 'el', 'en'] + FUELS[:4])
    for name in sorted(rows, key=lambda n: (n == GREECE, n)):
        el, en = GREECE_NAMES if name == GREECE else NOMOI[name]
        w.writerow([day.isoformat(), name, el, en] + ['%.3f' % rows[name][f] if f in rows[name] else '' for f in FUELS[:4]])
    open(OUT, 'w', encoding='utf-8', newline='').write(buf.getvalue())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pdf')
    ap.add_argument('--date')
    args = ap.parse_args()
    if args.pdf:
        got = (open(args.pdf, 'rb').read(), datetime.date.fromisoformat(args.date) if args.date else datetime.date.today())
    else:
        got = download()
    if got is None:
        print('No bulletin in the last %d days' % DAYS_BACK, file=sys.stderr)
        return 1
    pdf, day = got
    rows = parse(text(pdf))
    nomoi = sum(1 for n in rows if n != GREECE)
    if nomoi < MIN_NOMOI:
        print('Only %d prefectures read from the %s bulletin' % (nomoi, day), file=sys.stderr)
        return 1
    write(rows, day)
    print('%s: %d prefectures%s' % (day, nomoi, ' and the national average' if GREECE in rows else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
