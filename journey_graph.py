"""Draw the actual computed graph paths; no preset route or city positions."""


def draw_graph(summary, nodes, metadata, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, (map_ax, path_ax) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    lon = {u: float(metadata[u]['longitude']) for u in nodes}
    lat = {u: float(metadata[u]['latitude']) for u in nodes}
    map_ax.scatter(list(lon.values()), list(lat.values()), s=23, c='#b5bcc6', label='Eligible stations')
    for path, color, style, label in [(summary['optimal_path'], '#168064', '-', 'Minimum fuel cost'),
                                      (summary['shortest_path'], '#315ab3', '--', 'Shortest feasible distance')]:
        map_ax.plot([lon[u] for u in path], [lat[u] for u in path], style, color=color, lw=2, marker='o', label=label)
    from data import distance, coords
    endpoints = [nodes[0], nodes[-1]]
    labels = {u for u in summary['optimal_path'] + summary['shortest_path']
              if u in endpoints or min(distance(coords(metadata[u]), coords(metadata[e])) for e in endpoints) > 50}
    for i, u in enumerate(v for v in nodes if v in labels):
        map_ax.annotate(metadata[u]['city'], (lon[u], lat[u]), xytext=(6, 8 if i%2 else -15),
                        textcoords='offset points', fontsize=9)
    map_ax.set(title=f"{summary['source']} to {summary['destination']}", xlabel='Longitude', ylabel='Latitude')
    map_ax.grid(alpha=.18)
    map_ax.legend(loc='best')
    path = summary['shortest_path']
    path_ax.set_xlim(-.5, max(1, len(path)-.5))
    path_ax.set_ylim(-.7, .8)
    for i, u in enumerate(path):
        path_ax.scatter(i, 0, s=140, c='#315ab3', zorder=3)
        suffix = '\n(start)' if i==0 else '\n(end)' if i==len(path)-1 else '\n(pump)'
        path_ax.text(i, -.3, metadata[u]['city']+suffix, ha='center', fontsize=max(7, 12-len(path)//4))
        if i:
            path_ax.annotate('', xy=(i-.05, 0), xytext=(i-1+.05, 0), arrowprops={'arrowstyle': '->', 'color': '#315ab3'})
            km = distance(coords(metadata[path[i-1]]), coords(metadata[u]))
            path_ax.text(i-.5, .18, f'{km:.1f} km', ha='center', fontsize=9)
    path_ax.set_title(f"Shortest feasible path | {summary['shortest_distance_km']:.1f} km estimated", fontsize=11)
    path_ax.axis('off')
    fig.suptitle('Journey graph from Indian CSV data', fontsize=16, fontweight='bold')
    fig.text(.5, .015, 'Straight-line estimates, not road navigation. Fuel prices are a dated snapshot.', ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .04, 1, .95))
    fig.savefig(output/'shortest_path_graph.png', dpi=160)
    fig.savefig(output/'shortest_path_graph.svg')
    plt.close(fig)
