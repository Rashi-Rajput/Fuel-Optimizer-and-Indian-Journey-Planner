"""Synthetic fixtures belong in tests only. Runtime data comes from Indian CSVs."""
import random
import unittest
from math import inf, isclose
from data import read_csv, choose_city, build_graph, FUEL_STEP
from fuel_dp import optimize
from main import plan


def enumerate_plans(nodes, edges, prices, capacity, initial, reserve):
    best = inf
    reached = {u: [inf]*(capacity+1) for u in nodes}
    def visit(u, fuel, cost):
        nonlocal best
        reached[u][fuel] = min(reached[u][fuel], cost)
        if u==nodes[-1]:
            if fuel >= reserve:
                best = min(best, cost)
            return
        for buy in range(capacity-fuel+1) if prices[u] is not None else [0]:
            for v, _, used in edges[u]:
                if fuel+buy >= used:
                    visit(v, fuel+buy-used, cost+buy*(prices[u] or 0))
    visit(nodes[0], initial, 0)
    return best, reached


class OptimizationTests(unittest.TestCase):
    def test_both_directions_against_exhaustive_plans(self):
        rng = random.Random(2026)
        for _ in range(100):
            nodes = ['S', 'A', 'B', 'T']
            edges = {u: [(v, rng.randint(1, 6), rng.randint(1, 5)) for v in nodes[i+1:]
                         if rng.random()<.7] for i, u in enumerate(nodes)}
            prices = {u: rng.choice([None, 0, 4, 7, 10]) for u in nodes}
            initial, reserve = rng.randint(0, 4), rng.randint(0, 4)
            best, reached = enumerate_plans(nodes, edges, prices, 4, initial, reserve)
            if best==inf:
                with self.assertRaises(ValueError):
                    optimize(nodes, edges, prices, 4, initial, reserve)
                continue
            r = optimize(nodes, edges, prices, 4, initial, reserve)
            self.assertEqual((r['cost'], r['forward']), (best, reached))
            u, f, cost = 'S', initial, 0
            while u != 'T':
                v, left, buy, _, used = r['policy'][u, f]
                self.assertEqual(left, f+buy-used)
                self.assertLessEqual(f+buy, 4)
                self.assertTrue(prices[u] is not None or buy==0)
                cost += buy*(prices[u] or 0)
                u, f = v, left
            self.assertEqual(cost, best)
            self.assertGreaterEqual(f, reserve)

    def test_csv_contains_300_genuine_distinct_indian_pumps(self):
        pumps = read_csv('fuel_plan.csv')
        self.assertEqual(len(pumps), 300)
        self.assertEqual(len({r['station_id'] for r in pumps}), 300)
        self.assertTrue(all(float(r['petrol_inr_litre'])>0 and float(r['diesel_inr_litre'])>0 for r in pumps))
        self.assertTrue(all(r['captured_at'] and r['source_url'].startswith('https://') for r in pumps))

    def test_city_names_aliases_and_reprompt(self):
        cities = read_csv('indian_cities.csv')
        self.assertGreater(len(cities), 300)
        self.assertEqual(choose_city('', cities, lambda _: 'mumbai')['city'], 'Mumbai')
        answers = iter(['not-a-city', 'Bangalore'])
        city = choose_city('', cities, lambda _: next(answers))
        self.assertIn(city['city'], ('Bengaluru', 'Bangalore'))

    def test_real_indian_journeys_have_feasible_plans(self):
        cities = read_csv('indian_cities.csv')
        for source, destination, fuel in [('Delhi','Mumbai','petrol'), ('Chennai','Bengaluru','diesel'),
                                          ('Lucknow','Jaipur','petrol')]:
            a = choose_city('', cities, lambda _: source)
            b = choose_city('', cities, lambda _: destination)
            summary, result, nodes, metadata, catalogue, f, back = plan(a, b, fuel, 50, 10, 15, 5, 100)
            self.assertEqual(summary['cost_inr'], summary['backward_cost_inr'])
            self.assertEqual(summary['savings_inr'], round(summary['baseline_inr']-summary['cost_inr'], 2))
            self.assertLessEqual(summary['cost_inr'], summary['fixed_route_cost_inr']+.001)
            self.assertLessEqual(summary['fixed_route_cost_inr'], summary['baseline_inr']+.001)
            self.assertTrue(isclose(f[nodes[-1]], back[nodes[0]]))
            self.assertEqual(len(catalogue), 300)
            self.assertGreaterEqual(summary['final_fuel_litres'], 5)
            self.assertEqual(10+summary['purchased_litres']-sum(s['leg_model_litres'] for s in summary['steps']),
                             summary['final_fuel_litres'])
            for s in summary['steps']:
                self.assertLessEqual(s['departure_litres'], 50)
                self.assertGreaterEqual(s['next_fuel_litres'], 0)
                self.assertGreaterEqual(s['leg_model_litres']+.001, s['leg_km']/15)

    def test_infeasible_initial_fuel_and_equal_cities(self):
        cities = read_csv('indian_cities.csv')
        a = choose_city('', cities, lambda _: 'Delhi')
        b = choose_city('', cities, lambda _: 'Mumbai')
        with self.assertRaisesRegex(ValueError, 'No feasible journey'):
            plan(a, b, 'petrol', 50, 0, 15, 5, 100)
        with self.assertRaisesRegex(ValueError, 'different source'):
            plan(a, a, 'petrol', 50, 10, 15, 5, 100)

    def test_invalid_dag_and_reserve(self):
        zero_leg = optimize(['S','T'], {'S':[('T', 0, 0)],'T':[]}, {'S':None,'T':None}, 8, 0)
        self.assertEqual(zero_leg['cost'], 0)
        with self.assertRaisesRegex(ValueError, 'forward DAG'):
            optimize(['S','T'], {'S':[('S', 10, 1)],'T':[]}, {'S':100,'T':None}, 8, 2)
        with self.assertRaisesRegex(ValueError, 'Reserve'):
            optimize(['S','T'], {'S':[],'T':[]}, {'S':100,'T':None}, 8, 2, 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
