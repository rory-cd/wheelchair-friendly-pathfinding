# Wheelchair-Friendly Pathfinding

A graph-based pathfinding system that finds optimal routes for wheelchair users navigating a real-world environment. Built for SIT215 Computational Intelligence at Deakin University.

## Overview

Standard navigation apps optimise for distance or travel time — neither of which reflects the effort required to navigate in a wheelchair. This project finds the least-effort path by accounting for:
 
- **Path distance**
- **Slope** (graded against Australian accessibility standards)
- **Elevation change**
- **Surface type** (made path, gravel, or nature strip)

A section of **Ocean Grove, VIC** has been mapped as an example of the algorithm in practice.

## Features
 
- **A\* Search** with a custom admissible and consistent heuristic
- **Dijkstra's Algorithm** implemented for performance comparison
- **Three heuristic modes:** Euclidean-only, Standard (Euclidean + elevation + slope), and Extended (+ beach proximity risk zone)
- **Two cost functions:** Standard and Extended (with surface penalties)
- **Admissibility & consistency checking** built into the evaluation suite

## Dependencies

- Python 3.x
- `tkinter` — GUI
- `shapely` — polygon-based risk zone detection
- `numpy`

## Usage

### algorithms.py
`algorithms.py` is designed as a library for the GUI, but can be run as a script on its own.
By default, it will search for a path from A to Z and print the results.
To check other paths, replace the selected nodes in line 801, then run again:
`set_problem('A', 'Z')`

### gui.py
1. Run the script.
2. Select algorithm options from the left panel.
3. Select a start node by clicking it.
4. Select an end node by clicking it.
5. The search will run, highlighting the best cost path with details in the left panel.
6. Click anywhere on the map (or another node) to clear the search, ready to try again.

## Algorithms & Approach
 
### Cost Function
 
Each edge cost is the sum of three components:
 
| Component | Description |
|---|---|
| **Distance** | Physical path length in metres |
| **Slope penalty** | Exponential function `e^(10x) - 1`, uphill weighted more heavily than downhill, paths exceeding 1:14 grade receive a large multiplier |
| **Elevation penalty** | Absolute elevation difference × 35 (uphill) or × 15 (downhill) |
 
The extended cost function adds a **surface penalty** (surface difficulty × 10), where 0 = made path, 1 = gravel, 2 = nature strip.
 
### Heuristic
 
The standard heuristic is composed of:
- **Euclidean distance** to goal (via the Haversine formula, converting coordinates to metres)
- **Estimated slope penalty** (dampened by 0.15 to preserve admissibility)
- **Elevation difference** to goal (same multipliers as cost function)
The extended heuristic adds a **beach proximity penalty** using a Shapely polygon risk zone. The penalty scales exponentially with distance from the goal (`e^(0.05x) - 1`, capped at 20) to avoid inadmissibility near the goal.

## Test Results (Using Provided Example Environment)
 
| Algorithm | Avg. Efficiency | Always Optimal | Notes |
|---|---|---|---|
| A\* — Standard Heuristic | ~67% | ✅ | Best balance of speed and efficiency |
| A\* — Extended Heuristic | ~68% | ⚠️ | Marginally more efficient, inadmissible on some paths, slower |
| A\* — Euclidean Only | ~52% | ✅ | Useful baseline |
| Dijkstra's Algorithm | ~39% | ✅ | Consistently worst efficiency and runtime |
 
> *Efficiency = `len(path) / len(explored) × 100`*
 
A\* with the **standard heuristic** was selected as the best overall performer — highest efficiency, fastest runtimes, and consistent admissibility across all test cases.

## Example Environment
 
The map covers a section of Ocean Grove, VIC, chosen for its combination of steep slopes, gravel paths, and proximity to beach access points — a challenging real-world environment for wheelchair navigation.
 
**Data sources:**
- Path distances: [Google MyMaps](https://www.google.com/maps/about/mymaps/)
- Node elevations: [randymajors.org Elevation Tool](https://www.randymajors.org/elevation-on-google-maps)
- Slope grading standards: AS 1428.1 (via [Gilani Mobility](https://gilanimobility.com.au/blog/calculate-ramp-gradient-in-australia/))

**Slope classification:**
- 🟢 Comfortable — gradient ≤ 1:20
- 🟠 Uncomfortable — gradient between 1:20 and 1:14
- 🔴 Steep — gradient > 1:14