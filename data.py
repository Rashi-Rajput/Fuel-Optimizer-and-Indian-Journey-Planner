"""CSV loading, Indian city search, and a geographic journey graph."""
import csv
import difflib
from math import asin, atan2, cos, radians, sin, sqrt, ceil
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent
FUEL_STEP = 0.5  # litres per DP state; leg consumption rounds UP


def key(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return ' '.join(text.casefold().split())


def read_csv(name):
    with (ROOT / 'data' / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def distance(a, b):
    """Haversine kilometres between (latitude, longitude) pairs."""
    a, b = [list(map(radians, point)) for point in (a, b)]
    h = sin((b[0]-a[0])/2)**2 + cos(a[0])*cos(b[0])*sin((b[1]-a[1])/2)**2
    return 6371.0088 * 2 * asin(min(1, sqrt(h)))


def coords(row):
    return float(row['latitude']), float(row['longitude'])


def choose_city(prompt, cities, ask=None):
    ask = ask or input
    while True:
        query = key(ask(prompt))
        if not query:
            print('Enter a city name.')
            continue
        if query == 'list':
            print(', '.join(sorted({r['city'] for r in cities})))
            continue
        found = [r for r in cities if query in {key(r['city']), key(r['city']+', '+r['state'])}]
        if not found:
            found = [r for r in cities if query in {key(x) for x in r['aliases'].split('|')}]
        if len(found) == 1:
            return found[0]
        if found:
            for i, r in enumerate(found, 1):
                print(f"{i}. {r['city']}, {r['state']}")
            answer = ask('Choose city number: ').strip()
            if answer.isdigit() and 1 <= int(answer) <= len(found):
                return found[int(answer)-1]
        else:
            names = sorted({r['city'] for r in cities})
            suggestions = difflib.get_close_matches(query, [key(x) for x in names], cutoff=.3)
            print('City not found. Suggestions:', ', '.join(suggestions), '(or type list)')


def build_graph(source, destination, stations, tank, initial, mileage, corridor, reserve=0):
    """Forward corridor DAG using geodesic estimates, NOT road navigation."""
    a, b = coords(source), coords(destination)
    total = distance(a, b)
    if total < .01:
        raise ValueError('Choose different source and destination cities.')
    def bearing(x, y):
        lat1, lat2 = radians(x[0]), radians(y[0])
        lon = radians(y[1]-x[1])
        return atan2(sin(lon)*cos(lat2), cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(lon))
    direction = bearing(a, b)
    eligible, catalogue = [], []
    for station in stations:
        point = coords(station)
        arc, angle = distance(a, point)/6371.0088, bearing(a, point)-direction
        progress = 6371.0088 * atan2(sin(arc)*cos(angle), cos(arc))
        offset = abs(6371.0088 * asin(max(-1, min(1, sin(arc)*sin(angle)))))
        # Endpoint-near pumps are included; actual leg distances are preserved.
        in_corridor = offset <= corridor and -corridor <= progress <= total+corridor
        record = dict(station, progress_km=round(progress, 3), offset_km=round(offset, 3),
                      in_corridor=in_corridor, selected=False)
        catalogue.append(record)
        if in_corridor:
            eligible.append((max(0, min(total, progress)), station['station_id'], record))
    eligible.sort(key=lambda x: (x[0], x[1]))
    records = [dict(source, station_id='SOURCE', name=source['city'], price_inr_litre=None)]
    records += [row for _, _, row in eligible]
    records += [dict(destination, station_id='DESTINATION', name=destination['city'], price_inr_litre=None)]
    nodes = [r['station_id'] for r in records]
    metadata = dict(zip(nodes, records))
    edges = {u: [] for u in nodes}
    for i, u in enumerate(nodes[:-1]):
        for v in nodes[i+1:]:
            km = distance(coords(metadata[u]), coords(metadata[v]))
            demand = max(0, ceil(km / mileage / FUEL_STEP - 1e-10))
            if demand + (reserve if v == 'DESTINATION' else 0) <= (initial if u == 'SOURCE' else tank):
                edges[u].append((v, km, demand))
    # Each price is integer half-paise per 0.5 L; cost / 200 gives INR.
    prices = {u: round(float(metadata[u]['price_inr_litre'])*100)
              if metadata[u].get('price_inr_litre') is not None else None for u in nodes}
    return nodes, edges, prices, metadata, catalogue
