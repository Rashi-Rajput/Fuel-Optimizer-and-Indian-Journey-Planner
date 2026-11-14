"""Bellman forward/backward DP on a DAG, O((N+E) C).

Fuel is in integer state units; edges are (next, distance, units).
Prices are integer costs per unit; None means no purchase at that node.
"""
from math import inf


def optimize(nodes, edges, prices, capacity, initial, reserve=0):
    if not nodes or len(nodes) != len(set(nodes)) or type(capacity) is not int or type(initial) is not int or not 0 <= initial <= capacity:
        raise ValueError('Invalid nodes or fuel limits.')
    if type(reserve) is not int or not 0 <= reserve <= capacity:
        raise ValueError('Reserve must be within tank capacity.')
    order = {u: i for i, u in enumerate(nodes)}
    for u in nodes:
        if prices[u] is not None and (type(prices[u]) is not int or prices[u] < 0):
            raise ValueError('Prices must be nonnegative integers, or None.')
        for v, km, used in edges[u]:
            if v not in order or order[v] <= order[u] or type(used) is not int or used < 0 or km < 0:
                raise ValueError('Use a forward DAG with nonnegative integer fuel demands.')
    forward = {u: [inf]*(capacity+1) for u in nodes}
    backward = {u: [inf]*(capacity+1) for u in nodes}
    parent, policy = {}, {}
    forward[nodes[0]][initial] = 0
    # Prefix minima: buy fuel first, then travel; no nested purchase loop.
    for u in nodes[:-1]:
        depart, origin = forward[u][:], list(range(capacity+1))
        for h in range(1, capacity+1):
            if prices[u] is not None and depart[h-1]+prices[u] < depart[h]:
                depart[h], origin[h] = depart[h-1]+prices[u], origin[h-1]
        for v, km, used in edges[u]:
            for h in range(used, capacity+1):
                if depart[h] < forward[v][h-used]:
                    forward[v][h-used] = depart[h]
                    parent[v, h-used] = (u, origin[h], h-origin[h], km, used)
    backward[nodes[-1]] = [0 if f >= reserve else inf for f in range(capacity+1)]
    for u in reversed(nodes[:-1]):
        for v, km, used in edges[u]:
            for f in range(used, capacity+1):
                if backward[v][f-used] < backward[u][f]:
                    backward[u][f] = backward[v][f-used]
                    policy[u, f] = (v, f-used, 0, km, used)
        for f in range(capacity-1, -1, -1):
            if prices[u] is not None and prices[u]+backward[u][f+1] < backward[u][f]:
                backward[u][f] = prices[u]+backward[u][f+1]
                v, left, buy, km, used = policy[u, f+1]
                policy[u, f] = (v, left, buy+1, km, used)
    end, left = nodes[-1], min(range(reserve, capacity+1), key=forward[nodes[-1]].__getitem__)
    cost = forward[end][left]
    if cost == inf:
        raise ValueError('No feasible journey. Try more starting fuel, a larger tank or a wider corridor.')
    assert cost == backward[nodes[0]][initial], 'Forward/backward answers disagree.'
    steps, v, fuel = [], end, left
    while v != nodes[0]:
        u, arrival, buy, km, used = parent[v, fuel]
        steps.append(dict(node=u, next=v, arrival=arrival, buy=buy, departure=arrival+buy,
                          distance_km=km, demand=used, next_fuel=fuel, cost=(prices[u] or 0)*buy))
        v, fuel = u, arrival
    return dict(cost=cost, final_fuel=left, steps=steps[::-1], forward=forward,
                backward=backward, policy=policy)


def just_enough(path, edges, prices, initial, reserve=0):
    fuel, cost = initial, 0
    for u, v in zip(path, path[1:]):
        used = next(demand for target, _, demand in edges[u] if target == v)
        target = used + (reserve if v == path[-1] else 0)
        buy = max(0, target-fuel)
        if buy and prices[u] is None:
            raise ValueError('No pump at the start of this leg.')
        cost += buy*(prices[u] or 0)
        fuel += buy-used
    return cost
