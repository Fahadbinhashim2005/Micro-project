# Campus City Logistics – Emergency Supply Distribution Optimization

## Problem Statement
As an optimization analyst for **Campus City Logistics**, the objective is to design an optimal emergency supply distribution network to serve essential campus facilities. The existing manual distribution approach is inefficient, costly, and lacks redundancy during emergency scenarios. A data-driven optimization model is required to ensure reliable and cost-effective supply allocation.

---

## Goal
Determine the optimal warehouse selection and supply distribution plan that:

- Minimizes total annual operational cost  
- Satisfies demand at all campus facilities  
- Respects warehouse capacity limitations  
- Ensures redundancy through controlled warehouse selection  
- Operates within the allocated annual budget  

---

## Dataset Overview

### Facilities Data
Eight essential campus facilities were considered for emergency supply planning.

| Facility ID | Facility Name | Type | Daily Demand (Units) |
|------------|---------------|------|----------------------|
| MEDICAL_CENTER | Campus Medical Center | Critical | 90 |
| ENGINEERING_BLOCK | Engineering Block | Academic | 40 |
| SCIENCE_BLOCK | Science Complex | Academic | 45 |
| BOYS_HOSTEL | Boys Hostel | Residential | 60 |
| GIRLS_HOSTEL | Girls Hostel | Residential | 55 |
| CENTRAL_LIBRARY | Central Library | Academic | 30 |
| FOOD_COURT | Food Court | Essential | 50 |
| SPORTS_COMPLEX | Sports Complex | Recreational | 35 |

**Total Daily Demand ≈ 405 Units/Day**

---

### Warehouse Data

| Warehouse ID | Warehouse Name | Daily Capacity (Units) | Construction Cost | Operational Cost / Day |
|-------------|---------------|------------------------|-------------------|------------------------|
| WH_NORTH | North Depot | 420 | $310,000 | $850 |
| WH_SOUTH | South Depot | 380 | $295,000 | $780 |
| WH_EAST | East Depot | 450 | $330,000 | $910 |
| WH_WEST | West Depot | 400 | $305,000 | $820 |

**Total Available Capacity = 1,650 Units/Day**

---

### Transportation Costs

| Parameter | Value |
|---------|-------|
| Cost Range | $3.6 – $4.8 per unit |
| Basis | Relative campus distance and accessibility |

---

## Financial Constraints

| Parameter | Value |
|---------|-------|
| Annual Budget | $2,000,000 |
| Planning Period | 365 Days |
| Construction Amortization | 8 Years |

---

## Solution Approach

### Optimization Technique
The problem is formulated as a **Mixed Integer Linear Programming (MILP)** model and implemented using the **PuLP** optimization library in Python.

---

### Decision Variables

| Variable | Type | Description |
|--------|------|-------------|
| Warehouse Activation | Binary | 1 if warehouse is selected, 0 otherwise |
| Shipment Quantity | Continuous | Annual units shipped from warehouse to facility |

---

## Optimization Results

### Financial Summary

| Metric | Value |
|------|-------|
| Total Annual Cost | $1,255,957.50 |
| Construction Cost (Annualized) | Included |
| Operational Cost | Included |
| Transportation Cost | Included |
| Remaining Budget | $744,042.50 |

---

### Selected Warehouses

| Warehouse | Selected |
|---------|----------|
| WH_SOUTH | Yes |
| WH_WEST | Yes |
| WH_NORTH | No |
| WH_EAST | No |

---

### Distribution Plan (Annual Units)

| Warehouse | Facility | Units Shipped |
|---------|----------|---------------|
| WH_SOUTH | MEDICAL_CENTER | 32,850 |
| WH_SOUTH | ENGINEERING_BLOCK | 14,600 |
| WH_SOUTH | SCIENCE_BLOCK | 16,425 |
| WH_SOUTH | BOYS_HOSTEL | 21,900 |
| WH_SOUTH | GIRLS_HOSTEL | 20,075 |
| WH_SOUTH | FOOD_COURT | 18,250 |
| WH_SOUTH | SPORTS_COMPLEX | 12,775 |
| WH_WEST | CENTRAL_LIBRARY | 9,125 |

---

## Technologies Used

| Technology | Purpose |
|-----------|--------|
| Python | Programming and modeling |
| PuLP | MILP optimization |
| Pandas | Data processing and validation |
| CBC Solver | Optimization engine |

---

## Conclusion
The MILP-based optimization model successfully identifies the most cost-effective and reliable emergency supply distribution strategy for the campus. The selected warehouses minimize total annual cost while satisfying all facility demands and capacity constraints. The model demonstrates strong scalability and can be extended to incorporate additional facilities, budget scenarios, or sustainability constraints, making it suitable for real-world campus logistics planning.
