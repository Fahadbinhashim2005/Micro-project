import pandas as pd
import os
import folium
import math
from pulp import *

# --------------------------------------------------
# Load Data
# --------------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_path, "..", "data")

facilities = pd.read_csv(os.path.join(data_path, "facilities.csv"))
warehouses = pd.read_csv(os.path.join(data_path, "warehouses.csv"))

# --------------------------------------------------
# Clean Columns
# --------------------------------------------------

def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.replace('\ufeff','')
        .str.strip()
        .str.lower()
    )
    return df

facilities = clean_columns(facilities)
warehouses = clean_columns(warehouses)

# --------------------------------------------------
# Convert Data
# --------------------------------------------------

facility_demand = dict(zip(facilities.facility_id, facilities.daily_demand))
warehouse_capacity = dict(zip(warehouses.warehouse_id, warehouses.daily_capacity))
construction_cost = dict(zip(warehouses.warehouse_id, warehouses.construction_cost))
operational_cost = dict(zip(warehouses.warehouse_id, warehouses.operational_cost_per_day))

# --------------------------------------------------
# Coordinates
# --------------------------------------------------

facility_coords = {

"RB_BLOCK":[9.51030,76.55040],
"VB_BLOCK":[9.51005,76.55020],
"CLC_BLOCK":[9.51035,76.55075],
"AB_BLOCK":[9.50985,76.55010],

"NORTH_BLOCK":[9.51065,76.55060],
"SOUTH_BLOCK":[9.50945,76.55070],

"AMENITY_BLOCK":[9.50975,76.55030],
"AK_BLOCK":[9.51015,76.55000],

"MINI_AUDITORIUM":[9.50995,76.55045],
"AMPHITHEATRE":[9.50970,76.55050],

"CENTRAL_COMPLEX":[9.51010,76.55055],
"LAB_BLOCKS":[9.50935,76.55085],

"MAIN_ENTRY":[9.50920,76.55105]
}

warehouse_coords = {

"WH_NORTH":[9.5158,76.5520],
"WH_SOUTH":[9.5038,76.5505],
"WH_EAST":[9.5105,76.5565],
"WH_WEST":[9.5100,76.5455]

}

# --------------------------------------------------
# Haversine Distance
# --------------------------------------------------

def haversine(coord1, coord2):

    lat1,lon1 = coord1
    lat2,lon2 = coord2

    R = 6371

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)

    a = (
        math.sin(dlat/2)**2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon/2)**2
    )

    c = 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))

    return R*c

# --------------------------------------------------
# Sets
# --------------------------------------------------

F = list(facility_demand.keys())
W = list(warehouse_capacity.keys())

resources = ["food","medicine","water"]

# --------------------------------------------------
# Distance Matrix
# --------------------------------------------------

distance = {}

for w in W:
    for f in F:

        if w in warehouse_coords and f in facility_coords:

            distance[(w,f)] = haversine(
                warehouse_coords[w],
                facility_coords[f]
            )

# --------------------------------------------------
# Optimization Model
# --------------------------------------------------

model = LpProblem("Smart_Campus_Logistics",LpMinimize)

x = LpVariable.dicts(
    "Shipment",
    [(w,f,r) for w in W for f in F for r in resources],
    lowBound=0
)

y = LpVariable.dicts("Activate",W,cat=LpBinary)

DIST_COST = 1.2

model += lpSum(
    (construction_cost[w]/8 + 365*operational_cost[w])*y[w]
    for w in W
) + lpSum(
    DIST_COST*distance[(w,f)]*x[(w,f,r)]
    for (w,f) in distance
    for r in resources
)

# --------------------------------------------------
# Demand
# --------------------------------------------------

for f in F:

    annual = facility_demand[f]*365

    for r in resources:

        model += lpSum(x[(w,f,r)] for w in W) >= annual

# --------------------------------------------------
# Capacity
# --------------------------------------------------

for w in W:

    annual_cap = warehouse_capacity[w]*365

    for r in resources:

        model += lpSum(x[(w,f,r)] for f in F) <= annual_cap*y[w]

# --------------------------------------------------
# Redundancy
# --------------------------------------------------

model += lpSum(y[w] for w in W) >= 2

# --------------------------------------------------
# Solve
# --------------------------------------------------

model.solve()

print("\n======================")
print("OPTIMIZATION RESULTS")
print("======================")

print("Status:",LpStatus[model.status])
print("Total Cost:",round(value(model.objective),2))

print("\nSelected Warehouses:")

for w in W:
    if y[w].varValue==1:
        print("-",w)

print("\nShipment Plan:")

shipment_summary = {}

for w in W:

    if y[w].varValue!=1:
        continue

    for f in F:

        total = sum(
            x[(w,f,r)].varValue
            for r in resources
            if x[(w,f,r)].varValue
        )

        if total:

            shipment_summary[(w,f)] = total

            print(
                f"{w} -> {f} | "
                f"{round(distance[(w,f)],2)} km | "
                f"{round(total)} units/year"
            )

# --------------------------------------------------
# Map
# --------------------------------------------------

campus_center=[9.509856,76.550732]

m = folium.Map(location=campus_center,zoom_start=16)

# Warehouses

for w in W:

    if w not in warehouse_coords:
        continue

    color="green" if y[w].varValue==1 else "red"

    folium.Marker(
        warehouse_coords[w],
        popup=f"Warehouse {w}",
        icon=folium.Icon(color=color)
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

# --------------------------------------------------
# Routes
# --------------------------------------------------

label_index = 0

for (w,f),total in shipment_summary.items():

    start = warehouse_coords[w]
    end = facility_coords[f]

    folium.PolyLine(
        [start,end],
        color="green",
        weight=3,
        opacity=0.8
    ).add_to(m)

    # midpoint
    mid_lat=(start[0]+end[0])/2
    mid_lon=(start[1]+end[1])/2

    offset = label_index*0.00008

    folium.Marker(
        [mid_lat+offset,mid_lon-offset],
        icon=folium.DivIcon(
            html=f"""
            <div style="
            font-size:11px;
            background:white;
            padding:2px;
            border-radius:3px;">
            {round(distance[(w,f)],2)} km
            </div>
            """
        )
    ).add_to(m)

    label_index += 1
# --------------------------------------------------
# Add Map Legend
# --------------------------------------------------

legend_html = '''
<div style="
position: fixed; 
bottom: 40px; left: 40px; width: 220px; height: 130px; 
background-color: white;
border:2px solid grey;
z-index:9999;
font-size:14px;
padding:10px;
">

<b>Smart Campus Logistics</b><br><br>

<i style="color:green;">●</i> Active Warehouse<br>
<i style="color:red;">●</i> Inactive Warehouse<br>
<i style="color:blue;">●</i> Campus Facility<br>
<i style="color:green;">━━</i> Supply Route<br>
📏 Distance (km)

</div>
'''

m.get_root().html.add_child(folium.Element(legend_html))
# --------------------------------------------------
# Save Map
# --------------------------------------------------

html_path=os.path.join(base_path,"campus_logistics_map.html")

m.save(html_path)

print("\nMap saved:",html_path)

# --------------------------------------------------
# Export Map to PNG
# --------------------------------------------------

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

png_path = os.path.join(base_path, "campus_logistics_map.png")

try:

    service = Service(ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1400,1000")

    driver = webdriver.Chrome(service=service, options=options)

    driver.get("file:///" + html_path)

    # wait for map to fully load
    time.sleep(5)

    driver.save_screenshot(png_path)

    driver.quit()

    print("Map image saved:", png_path)

except Exception as e:

    print("PNG export failed:", e)