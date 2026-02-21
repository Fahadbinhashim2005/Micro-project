import pandas as pd
import os
from pulp import *

# ---------------------------------------------------
# Load Data (Robust Path + Header Handling)
# ---------------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_path, "..", "data")

facilities = pd.read_csv(os.path.join(data_path, "facilities.csv"))
warehouses = pd.read_csv(os.path.join(data_path, "warehouses.csv"))
transport = pd.read_csv(os.path.join(data_path, "transport_costs.csv"))

# ---------------------------------------------------
# Auto-clean column names (robust CSV handling)
# ---------------------------------------------------

def clean_columns(df):
    df.columns = (
        df.columns
        .astype(str)
        .str.replace('\ufeff', '', regex=False)
        .str.strip()
        .str.lower()
    )
    return df

facilities = clean_columns(facilities)
warehouses = clean_columns(warehouses)
transport = clean_columns(transport)

# Standardize ID column names
facilities = facilities.rename(columns={facilities.columns[0]: "facility_id"})
warehouses = warehouses.rename(columns={warehouses.columns[0]: "warehouse_id"})
transport = transport.rename(columns={
    transport.columns[0]: "warehouse_id",
    transport.columns[1]: "facility_id"
})

# ---------------------------------------------------
# Sets
# ---------------------------------------------------

F = facilities["facility_id"].tolist()
W = warehouses["warehouse_id"].tolist()

# ---------------------------------------------------
# Model Creation
# ---------------------------------------------------

model = LpProblem("Campus_Emergency_Logistics_Optimization", LpMinimize)

# ---------------------------------------------------
# Decision Variables
# ---------------------------------------------------

# Annual shipment from warehouse w to facility f
x = LpVariable.dicts(
    "Shipment",
    [(w, f) for w in W for f in F],
    lowBound=0
)

# Warehouse activation decision
y = LpVariable.dicts(
    "Activate",
    W,
    cat=LpBinary
)

# ---------------------------------------------------
# Objective Function (CORRECTED)
# ---------------------------------------------------
# x is already ANNUAL units
# transport cost is per unit (NO 365 here)

construction_term = lpSum(
    (warehouses.loc[i, "construction_cost"] / 8) *
    y[warehouses.loc[i, "warehouse_id"]]
    for i in warehouses.index
)

operational_term = lpSum(
    365 * warehouses.loc[i, "operational_cost_per_day"] *
    y[warehouses.loc[i, "warehouse_id"]]
    for i in warehouses.index
)

transport_term = lpSum(
    transport.loc[i, "cost_per_unit"] *
    x[(transport.loc[i, "warehouse_id"],
       transport.loc[i, "facility_id"])]
    for i in transport.index
)

model += construction_term + operational_term + transport_term

# ---------------------------------------------------
# Constraints
# ---------------------------------------------------

# 1️⃣ Demand Satisfaction (Annual)
for f in F:
    daily_demand = facilities.loc[
        facilities["facility_id"] == f,
        "daily_demand"
    ].values[0]

    model += lpSum(x[(w, f)] for w in W) == 365 * daily_demand

# 2️⃣ Capacity Constraints (Annual)
for w in W:
    daily_capacity = warehouses.loc[
        warehouses["warehouse_id"] == w,
        "daily_capacity"
    ].values[0]

    model += lpSum(x[(w, f)] for f in F) <= 365 * daily_capacity * y[w]

# 3️⃣ Redundancy Constraint
model += lpSum(y[w] for w in W) == 2

# 4️⃣ Budget Constraint (REALISTIC)
BUDGET = 2_000_000
model += model.objective <= BUDGET

# ---------------------------------------------------
# Solve Model
# ---------------------------------------------------

model.solve()

# ---------------------------------------------------
# Output Results
# ---------------------------------------------------

print("\n==============================")
print("OPTIMIZATION RESULTS")
print("==============================")
print("Status:", LpStatus[model.status])
print("Optimal Annual Cost: ${:,.2f}".format(value(model.objective)))

print("\nSelected Warehouses:")
for w in W:
    if y[w].varValue == 1:
        print(" -", w)

print("\nSample Shipment Plan (Non-Zero Flows):")
for w in W:
    for f in F:
        val = x[(w, f)].varValue
        if val is not None and val > 0:
            print(f"{w} → {f}: {val:.2f} units annually")

print("==============================")