# Fuel Optimise Indian Journey Planner

A small terminal application. The traveller enters the source and destination;
routes, prices and answers are calculated from CSV data. No route or city price
is embedded in the application code. The graph compares shortest feasible
distance with minimum fuel cost.

## Run

```powershell
cd C:\Users\Dell\Desktop\OOPSIE\opti\fuel_optimise_simple
python -m pip install -r requirements.txt
python main.py
```

On Windows you can also double-click `start_journey.bat` after installing the requirements.

The application asks for source city, destination city, petrol or diesel, tank
capacity, mileage in km/L, current fuel, minimum arrival fuel, and corridor width
in kilometres. Fuel inputs use half-litre increments. Type `list` at either city
prompt to browse the Indian cities; old names such as Bangalore are aliases from
the city dataset. Ambiguous names show numbered choices. There are no assumed
vehicle values: enter your own. After each trip it offers to open the graph and
plan another journey. `python main.py --no-open` skips the graph-opening question.

## Data and the 300 rows

- `data/indian_cities.csv`: 3,788 Indian city entries and aliases from GeoNames.
- `data/fuel_plan.csv`: exactly 300 distinct Indian pumps, with actual station
  coordinates, separate petrol/diesel prices in INR/L, capture dates and source
  URLs. One pump is sampled near each of 300 populous cities. The `city` column
  identifies its associated GeoNames city; `station_city` preserves the source's
  city wording. The station need not be at the city's centre.
- `outputs/fuel_plan.csv`: all 300 records, annotated with journey corridor and
  selected-path flags. These are candidate records, not 300 claimed trip stops.
- `outputs/journey_plan.csv`: only the calculated journey legs and purchases.

The station prices are a snapshot captured on **19 October 2026**, not live pump
quotes. Petrol and diesel are not mixed with premium grades. Update the CSV
with verified prices before relying on a cost estimate. Missing prices are not
filled with invented values. The original US dataset remains in the sibling
`fuel-optimizer/data` folder and is not relabelled as Indian data.

## Distance model and scope

The supplied files contain no drivable road network. This offline version
therefore uses Haversine straight-line distances between actual coordinates.
The graph is a planning/optimization demonstration, **not road navigation**;
straight lines can cross terrain or areas without connecting roads. Compare
with a road map before travelling. It does not estimate travel time or tolls.

A station enters the DAG when its cross-track distance is within the user's
corridor and its along-track position is between the endpoints, allowing the
same corridor tolerance at either end. Stations are sorted by forward progress;
only transitions to later stations are considered. Slight backward movement
within endpoint groups can occur; arbitrary cyclic detours are excluded.
Changing the corridor or the sampled station coverage changes the feasible set.

The source and destination are city coordinates, not invented fuel pumps. No
fuel may be bought there. Starting fuel must reach a real CSV station, and the
last leg must preserve the requested arrival reserve. Each leg's fuel demand
is rounded **up** to 0.5 L. Thus quantities are conservative for the geographic
model, and the optimality claim applies to that finite model, not a continuous
road journey. Rounding can overstate consumption by less than 0.5 L per leg.
Geographic distance itself generally understates road distance.

## Optimization concepts

**Bellman's principle.** The state is `(node, arrival fuel)` before purchasing.
Future feasible actions depend on those two values, so replacing an expensive
continuation by a cheaper one from the same state improves the whole plan.

**Forward recursion.** Let `F[u,f]` be minimum spending already incurred on
arrival. Set `F[source,initial]=0`, all other values infinity. A feasible buy `q`
and leg using `r` units produce `g=f+q-r` and the update
`F[v,g]=min(F[v,g], F[u,f]+price[u]*q)`.
Here fuel quantities are in 0.5 L units and price means cost per such unit.

**Backward recursion.** Let `V[u,f]` be minimum future cost. At the destination,
`V[end,f]=0` if `f>=reserve`, otherwise infinity. Process nodes in reverse order:
`V[u,f]=min(price[u]*q + V[v,f+q-r])` over feasible purchases and next nodes.
Forward and backward answers must agree. Prefix/suffix purchase passes avoid
enumerating every quantity separately, giving `O((N+E) C)` time and `O(N C)`
space, where C is capacity in half-litre states.

**Shortest path.** Forward distance values satisfy
`L[v]=min(L[u]+distance[u,v])`, with `L[source]=0`. Backward values satisfy
`H[u]=min(distance[u,v]+H[v])`, with `H[end]=0`. Fuel DP is also a shortest path
on expanded `(node,fuel)` states. Saving predecessors reconstructs both paths.

**Resource allocation.** Tank space and carried fuel are limited resources.
The purchase decisions allocate fuel buying across stations while maintaining
inventory balance. The journey workflow contains no separate fleet-benefit
example; fuel allocation is handled directly by the route DP.

## Outputs and verification

Each successful run regenerates the 300-row catalogue, selected journey,
`results.json`, `sample_output.txt`, both complete fuel DP tables, shortest-path
distance values, and `shortest_path_graph.png` / `.svg`. Existing outputs are
overwritten by the latest **successful** journey; an infeasible journey prints
an explanation and preserves the previous outputs.

Costs exclude the value of already-owned starting fuel. Comparisons use the
same reserve and discretization: just-enough purchases on the shortest path,
optimal purchases on that path, and joint path/purchase optimization.
The saved tables preserve half-paise precision; displayed amounts round to
two decimals. Savings are the difference between the displayed rounded totals.

```powershell
python -m unittest -v
python prepare_data.py          # rebuild CSVs from retained source snapshots
python report/build_report.py  # rebuild the five-page report from latest output
```

Tests compare DP with independent enumeration on 100 random tiny DAGs and check
real Indian journeys, resource balances, reserve constraints, aliases, invalid
inputs, and the 300 distinct records. Synthetic data exists only in tests.

## Sources and attribution

Indian pump records: [ForceGT India Fuel Pumps](https://github.com/ForceGT/india-fuel-pumps),
BPCL source snapshot; MIT license, copyright 2026 Gaurav Thakkar. License retained
in `data/source/fuel_dataset_LICENSE.txt`. Source snapshot is retained compressed
for offline reproducibility. This project is not affiliated with BPCL.

Indian cities: [GeoNames cities15000 and administrative codes](https://download.geonames.org/export/dump/),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Only Indian rows are
extracted; aliases are preserved in the CSV. Original snapshots are retained.

Project inspiration: [vinayakula06/fuel-optimizer](https://github.com/vinayakula06/fuel-optimizer).
Optimization reference: [MIT OCW 6.231, Lectures 2 and 3](https://ocw.mit.edu/courses/6-231-dynamic-programming-and-stochastic-control-fall-2015/pages/lecture-notes/).
