import pandas as pd
import os
import folium
from pulp import *

# --------------------------------------------------
# Load Data
# --------------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_path, "..", "data")

facilities = pd.read_csv(os.path.join(data_path, "facilities.csv"))
warehouses = pd.read_csv(os.path.join(data_path, "warehouses.csv"))
transport = pd.read_csv(os.path.join(data_path, "transport_costs.csv"))
travel = pd.read_csv(os.path.join(data_path, "travel_time.csv"))

# --------------------------------------------------
# Clean Columns
# --------------------------------------------------

def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.replace('\ufeff', '')
        .str.strip()
        .str.lower()
    )
    return df

facilities = clean_columns(facilities)
warehouses = clean_columns(warehouses)
transport = clean_columns(transport)
travel = clean_columns(travel)

# --------------------------------------------------
# Convert Data to Dictionaries (Faster Access)
# --------------------------------------------------

facility_demand = dict(zip(facilities.facility_id, facilities.daily_demand))
warehouse_capacity = dict(zip(warehouses.warehouse_id, warehouses.daily_capacity))
construction_cost = dict(zip(warehouses.warehouse_id, warehouses.construction_cost))
operational_cost = dict(zip(warehouses.warehouse_id, warehouses.operational_cost_per_day))

transport_cost = {
    (row.warehouse_id, row.facility_id): row.cost_per_unit
    for _, row in transport.iterrows()
}

travel_time = {
    (row.warehouse_id, row.facility_id): row.minutes
    for _, row in travel.iterrows()
}

# --------------------------------------------------
# Coordinates
# --------------------------------------------------

facility_coords = {
"RB_BLOCK":[9.5835,76.5225],
"VB_BLOCK":[9.5838,76.5227],
"CLC_BLOCK":[9.5840,76.5230],
"AB_BLOCK":[9.5833,76.5222],
"NORTH_BLOCK":[9.5843,76.5226],
"SOUTH_BLOCK":[9.5828,76.5224],
"AMENITY_BLOCK":[9.5831,76.5232],
"AK_BLOCK":[9.5841,76.5223],
"MINI_AUDITORIUM":[9.5836,76.5233],
"AMPHITHEATRE":[9.5832,76.5235],
"CENTRAL_COMPLEX":[9.5834,76.5229],
"LAB_BLOCKS":[9.5842,76.5234],
"MAIN_ENTRY":[9.5826,76.5220]
}

warehouse_coords = {
"WH_NORTH":[9.5845,76.5226],
"WH_SOUTH":[9.5825,76.5224],
"WH_EAST":[9.5837,76.5238],
"WH_WEST":[9.5830,76.5218]
}

# --------------------------------------------------
# Sets
# --------------------------------------------------

F = list(facility_demand.keys())
W = list(warehouse_capacity.keys())
resources = ["food", "medicine", "water"]

# --------------------------------------------------
# Model
# --------------------------------------------------

model = LpProblem("Smart_Campus_Logistics", LpMinimize)

# --------------------------------------------------
# Decision Variables
# --------------------------------------------------

x = LpVariable.dicts(
    "Shipment",
    [(w, f, r) for w in W for f in F for r in resources],
    lowBound=0
)

y = LpVariable.dicts("Activate", W, cat=LpBinary)

# --------------------------------------------------
# Objective Function
# --------------------------------------------------

model += lpSum(
    (construction_cost[w]/8 + 365*operational_cost[w]) * y[w]
    for w in W
) + lpSum(
    transport_cost[(w,f)] * x[(w,f,r)]
    for (w,f) in transport_cost
    for r in resources
)

# --------------------------------------------------
# Demand Constraints
# --------------------------------------------------

for f in F:
    annual = facility_demand[f] * 365
    for r in resources:
        model += lpSum(x[(w,f,r)] for w in W) >= annual

# --------------------------------------------------
# Warehouse Capacity
# --------------------------------------------------

for w in W:
    annual_cap = warehouse_capacity[w] * 365
    for r in resources:
        model += lpSum(x[(w,f,r)] for f in F) <= annual_cap * y[w]

# --------------------------------------------------
# Travel Time Constraint
# --------------------------------------------------

MAX_TIME = 30

for (w,f), t in travel_time.items():
    if t > MAX_TIME:
        for r in resources:
            model += x[(w,f,r)] == 0

# --------------------------------------------------
# Redundancy Constraint
# --------------------------------------------------

model += lpSum(y[w] for w in W) >= 2

# --------------------------------------------------
# Solve Model
# --------------------------------------------------

model.solve()

print("\n==============================")
print("SMART CAMPUS LOGISTICS RESULTS")
print("==============================")
print("Status:", LpStatus[model.status])
print("Optimal Annual Cost:", round(value(model.objective),2))

# --------------------------------------------------
# Selected Warehouses
# --------------------------------------------------

print("\nSelected Warehouses:")
selected = []

for w in W:
    if y[w].varValue == 1:
        selected.append(w)
        print("•", w)

# --------------------------------------------------
# Shipment Summary
# --------------------------------------------------

print("\nSample Shipment Plan:")

for w in W:
    for f in F:
        for r in resources:
            val = x[(w,f,r)].varValue
            if val and val > 0:
                print(f"{w} → {f} ({r}) : {round(val,2)} units/year")

# --------------------------------------------------
# Map Visualization
# --------------------------------------------------

campus_center = [9.509856, 76.550732]

m = folium.Map(location=campus_center, zoom_start=17)

# Warehouses

for w in W:

    if w not in warehouse_coords:
        continue

    color = "green" if y[w].varValue == 1 else "red"

    folium.Marker(
        warehouse_coords[w],
        popup=f"Warehouse: {w}",
        icon=folium.Icon(color=color, icon="home")
    ).add_to(m)

# Facilities

for f in F:

    if f not in facility_coords:
        continue

    folium.Marker(
        facility_coords[f],
        popup=f,
        icon=folium.Icon(color="blue")
    ).add_to(m)

# Routes

for w in W:
    for f in F:
        for r in resources:

            val = x[(w,f,r)].varValue

            if val and val > 0 and w in warehouse_coords and f in facility_coords:

                folium.PolyLine(
                    [warehouse_coords[w], facility_coords[f]],
                    color="green",
                    weight=3
                ).add_to(m)

# --------------------------------------------------
# Save Map
# --------------------------------------------------

html_path = os.path.join(base_path, "campus_logistics_map.html")
m.save(html_path)

print("\nMap saved:", html_path)
print("==============================")