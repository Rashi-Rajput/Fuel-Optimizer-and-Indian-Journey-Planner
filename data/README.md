# Indian journey data

`fuel_plan.csv` has 300 unique Indian station records. `indian_cities.csv`
contains 3,788 Indian city entries, coordinates, states and alternate spellings.
The application reads these files on every journey. Edit verified prices in
the CSV, not in Python. Keep units INR per litre; keep petrol and diesel separate.

Pump catalogue columns include `station_id`, actual pump `name`, associated
GeoNames `city`, `state`, original `station_city`, latitude/longitude, separate
petrol/diesel prices, `captured_at`, and `source_url`. The associated city is
within 30 km of the pump; it is not an assertion that the pump is at its centre.

Price/coordinate source: ForceGT India Fuel Pumps, BPCL snapshot, captured
2026-10-19. https://github.com/ForceGT/india-fuel-pumps
Retrieved 2026-11-14. MIT license: copyright 2026 Gaurav Thakkar; retained as
`source/fuel_dataset_LICENSE.txt`. Source records contain standard PETROL and
DIESEL products. No fabricated prices, duplicate padding, US price conversions,
premium-fuel substitutions or random station coordinates are used.

City source: GeoNames cities15000 and admin1CodesASCII, downloaded 2026-11-14.
https://download.geonames.org/export/dump/
GeoNames data is licensed CC BY 4.0:
https://creativecommons.org/licenses/by/4.0/
The Indian subset is derived from those files; alternate names are pipe-separated.

The original compressed source files are retained under `source`. Run
`python prepare_data.py` from the project directory to rebuild both CSVs without
network access. Preparation sorts Indian cities by source population and selects
one distinct nearby BPCL pump with both standard fuel prices for each of 300
cities. Geographic coverage is a sample, not every Indian city or pump.

Distances are computed geographically, not from a road database. Price dates
are shown at run time. Current pump prices and drivable routes must be verified
before an actual journey. The optimizer cannot infer missing roads from these CSVs.
