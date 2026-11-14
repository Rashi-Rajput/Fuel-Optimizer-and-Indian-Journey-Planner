"""Interactive Indian journey planner. Run: python main.py"""
import csv
import io
import json
import math
import sys
import webbrowser
from contextlib import redirect_stdout
from decimal import Decimal, ROUND_HALF_UP
from data import ROOT, FUEL_STEP, read_csv, choose_city, build_graph
from fuel_dp import optimize, just_enough
from shortest_path import shortest_path


def money(half_paise):
    return float((Decimal(half_paise)/200).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def number(prompt, minimum=0, maximum=math.inf, half_litres=False):
    while True:
        try:
            value = float(input(prompt))
            if not math.isfinite(value) or not minimum <= value <= maximum or (half_litres and not (value/FUEL_STEP).is_integer()):
                raise ValueError
            return value
        except ValueError:
            print(f'Enter a number between {minimum:g} and {maximum:g}' +
                  (f', in {FUEL_STEP:g}-litre increments.' if half_litres else '.'))


def write_rows(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plan(source, destination, fuel, tank, initial, mileage, reserve, corridor):
    stations = [dict(r, price_inr_litre=r[f'{fuel}_inr_litre']) for r in read_csv('fuel_plan.csv')]
    c, f0, r0 = [round(x/FUEL_STEP) for x in (tank, initial, reserve)]
    nodes, edges, prices, meta, catalogue = build_graph(source, destination, stations, c, f0, mileage, corridor, r0)
    result = optimize(nodes, edges, prices, c, f0, r0)
    shortest, distance_f, distance_b = shortest_path(nodes, edges)
    pairs = set(zip(shortest, shortest[1:]))
    fixed_edges = {u: [e for e in edges[u] if (u, e[0]) in pairs] for u in nodes}
    fixed = optimize(nodes, fixed_edges, prices, c, f0, r0)
    baseline = just_enough(shortest, edges, prices, f0, r0)
    steps = [dict(sequence=i, city=meta[s['node']]['city'], station=meta[s['node']]['name'],
                  station_id=s['node'], arrival_litres=s['arrival']*FUEL_STEP,
                  buy_litres=s['buy']*FUEL_STEP, departure_litres=s['departure']*FUEL_STEP,
                  price_inr_litre=meta[s['node']].get('price_inr_litre') or '',
                  cost_inr=money(s['cost']), next_city=meta[s['next']]['city'],
                  next_station_id=s['next'], leg_km=round(s['distance_km'], 3),
                  leg_model_litres=s['demand']*FUEL_STEP,
                  next_fuel_litres=s['next_fuel']*FUEL_STEP)
             for i, s in enumerate(result['steps'], 1)]
    selected = {s['node'] for s in result['steps']}
    for record in catalogue:
        record['selected'] = record['station_id'] in selected
    summary = dict(source=source['city'], destination=destination['city'], fuel=fuel,
                   tank_litres=tank, initial_litres=initial, mileage_km_litre=mileage,
                   reserve_litres=reserve, corridor_km=corridor, fuel_step_litres=FUEL_STEP,
                   data_rows=len(stations), graph_nodes=len(nodes), graph_edges=sum(map(len, edges.values())),
                   cost_inr=money(result['cost']), backward_cost_inr=money(result['backward'][nodes[0]][f0]),
                   final_fuel_litres=result['final_fuel']*FUEL_STEP,
                   purchased_litres=sum(s['buy_litres'] for s in steps),
                   estimated_distance_km=sum(s['distance_km'] for s in result['steps']),
                   shortest_distance_km=distance_f[nodes[-1]], baseline_inr=money(baseline),
                   fixed_route_cost_inr=money(fixed['cost']),
                   savings_inr=round(money(baseline)-money(result['cost']), 2),
                   dates=sorted({r['captured_at'][:10] for r in stations}),
                   shortest_path=shortest, optimal_path=[s['node'] for s in result['steps']]+[nodes[-1]],
                   names={u: meta[u]['city'] for u in nodes}, steps=steps,
                   distance_method='Haversine straight-line estimates; not road distances or navigation')
    return summary, result, nodes, meta, catalogue, distance_f, distance_b


def save_and_show(summary, result, nodes, meta, catalogue, distance_f, distance_b):
    out = ROOT/'outputs'
    out.mkdir(exist_ok=True)
    write_rows(out/'fuel_plan.csv', catalogue)  # all 300 genuine records, with route flags
    write_rows(out/'journey_plan.csv', summary['steps'])
    write_rows(out/'shortest_path.csv', [dict(node=u, city=meta[u]['city'],
               forward_km=distance_f[u] if math.isfinite(distance_f[u]) else 'INF',
               backward_km=distance_b[u] if math.isfinite(distance_b[u]) else 'INF') for u in nodes])
    for direction in ('forward', 'backward'):
        rows = [dict(node=u, city=meta[u]['city'], **{f'{f*FUEL_STEP:g}L':
                cost/200 if math.isfinite(cost) else 'INF' for f, cost in enumerate(result[direction][u])}) for u in nodes]
        write_rows(out/f'{direction}_dp.csv', rows)
    from journey_graph import draw_graph
    draw_graph(summary, nodes, meta, out)
    (out/'results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    capture = io.StringIO()
    with redirect_stdout(capture):
        print(f"\nYOUR JOURNEY: {summary['source']} -> {summary['destination']}")
        print(f"{summary['data_rows']} Indian station records; {len(nodes)-2} within your corridor.")
        print(f"Price snapshot dates: {summary['dates'][0]} to {summary['dates'][-1]} (not live prices).")
        print('Distances are straight-line estimates, NOT road routes. Check an actual road map before travel.')
        print('Shortest feasible path:', ' -> '.join(summary['names'][u] +
              (' (start)' if u==nodes[0] else ' (end)' if u==nodes[-1] else ' (pump)') for u in summary['shortest_path']))
        print('Fuel-cost path:', ' -> '.join(summary['names'][u] for u in summary['optimal_path']))
        print(f"Shortest estimate: {summary['shortest_distance_km']:.1f} km | Fuel-plan estimate: {summary['estimated_distance_km']:.1f} km")
        print('\nCity / station                          Arrive L  Buy L  Leave L   INR/L   Cost INR')
        for s in summary['steps']:
            price = f"{float(s['price_inr_litre']):.2f}" if s['price_inr_litre'] else '--'
            print(f"{s['city']+' / '+s['station']:<39.39} {s['arrival_litres']:8.1f} {s['buy_litres']:6.1f} "
                  f"{s['departure_litres']:8.1f} {price:>7} {s['cost_inr']:10.2f}")
        print(f"Forward optimum: INR {summary['cost_inr']:.2f} | Backward optimum: INR {summary['backward_cost_inr']:.2f}")
        print(f"Just-enough buying on shortest path: INR {summary['baseline_inr']:.2f}")
        print(f"Optimal buying on shortest path: INR {summary['fixed_route_cost_inr']:.2f}")
        print(f"Savings against just-enough baseline: INR {summary['savings_inr']:.2f}")
        print(f"Purchased: {summary['purchased_litres']:.1f} L | Arrival fuel: {summary['final_fuel_litres']:.1f} L")
        print('Initial fuel is already owned; its value is excluded from every comparison.')
        print('Leg fuel rounds up to 0.5 L; the optimum applies to this discretized corridor model.')
        print('Saved full DP tables, 300-row fuel_plan.csv, journey_plan.csv and shortest_path_graph.png in', out)
    text = capture.getvalue()
    print(text)
    (out/'sample_output.txt').write_text(text, encoding='utf-8')


def main():
    cities = read_csv('indian_cities.csv')
    print('FUEL OPTIMISE | INDIAN JOURNEY PLANNER')
    print(f'{len(cities)} Indian cities available. Type list to browse. Prices are a dated snapshot.')
    print('This offline planner uses straight-line distances, not a driving-road network.')
    while True:
        source = choose_city('Where are you starting from? ', cities)
        destination = choose_city('Where do you want to travel? ', cities)
        if source == destination:
            print('You are already at your destination. Choose a different journey.')
            continue
        fuel = input('Fuel type (petrol/diesel): ').strip().casefold()
        if fuel not in ('petrol', 'diesel'):
            print('Choose petrol or diesel. Please enter the journey again.')
            continue
        tank = number('Tank capacity (litres): ', FUEL_STEP, 500, True)
        mileage = number('Vehicle mileage (km/litre): ', .1, 200)
        initial = number('Fuel currently in tank (litres): ', 0, tank, True)
        reserve = number('Minimum fuel on arrival (litres): ', 0, tank, True)
        corridor = number('Station corridor width from direct route (km): ', 1, 500)
        try:
            save_and_show(*plan(source, destination, fuel, tank, initial, mileage, reserve, corridor))
            if '--no-open' not in sys.argv and input('Open the shortest-path graph? [Y/n] ').strip().casefold() != 'n':
                webbrowser.open((ROOT/'outputs/shortest_path_graph.svg').as_uri())
        except ValueError as error:
            print(error)
        if input('Plan another journey? [y/N] ').strip().casefold() != 'y':
            break


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print('\nJourney planner closed.')
