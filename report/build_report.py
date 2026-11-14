"""Build the five-page PDF. Only this optional report script uses ReportLab."""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
pdfmetrics.registerFont(TTFont('TNR', 'C:/Windows/Fonts/times.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Bold', 'C:/Windows/Fonts/timesbd.ttf'))
pdfmetrics.registerFont(TTFont('TNR-Italic', 'C:/Windows/Fonts/timesi.ttf'))
pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-Bold', italic='TNR-Italic')
W = A4[0] - 84
styles = {
    'body': ParagraphStyle('body', fontName='TNR', fontSize=12, leading=18,
                           alignment=TA_JUSTIFY, spaceAfter=6),
    'head': ParagraphStyle('head', fontName='TNR-Bold', fontSize=12, leading=18,
                           spaceBefore=7, spaceAfter=5, keepWithNext=True),
    'center': ParagraphStyle('center', fontName='TNR', fontSize=12, leading=18,
                             alignment=TA_CENTER, spaceAfter=6),
    'cover': ParagraphStyle('cover', fontName='TNR-Bold', fontSize=12, leading=18,
                            alignment=TA_CENTER, spaceAfter=6),
    'title': ParagraphStyle('title', fontName='TNR-Bold', fontSize=16, leading=22,
                            alignment=TA_CENTER, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName='TNR', fontSize=12, leading=18, alignment=TA_CENTER),
    'ref': ParagraphStyle('ref', fontName='TNR', fontSize=12, leading=18,
                          alignment=TA_LEFT, spaceAfter=5, splitLongWords=True),
}
story, source = [], []


def p(text, style='body'):
    story.append(Paragraph(text, styles[style]))
    source.append(text.replace('<b>', '**').replace('</b>', '**'))


def head(text):
    p(text, 'head')
    source[-1] = '## ' + source[-1]


def table(rows, widths=None):
    data = [[Paragraph(escape(str(x)), styles['cell']) for x in row] for row in rows]
    t = Table(data, colWidths=widths or [W / len(rows[0])] * len(rows[0]), repeatRows=1, hAlign='CENTER')
    t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#D9D9D9')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8E8E8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.extend([t, Spacer(1, 7)])
    source.append('| ' + ' | '.join(str(x) for x in rows[0]) + ' |')
    source.append('| ' + ' | '.join('---' for _ in rows[0]) + ' |')
    source.extend(['| ' + ' | '.join(str(x) for x in row) + ' |' for row in rows[1:]])


def page():
    story.append(PageBreak())
    source.append('\n--- PAGE BREAK ---\n')


def footer(canvas, doc):
    canvas.setFont('TNR', 12)
    canvas.drawCentredString(A4[0] / 2, 23, str(doc.page))


