"""Rebuild Indian CSVs from retained, attributed snapshots. Runs offline."""
import csv
import gzip
import json
import zipfile
from math import cos, radians
from data import ROOT, distance


def write_csv(name, rows):
    with (ROOT/'data'/name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare():
    folder = ROOT/'data/source'
    states = dict(line.rstrip().split('\t')[:2] for line in (folder/'admin1CodesASCII.txt').read_text(encoding='utf-8').splitlines())
    with zipfile.ZipFile(folder/'cities15000.zip') as archive:
        records = csv.reader(archive.read('cities15000.txt').decode('utf-8').splitlines(), delimiter='\t')
        cities = [dict(city=r[2], state=states.get('IN.'+r[10], r[10]), latitude=r[4], longitude=r[5],
                       population=int(r[14]), aliases=r[3].replace(',', '|')) for r in records if r[8]=='IN']
    cities.sort(key=lambda r: (-r['population'], r['city']))
    write_csv('indian_cities.csv', cities)
    with gzip.open(folder/'bpcl-raw.jsonl.gz', 'rt', encoding='utf-8') as f:
        raw = [json.loads(line) for line in f]
    pumps = []
    for r in raw:
        products = {x['name']: x['priceInr'] for x in r.get('products', [])}
        if products.get('PETROL') and products.get('DIESEL') and 8 <= r['lat'] <= 37 and 68 <= r['lng'] <= 98:
            pumps.append(r)
    chosen, ids = [], set()
    for city in cities:
        lon_weight = cos(radians(float(city['latitude'])))
        nearby = min((r for r in pumps if r['stationId'] not in ids),
                     key=lambda r: (float(city['latitude'])-r['lat'])**2 +
                     ((float(city['longitude'])-r['lng'])*lon_weight)**2)
        if distance((float(city['latitude']), float(city['longitude'])), (nearby['lat'], nearby['lng'])) > 30:
            continue
        products = {x['name']: x['priceInr'] for x in nearby['products']}
        chosen.append(dict(station_id=nearby['stationId'], name=nearby['name'], city=city['city'],
                           state=city['state'], station_city=nearby.get('city') or '',
                           latitude=nearby['lat'], longitude=nearby['lng'],
                           petrol_inr_litre=products['PETROL'], diesel_inr_litre=products['DIESEL'],
                           captured_at=nearby['capturedAt'], source_url=nearby['sourceUrl']))
        ids.add(nearby['stationId'])
        if len(chosen)==300:
            break
    if len(chosen) != 300:
        raise ValueError('Source snapshot did not yield 300 distinct priced pumps.')
    write_csv('fuel_plan.csv', chosen)
    print(f'Prepared {len(cities)} Indian cities and {len(chosen)} distinct priced stations.')


if __name__ == '__main__':
    prepare()
