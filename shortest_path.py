"""Forward and backward dynamic programming for shortest distance on a DAG."""
from math import inf


def shortest_path(nodes, roads):
    forward = dict.fromkeys(nodes, inf)
    backward = dict.fromkeys(nodes, inf)
    parent = {}
    forward[nodes[0]] = 0
    for u in nodes:
        for v, km, _ in roads[u]:
            if forward[u] + km < forward[v]:
                forward[v] = forward[u] + km
                parent[v] = u
    backward[nodes[-1]] = 0
    for u in reversed(nodes[:-1]):
        backward[u] = min((km + backward[v] for v, km, _ in roads[u]), default=inf)
    if forward[nodes[-1]] == inf:
        raise ValueError("Destination is unreachable.")
    path = [nodes[-1]]
    while path[-1] != nodes[0]:
        path.append(parent[path[-1]])
    return list(reversed(path)), forward, backward