def build():
    r = json.loads((ROOT / 'outputs/results.json').read_text(encoding='utf-8'))
    # Cover structure follows the supplied institute report format.
    story.append(Spacer(1, 18))
    p('JAYPEE INSTITUTE OF INFORMATION TECHNOLOGY, NOIDA', 'cover')
    story.append(Spacer(1, 15))
    p('B.TECH V SEMESTER', 'cover')
    p('REPORT FOR PBL', 'cover')
    p('OPTIMIZATION METHODS &amp; APPLICATIONS', 'title')
    p('(26B12MA312)', 'cover')
    story.append(Spacer(1, 10))
    logo = HERE / 'assets/jiit_logo.png'
    if logo.exists():
        story.append(Image(str(logo), width=96, height=108))
    story.append(Spacer(1, 12))
    p('Indian Fuel Journey Planning<br/>Using Dynamic Programming', 'title')
    story.append(Spacer(1, 8))
    p('Submitted by', 'cover')
    p('Group: ____________________', 'center')
    p('Group Head: ________________________________________', 'center')
    table([['S.No.', 'Enrolment No.', 'Mobile', 'Name', 'Batch']] +
          [[i, '', '', '', ''] for i in range(1, 6)], [36, 105, 95, W - 291, 55])
    story.append(Spacer(1, 8))
    p('<b>Under the Supervision of:</b><br/>Dr. Anjali<br/>Department of Mathematics<br/>JIIT, Sector 62, Noida', 'ref')

    page()
    head('1. Objective')
    p('Build an interactive Indian journey planner that asks for source, destination and vehicle details, '
      'then minimizes fuel purchase cost using CSV station data. Demonstrate Bellman\'s principle, '
      'forward and backward recursion, shortest-path DP, and fuel inventory allocation under tank and reserve constraints.')
    head('2. Introduction')
    p('A traveller needs to decide where to buy fuel and how much to carry. Different station prices '
      'make minimum distance and minimum cost different objectives. This terminal-only Python application '
      'uses actual Indian city names, station coordinates and dated prices rather than preset routes. '
      'It is inspired by Fuel Route Optimizer [1] and applies finite-state DP [2].')
    head('3. Problem definition')
    p(f'The input catalogue contains {r["data_rows"]} distinct Indian pumps [3], with petrol and diesel '
      'prices in INR/L, capture dates and source URLs. GeoNames supplies city coordinates and aliases [4]. '
      'The application prompts for cities, fuel type, tank capacity, mileage, starting fuel, arrival reserve '
      'and corridor width. No journey, station price or vehicle value is fixed in the application code.')
    p('S and T are the requested city coordinates. Candidate pumps lie within the chosen geographic corridor '
      'and are ordered by forward progress. Edges join later nodes only, forming a directed acyclic graph '
      '(DAG). Haversine distances are straight-line estimates; they do not describe a drivable road network. '
      'No fuel may be bought at a city coordinate unless the plan reaches a listed pump.')
    p('<b>Mathematical model.</b> Choose an S-to-T path and purchases q to minimize '
      'J = &#8721; p<sub>u</sub>q<sub>u</sub>. Fuel states use units of 0.5 L; '
      'p<sub>u</sub> is the INR price per unit, half the CSV price per litre. For distance d and mileage e, '
      'leg demand is r<sub>uv</sub> = ceil(d<sub>uv</sub> / (0.5e)). At arrival state (u,f), '
      '0 &#8804; q &#8804; C &#8722; f, f + q &#8805; r<sub>uv</sub>, and next fuel is '
      'g = f + q &#8722; r<sub>uv</sub>. At S, q = 0; at T, f must meet the requested reserve.')
    p('Starting fuel is already owned and excluded from every cost comparison. Prices are deterministic '
      'snapshots, not live quotations. Tolls and travel time are excluded. Rounding demand upward is '
      'conservative within the geographic model; the guarantee concerns the sampled, forward-only, '
      'discretized graph, not an actual road journey.')

    page()
    head('4. Methodology')
    head('Bellman principle of optimality')
    p('From an arrival state (u,f), an optimal journey must have an optimal continuation. Otherwise '
      'replacing its remaining plan with a cheaper feasible continuation would reduce total cost, '
      'contradicting optimality [2]. Node and fuel determine future choices, while purchase costs add. '
      'A node-only state would lose fuel inventory and is insufficient.')
    head('Forward recursion relation')
    p('F(u,f) is minimum expenditure already incurred when arriving at u with f fuel units. '
      'Initialize F(S,f<sub>0</sub>) = 0 and every other entry to infinity. In topological order, '
      'enumerate feasible purchase and travel decisions, with g = f + q &#8722; r<sub>uv</sub>:')
    p('<b>F(v,g) &#8592; min {F(v,g), F(u,f) + p<sub>u</sub>q}.</b>', 'center')
    p('The optimum is min F(T,f) over terminal fuel meeting the reserve. Save the predecessor '
      'state and purchase whenever a value improves, then backtrack to recover the actual journey.')
    head('Backward recursion relation')
    p('V(u,f) is minimum future purchase cost. Initialize V(T,f) = 0 for sufficient reserve, '
      'and infinity otherwise. Process nodes in reverse topological order:')
    p('<b>V(u,f) = min<sub>feasible (v,q)</sub> {p<sub>u</sub>q + V(v, f + q &#8722; r<sub>uv</sub>)}.</b>', 'center')
    p('A state without a feasible continuation has value infinity. The program saves minimizing '
      'actions as a backward policy and checks that V(S,f<sub>0</sub>) equals the forward optimum. '
      'Purchases distribute limited tank capacity across stations: carrying cheaper fuel can reduce '
      'expensive purchases later while preserving fuel balance.')
    head('Shortest path and implementation')
    p('For distance, L(S) = 0 and L(v) = min<sub>(u,v)</sub> {L(u) + d<sub>uv</sub>}. '
      'Backward values satisfy H(T) = 0 and H(u) = min<sub>(u,v)</sub> {d<sub>uv</sub> + H(v)}. '
      'The algorithm checks L(T) = H(S) and reconstructs the shortest feasible path. Fuel DP is '
      'itself a shortest path on expanded states (u,f), weighted by purchase costs.')
    p('The implementation separates purchases from travel and uses prefix and suffix purchase passes '
      'to evaluate the recursions in O((N + E)C) time and O(NC) memory. Geographic graph construction '
      'takes O(N<super>2</super>) distance checks. Distance-only DP takes O(N + E) time. '
      'All optimization uses Python\'s standard library; Matplotlib draws the graph.')

    page()
    head('4. Methodology continued')
    head('User inputs and computed results')
    p(f'This saved example runs from <b>{escape(r["source"])} to {escape(r["destination"])}</b>, '
      f'using {r["fuel"]}. The traveller enters a {r["tank_litres"]:g} L tank, '
      f'{r["mileage_km_litre"]:g} km/L mileage, {r["initial_litres"]:g} L initial fuel, '
      f'{r["reserve_litres"]:g} L arrival reserve and a {r["corridor_km"]:g} km corridor. '
      f'The generated graph has {r["graph_nodes"]} nodes and {r["graph_edges"]} feasible edges. '
      f'Price capture date range is {r["dates"][0]} to {r["dates"][-1]}.')
    table([['Strategy', 'Estimated km', 'Cost INR'],
           ['Shortest path, just enough fuel', f'{r["shortest_distance_km"]:.1f}', f'{r["baseline_inr"]:.2f}'],
           ['Shortest path, optimal purchases', f'{r["shortest_distance_km"]:.1f}', f'{r["fixed_route_cost_inr"]:.2f}'],
           ['Joint path and fuel optimization', f'{r["estimated_distance_km"]:.1f}', f'{r["cost_inr"]:.2f}']],
          [W-200, 105, 95])
    p(f'Forward and backward optima both equal INR {r["cost_inr"]:.2f}. Savings against '
      f'just-enough buying are INR {r["savings_inr"]:.2f}. All strategies use the same starting fuel, '
      'reserve and rounding convention. Extra distance is judged only through its fuel cost.')
    p('<b>Selected purchase plan</b>', 'center')
    table([['City', 'Arrive L', 'Buy L', 'Leave L', 'Cost INR']] +
          [[s['city'], f'{s["arrival_litres"]:g}', f'{s["buy_litres"]:g}',
            f'{s["departure_litres"]:g}', f'{s["cost_inr"]:.2f}'] for s in r['steps'][:6]],
          [W-320, 80, 70, 80, 90])
    p(f'Total purchased fuel is {r["purchased_litres"]:g} L and modelled arrival fuel is '
      f'{r["final_fuel_litres"]:g} L. The source row has no purchase. The complete leg plan, '
      'pump names and identifiers are saved in journey_plan.csv; the table shows at most six legs.')
    p('<b>DP values along the chosen journey</b>', 'center')
    def load_dp(name):
        with (ROOT/'outputs'/name).open(encoding='utf-8', newline='') as f:
            return {row['node']: row for row in csv.DictReader(f)}
    forward, backward = load_dp('forward_dp.csv'), load_dp('backward_dp.csv')
    states = [(s['station_id'], s['arrival_litres'], s['city']) for s in r['steps']]
    states.append(('DESTINATION', r['final_fuel_litres'], r['destination']))
    table([['Arrival city', 'Fuel L', 'F cost INR', 'V cost INR']] +
          [[city, f'{fuel:g}', f'{float(forward[u][f"{fuel:g}L"]):.2f}',
            f'{float(backward[u][f"{fuel:g}L"]):.2f}'] for u, fuel, city in states[:6]],
          [W-290, 70, 110, 110])
    p('F records spending already incurred; V records future spending. Full matrices for every '
      'candidate node and fuel level are exported as CSV. The 300-row fuel_plan.csv is the candidate '
      'catalogue with corridor and selected flags, not a claim that every pump is a journey stop.')

    page()
    head('4. Methodology continued')
    head('Shortest path graph')
    graph = ROOT/'outputs/shortest_path_graph.png'
    story.append(Image(str(graph), width=W, height=W*2/3))
    source.append('![Computed shortest and fuel paths](../outputs/shortest_path_graph.png)')
    p('The blue dashed path minimizes estimated distance; the green path minimizes fuel purchase '
      'cost. Grey points are eligible stations. The lower directed graph shows shortest-path legs '
      'and calculated distances. Both paths are derived from the current user input and CSV data.')
    head('5. Conclusion')
    p('The application accepts Indian journey inputs and reconstructs feasible refuelling decisions '
      'with matching forward and backward DP costs. Six tests pass, including independent enumeration '
      'on 100 small random DAGs and three Indian journeys. The model demonstrates optimal substructure '
      'and scarce fuel inventory allocation. Dated prices, sampled coverage, forward-only paths and '
      'straight-line distances limit practical accuracy; verify road distances and current pump prices before travel.')
    head('6. References')
    p('[1] Vinayakula06. Fuel Route Optimizer. '
      '<link href="https://github.com/vinayakula06/fuel-optimizer">github.com/vinayakula06/fuel-optimizer</link>.', 'ref')
    p('[2] D. Bertsekas. MIT OCW 6.231, Dynamic Programming and Stochastic Control, 2015, Lectures 2 and 3. '
      '<link href="https://ocw.mit.edu/courses/6-231-dynamic-programming-and-stochastic-control-fall-2015/pages/lecture-notes/">ocw.mit.edu, course 6.231</link>.', 'ref')
    p('[3] ForceGT. India Fuel Pumps, BPCL snapshot. MIT license. '
      '<link href="https://github.com/ForceGT/india-fuel-pumps">github.com/ForceGT/india-fuel-pumps</link>.', 'ref')
    p('[4] GeoNames. Cities15000 and administrative codes. CC BY 4.0. '
      '<link href="https://download.geonames.org/export/dump/">download.geonames.org/export/dump</link>.', 'ref')
    doc = SimpleDocTemplate(str(HERE/'Fuel_Optimise_Report.pdf'), pagesize=A4,
                           leftMargin=42, rightMargin=42, topMargin=35, bottomMargin=38,
                           title='Indian Fuel Journey Planning Using Dynamic Programming', author='')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    (HERE/'report_source.md').write_text('\n\n'.join(source), encoding='utf-8')
    print('Created', HERE/'Fuel_Optimise_Report.pdf')


if __name__ == '__main__':
    build()
