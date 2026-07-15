# Explainable Shelter Allocation and Overcrowding Prevention

The Explainable Shelter Allocation algorithm in X-DMRA dynamically evaluates available emergency shelters to optimize placements for displaced persons. It balances geographical proximity, specialized support facilities, and strict capacity limits to prevent dangerous overcrowding.

## Evaluation Criteria (100 Point Scale)

The algorithm calculates a composite score for each eligible shelter based on seven distinct criteria:

### 1. Capacity Suitability (30 points)
*   **Metric:** Proportion of the requested displaced population that the shelter can accommodate.
*   **Logic:** $Score = (\frac{\text{Proposed Allocation}}{\text{Total Requested People}}) \times 30$
*   **Explanation:** Shelters that can house the entire requested population in a single location receive the maximum score, minimizing family separation and logistical overhead.

### 2. Medical & Vulnerability Support (20 points)
*   **Metric:** Presence of critical facilities for vulnerable populations.
*   **Logic:**
    *   Medical Support present: +10 points
    *   Accessibility Support present: +5 points
    *   Women & Child Safe Area present: +5 points
*   **Explanation:** Prioritizes shelters that can safely host injured people, pregnant women, children, and those requiring medical observation.

### 3. Utilities & Provisions (15 points)
*   **Metric:** Availability of sustaining resources.
*   **Logic:**
    *   Food and Drinking Water present: +7.5 points
    *   Sanitation facilities present: +5 points
    *   Power Backup present: +2.5 points
*   **Explanation:** Ensures fundamental human needs are met at the recommended location.

### 4. Distance Suitability (15 points)
*   **Metric:** Haversine distance between the incident and the shelter.
*   **Logic:**
    *   Distance $\le$ 10km: 15 points
    *   Distance > 10km and $\le$ 50km: 10.5 points (70%)
    *   Distance > 50km: 4.5 points (30%)
*   **Explanation:** Minimizes transit time and logistical strain on transport vehicles.

### 5. Overcrowding Risk Prevention (10 points)
*   **Metric:** Projected occupancy percentage (Occupied + Reserved + Proposed) / Total Capacity.
*   **Logic:**
    *   Projected < 70% (Low Risk): 10 points
    *   Projected 70-84% (Moderate Risk): 8 points
    *   Projected 85-94% (High Risk): 3 points
    *   Projected $\ge$ 95% (Critical Risk): 0 points
*   **Explanation:** Actively discourages routing people to shelters that are nearing maximum capacity, distributing the load across the network.

### 6. Route Safety Constraints (5 points)
*   **Metric:** The risk level of the route between the incident and the shelter.
*   **Logic:**
    *   Low Risk: 5 points
    *   Medium Risk: 2.5 points
    *   High Risk: 1 point
    *   Blocked: Automatic Disqualification
*   **Explanation:** Prevents dispatching displaced persons over dangerous or flooded roads.

### 7. Intake Workload Management (5 points)
*   **Metric:** The ratio of current intake workload to maximum daily intake capacity.
*   **Logic:**
    *   Workload Ratio $\le$ 0.5: 5 points
    *   Workload Ratio > 0.5 and $\le$ 0.8: 2.5 points
    *   Workload Ratio > 0.8: 1 point
*   **Explanation:** Prevents overwhelming shelter staff and registration desks, ensuring orderly admissions.

## Single vs. Split Allocation

1.  **Single Source Evaluation:** The system first attempts to find a single shelter capable of safely accommodating the entire group.
2.  **Split Allocation Fallback:** If no single shelter has sufficient capacity (due to size limits or overcrowding thresholds), the algorithm automatically calculates a split allocation plan. It iterates through the highest-scoring shelters, reserving available blocks of capacity until the total requested population is covered.

## Hard Constraints (Disqualifiers)
A shelter is entirely excluded from the evaluation pool if:
*   Its operating status is `closed` or `unavailable`.
*   Its available capacity (Total - Occupied - Reserved) is 0 or less.
*   The route from the incident to the shelter is marked as `blocked`.
*   The request specifies mandatory accessibility, and the shelter lacks it.
*   The request specifies mandatory medical observation, and the shelter lacks medical support.

## Lifecycles & Workflows

### Capacity Reservation Lifecycle
1.  **Generation:** An officer generates shelter recommendations for a specific incident and population.
2.  **Approval:** The officer reviews the explanations (including overcrowding risk) and explicitly approves a reservation.
3.  **Reservation:** The approved capacity is added to the shelter's `reserved_capacity`, instantly updating its `available_spaces` to prevent double-booking.

### Admission and Cancellation Lifecycle
*   **In Transit:** Reservations can be marked as `in_transit` while displaced persons are moving.
*   **Admitted (Completion):** Upon arrival, the reservation is marked `admitted`. The `reserved_capacity` decreases, and `occupied_capacity` increases.
*   **Cancelled:** If a reservation is aborted before admission, the `reserved_capacity` is immediately released back to the general pool.

### Shelter Reallocation
If an approved shelter suddenly becomes unavailable (e.g., closed due to damage, or the route becomes blocked):
1.  The system evaluates a reallocation.
2.  The currently assigned (but now unsuitable) shelter is explicitly excluded.
3.  Replacement shelters are ranked using the same criteria.
4.  Upon officer approval of the replacement, the old reservation is cancelled (releasing its reserved capacity), and a new reservation is created atomically.

## Technical Limitations & Disclaimers

*   **Straight-Line-Distance Limitation:** Distance calculations currently use the Haversine formula (straight-line distance) rather than true road-network routing distance.
*   **Demonstration-Data Disclaimer:** The provided seed data (Coimbatore shelters) is entirely synthetic and for demonstration purposes only. It does not reflect real government infrastructure.
*   **Development SQLite Migration Limitation:** The database migration script (`backend/app/seed.py` / `migrate.py`) destructively drops and recreates SQLite tables. This is strictly for development environments and will cause data loss if used in production.
