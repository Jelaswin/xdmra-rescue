# Explainable Relief-Supply Allocation Algorithm

This document describes the mechanics of the Relief Allocation Engine used in Phase 6.

## 1. Eligibility Rules
A warehouse is **eligible** if and only if:
- `operating_status` is `active` or `limited` (excluding `closed` and `unavailable`).
- It holds at least one unit of a requested item type that has not already been reserved.
- There are no `blocked` route conditions between the warehouse and the incident.
- It has at least one delivery vehicle with `availability_status = available`.

## 2. Factor Weights
The system ranks eligible warehouses out of a maximum score of **100 points**, distributed as follows:

| Factor | Points | Evaluation Metric |
|--------|--------|-------------------|
| Stock Coverage | 35 | % of total demanded units that this warehouse can satisfy from available stock. |
| Item Coverage | 15 | % of requested item *types* (e.g., food vs. water) that the warehouse can supply. |
| Distance | 15 | Straight-line Haversine distance. (≤ 10km = full points, ≤ 50km = 70% points, > 50km = 30% points). |
| Vehicle Capacity | 15 | Ratio of available vehicle capacity vs. supplied units (Capped at 15 pts). |
| Route Safety | 10 | Penalizes `medium` (-50%) and `high` (-80%) risk routes. |
| Workload | 10 | Penalizes highly loaded warehouses based on `current_dispatch_workload / maximum_dispatch_capacity`. |

## 3. Split-Allocation Logic
If the top-ranked warehouse cannot fulfill 100% of the demand (Stock Coverage < 100%), the engine generates a **Split Allocation Plan**:
1. It selects the highest-ranking warehouse and assigns all its available stock to satisfy the demand.
2. It proceeds down the ranked list of warehouses.
3. For each subsequent warehouse, it draws available inventory to fulfill the *remaining* demand.
4. It halts when 100% of the demand is met, or all warehouses are exhausted.

## 4. Inventory Transaction Rules
Inventory movements are handled using database transactions to prevent race conditions or negative inventory.
- **Reservation Phase**: When an officer approves a dispatch, stock is moved from `available` to `reserved`. The total `quantity_reserved` cannot exceed `quantity_available`.
- **Failure handling**: If a reservation exceeds available stock, the transaction rolls back with an HTTP 400.
- **Dispatch**: When marked `dispatched`, stock remains in `reserved` physically but is logged as en-route.
- **Delivery**: When marked `delivered`, the stock is permanently deducted from `quantity_available` and `quantity_reserved`.
- **Cancellation**: Cancelling an approved dispatch releases the `reserved` amount back to availability.

## 5. Explainability
Every recommendation provides:
- A transparent `explanation` string summarising the total score.
- A list of `positive_reasons` (Pros).
- A list of `limitations` (Cons).
These fields are generated directly from the mathematical evaluation.
