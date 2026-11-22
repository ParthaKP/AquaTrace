# AquaTrace

**Understanding Drainage Networks. Tracing Risks. Protecting Cities.**

AquaTrace is an educational backend with its data structures and orchestration in Python and its core DSA algorithms implemented in C. It models assumed stormwater flow as a directed graph, traces downstream connectivity, combines reported and junction factors into a transparent inspection-priority score, and ranks reports with a hand-built binary max heap.

## Problem and approach

Drainage networks connect multiple junctions, so a reported blockage can warrant checking connected downstream locations. AquaTrace makes those relationships visible using an adjacency list, BFS/DFS, and an impact summary. The results say **potentially affected**: connectivity alone does not model rainfall-runoff, hydraulic capacity, terrain, or prove flooding.

## Features and DSA

- Directed adjacency-list graph storage and graph operations implemented in C; Python keeps the descriptive junction attributes.
- Manual BFS and recursive/iterative DFS implemented in C, with cycle protection.
- Downstream traversal and impact aggregation implemented in C with distance, population, infrastructure, and an explainable heuristic.
- Configurable 0 to 100 weighted risk scoring and classification implemented in C. It is an inspection heuristic, not a calibrated flood probability.
- Custom binary max heap implemented in C. Higher scores rank first; ties use ascending junction ID deterministically.
- No DSA implementation is provided in Python. `core/c_backend.py` is only the application bridge to the native C library.
- JSON report CRUD, validation, and atomic file replacement.
- Terminal menu and runtime performance measurements using `time` and `tracemalloc`.

## Technology

Python 3.10+, a C compiler (GCC or Clang), and the standard library. `pytest` is the only Python development dependency. No NetworkX or `heapq` is used in core operations. The shared library is built automatically on first use and cached in the operating system temporary directory.

## Structure

`algorithms/` contains only C files: `graph.c`, `traversal.c`, `impact_analysis.c`, `risk_scoring.c`, `priority_queue.c`, and their shared header. `core/c_backend.py` exposes those C operations to the Python maintenance engine without reimplementing them. `core/maintenance_engine.py` integrates reports and ranking; `reports/` handles JSON; `utils/` contains general validators; `data/` contains simulated examples; `tests/` contains unit and integration coverage; `benchmarks/` measures runtime and memory; `main.py` starts the terminal demo.

## Install and run

```bash
python -m pip install -r requirements.txt
python main.py
```

Ensure `gcc` or `clang` is available on `PATH`. On Windows, use a GCC/Clang distribution that supports producing shared libraries. The application builds the C library automatically when it starts. If no supported compiler is available, AquaTrace reports that requirement; it has no Python DSA fallback.

The bundled network and reports are explicitly synthetic demonstrations, not field-verified measurements. The menu can show the network, traverse it, inspect potential impacts, add and persist junctions/connections, submit persistent reports, calculate scores, and rank maintenance work.

## Example

```python
import json
from core.c_backend import DirectedGraph, analyze_downstream_impact

data = json.load(open("data/drainage_network.json", encoding="utf-8"))
graph = DirectedGraph.from_dict(data)
result = analyze_downstream_impact(graph, "J102")
print(result["impact_level"], result["total_affected_locations"])
```

## Tests and performance

### C DSA verification demo

Build and run the standalone C acceptance demo from the project root:

```powershell
gcc algorithms\graph.c algorithms\traversal.c algorithms\impact_analysis.c algorithms\risk_scoring.c algorithms\priority_queue.c algorithms\demo.c -o aquatrace_dsa_demo.exe -lm
.\aquatrace_dsa_demo.exe
```

It uses this sample directed network: `J1 -> J2`, `J1 -> J3`, `J2 -> J4`, `J3 -> J4`, `J4 -> J1`, with disconnected `J5`. It checks graph insert/remove validation, cycle-safe and depth-limited BFS, both DFS traversals, converging downstream paths, a weighted risk score, deterministic equal-score heap order, and graph counts. Its sample numeric inputs are populations `[2000, 4000, 1000]`, infrastructure `[80, 90, 30]`, risk factors `[90, 53, 80, 70, 90, 85]`, and risk weights `[0.25, 0.25, 0.15, 0.15, 0.10, 0.10]`. Edit those values and the graph edge arrays in `algorithms/demo.c` to demonstrate other cases. It prints `PASS` only when its checks match the expected results; a failed check exits with status 1.

Expected output:

```text
Graph: 5 junctions, 5 directed connections (J5 disconnected)
BFS from J1:       J1 -> J2 -> J3 -> J4
Recursive DFS:     J1 -> J2 -> J4 -> J3
Iterative DFS:     J1 -> J2 -> J4 -> J3
Potentially affected: J2, J3, J4 (3 unique downstream junctions)
Impact score:        53.00 (MEDIUM)
Risk score:          75.75 (HIGH)
Heap order:          J2 (75.75) -> J3 (75.75) -> J4 (53.00)
PASS: all C DSA checks matched their expected results.
```

For a live presentation, run `python main.py` and enter `4` then `J102` for BFS, `5` then `J102` for DFS, `6` then `J102` for downstream impact, `9` to enter six risk factors, or `10` to rank the sample reports. Those DSA calls run in the C library. Menu option `7` accepts a new report ID, junction ID, severity, rainfall, confidence, and description.

Run `python -m pytest -q`. The tests exercise the same C implementation used by the app. Run `python -m benchmarks.performance_analysis` to measure graph construction, traversal, impact, heap insertion/extraction, and peak traced memory for 100 through 10,000 nodes. Measurements depend on hardware and are produced by execution; no benchmark results are claimed in advance.

## Complexity

Graph traversals and downstream impact: O(V+E) time and O(V) auxiliary space in the native C routines. C graph storage: O(V+E). Native binary heap insertion/extraction: O(log n), peek: O(1), bottom-up heap construction: O(n).

## Limitations and research direction

Sample attributes and reports are simulated. Direction is assumed; the model has no elevations, pipe geometry, dynamic flow, rainfall forecasts, sensor validation, or calibration dataset. Missing risk inputs are reported as errors instead of silently becoming zero. Future research could integrate verified GIS/hydraulic data, uncertainty estimates, calibrated severity models, time-varying rainfall, and field validation while retaining the graph and ranking interfaces.
