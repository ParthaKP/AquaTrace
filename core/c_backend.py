
"""Application bridge to the C-only DSA implementation in algorithms/."""

import ctypes
import hashlib
import os
import shutil
import subprocess
import tempfile

from pathlib import Path


# --------------------------------------------------
# Configuration and Constants
# --------------------------------------------------

_ALGORITHM_DIR = Path(__file__).resolve().parent.parent / "algorithms"

_SOURCES = sorted(
    path for path in _ALGORITHM_DIR.glob("*.c") if path.name != "demo.c"
)
_HEADER = _ALGORITHM_DIR / "aquatrace_algorithms.h"

_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


# --------------------------------------------------
# Load and Configure C Library
# --------------------------------------------------

def _load_library():

    compiler = shutil.which("gcc") or shutil.which("clang")

    if not compiler:
        raise RuntimeError(
            "AquaTrace DSA is implemented in C and requires GCC or Clang on PATH."
        )

    # Generate a unique hash based on source files
    digest_source = (
        _HEADER.read_bytes()
        + b"".join(
            path.name.encode() + path.read_bytes()
            for path in _SOURCES
        )
    )

    digest = hashlib.sha256(digest_source).hexdigest()[:16]

    ext = (
        ".dll" if os.name == "nt"
        else ".dylib" if os.uname().sysname == "Darwin"
        else ".so"
    )

    output = Path(tempfile.gettempdir()) / f"aquatrace_{digest}{ext}"

    # Compile C source files into a shared library
    if not output.exists():

        command = [compiler, "-O2", "-shared"]

        if os.name != "nt":
            command.append("-fPIC")

        command += [
            str(path) for path in _SOURCES
        ] + ["-o", str(output), "-lm"]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode:
            raise RuntimeError(
                "Could not build AquaTrace C DSA library:\n"
                + result.stderr.strip()
            )

    # Load the compiled shared library
    lib = ctypes.CDLL(str(output))

    ip = ctypes.POINTER(ctypes.c_int)
    dp = ctypes.POINTER(ctypes.c_double)

    # Configure graph functions
    lib.aqt_graph_create.restype = ctypes.c_void_p

    lib.aqt_graph_destroy.argtypes = [ctypes.c_void_p]

    lib.aqt_graph_add_vertex.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_add_vertex.restype = ctypes.c_int

    lib.aqt_graph_remove_vertex.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_remove_vertex.restype = ctypes.c_int

    lib.aqt_graph_has_vertex.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_has_vertex.restype = ctypes.c_int

    lib.aqt_graph_add_edge.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_add_edge.restype = ctypes.c_int

    lib.aqt_graph_remove_edge.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_remove_edge.restype = ctypes.c_int

    lib.aqt_graph_has_edge.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_has_edge.restype = ctypes.c_int

    lib.aqt_graph_vertex_count.argtypes = [ctypes.c_void_p]
    lib.aqt_graph_vertex_count.restype = ctypes.c_size_t

    lib.aqt_graph_edge_count.argtypes = [ctypes.c_void_p]
    lib.aqt_graph_edge_count.restype = ctypes.c_size_t

    lib.aqt_graph_vertex_id.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t
    ]
    lib.aqt_graph_vertex_id.restype = ctypes.c_char_p

    lib.aqt_graph_neighbor_count.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p
    ]
    lib.aqt_graph_neighbor_count.restype = ctypes.c_size_t

    lib.aqt_graph_neighbor_id.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_size_t
    ]
    lib.aqt_graph_neighbor_id.restype = ctypes.c_char_p

    # Configure traversal function
    lib.aqt_traverse.argtypes = [
        ctypes.c_size_t,
        ip,
        ip,
        ctypes.c_size_t,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ip,
        ip,
        ip
    ]
    lib.aqt_traverse.restype = ctypes.c_int

    # Configure impact score function
    lib.aqt_impact_score.argtypes = [
        ctypes.c_size_t,
        dp,
        dp,
        dp,
        dp,
        dp,
        dp,
        ip
    ]
    lib.aqt_impact_score.restype = ctypes.c_double

    # Configure risk score function
    lib.aqt_risk_score.argtypes = [
        dp,
        dp,
        ctypes.c_size_t,
        dp,
        dp,
        ip
    ]
    lib.aqt_risk_score.restype = ctypes.c_int

    # Configure persistent heap functions
    lib.aqt_heap_create.restype = ctypes.c_void_p

    lib.aqt_heap_destroy.argtypes = [ctypes.c_void_p]

    lib.aqt_heap_push.argtypes = [
        ctypes.c_void_p,
        ctypes.c_double,
        ctypes.c_char_p,
        ctypes.c_size_t
    ]
    lib.aqt_heap_push.restype = ctypes.c_int

    lib.aqt_heap_pop.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.aqt_heap_pop.restype = ctypes.c_int

    lib.aqt_heap_peek.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.aqt_heap_peek.restype = ctypes.c_int

    lib.aqt_heap_size.argtypes = [ctypes.c_void_p]
    lib.aqt_heap_size.restype = ctypes.c_size_t

    lib.aqt_heap_push.argtypes = [
        ctypes.c_void_p,
        ctypes.c_double,
        ctypes.c_char_p,
        ctypes.c_size_t
    ]
    lib.aqt_heap_push.restype = ctypes.c_int

    return lib


# Store the loaded library
_LIB = None


def library():

    global _LIB

    if _LIB is None:
        _LIB = _load_library()

    return _LIB


# Convert Python values into bytes
def _bytes(value):
    return str(value).encode("utf-8")


# --------------------------------------------------
# Directed Graph
# --------------------------------------------------

class DirectedGraph:
    """Python-facing attributes over C-owned adjacency-list graph storage."""

    def __init__(self):

        self._lib = library()
        self._handle = self._lib.aqt_graph_create()

        self.vertices = {}
        self.edge_metadata = {}

        if not self._handle:
            raise MemoryError("Could not allocate C graph")

    # Add a vertex
    def add_vertex(self, junction_id, **attributes):

        if not isinstance(junction_id, str) or not junction_id.strip():
            raise ValueError("junction_id must be a non-empty string")

        junction_id = junction_id.strip()

        if not self._lib.aqt_graph_add_vertex(
            self._handle,
            _bytes(junction_id)
        ):
            raise ValueError(
                f"Vertex {junction_id} already exists or could not be allocated"
            )

        self.vertices[junction_id] = {
            "junction_id": junction_id,
            **attributes
        }

        return self.vertices[junction_id]

    # Remove a vertex
    def remove_vertex(self, junction_id):

        if not self._lib.aqt_graph_remove_vertex(
            self._handle,
            _bytes(junction_id)
        ):
            return False

        self.vertices.pop(junction_id, None)

        self.edge_metadata = {
            e: m
            for e, m in self.edge_metadata.items()
            if junction_id not in e
        }

        return True

    # Add a directed edge
    def add_edge(self, source, destination, **metadata):

        if not self.has_vertex(source) or not self.has_vertex(destination):
            raise ValueError("Both edge endpoints must exist")

        if source == destination:
            raise ValueError("Self-loops are not supported")

        if self.has_edge(source, destination):
            raise ValueError(
                f"Edge {source}->{destination} already exists"
            )

        if not self._lib.aqt_graph_add_edge(
            self._handle,
            _bytes(source),
            _bytes(destination)
        ):
            raise MemoryError("Could not allocate C graph edge")

        self.edge_metadata[(source, destination)] = dict(metadata)

    # Remove a directed edge
    def remove_edge(self, source, destination):

        removed = bool(
            self._lib.aqt_graph_remove_edge(
                self._handle,
                _bytes(source),
                _bytes(destination)
            )
        )

        if removed:
            self.edge_metadata.pop((source, destination), None)

        return removed

    # Get neighboring vertices
    def get_neighbors(self, junction_id):

        count = self._lib.aqt_graph_neighbor_count(
            self._handle,
            _bytes(junction_id)
        )

        return [
            self._lib.aqt_graph_neighbor_id(
                self._handle,
                _bytes(junction_id),
                i
            ).decode("utf-8")
            for i in range(count)
        ]

    # Get a particular vertex
    def get_vertex(self, junction_id):
        return self.vertices.get(junction_id)

    # Get all vertices
    def get_all_vertices(self):

        return [
            self.vertices[
                self._lib.aqt_graph_vertex_id(
                    self._handle,
                    i
                ).decode("utf-8")
            ]
            for i in range(self.get_vertex_count())
        ]

    # Get all edges with their metadata
    def get_all_edges(self):

        return [
            (u, v, dict(self.edge_metadata.get((u, v), {})))
            for u in self.vertices
            for v in self.get_neighbors(u)
        ]

    # Search for a vertex
    def search_vertex(self, junction_id):
        return self.get_vertex(junction_id)

    # Check whether a vertex exists
    def has_vertex(self, junction_id):

        return bool(
            self._lib.aqt_graph_has_vertex(
                self._handle,
                _bytes(junction_id)
            )
        )

    # Check whether an edge exists
    def has_edge(self, source, destination):

        return bool(
            self._lib.aqt_graph_has_edge(
                self._handle,
                _bytes(source),
                _bytes(destination)
            )
        )

    # Display graph connections
    def display_graph(self):

        return "\n".join(
            f"{u}: {', '.join(vs) if vs else '(no downstream junctions)'}"
            for u in self.vertices
            for vs in [self.get_neighbors(u)]
        ) or "(empty graph)"

    # Get vertex count
    def get_vertex_count(self):
        return self._lib.aqt_graph_vertex_count(self._handle)

    # Get edge count
    def get_edge_count(self):
        return self._lib.aqt_graph_edge_count(self._handle)

    # Create a graph from dictionary data
    @classmethod
    def from_dict(cls, data):

        graph = cls()

        for vertex in data.get("junctions", []):

            graph.add_vertex(
                vertex["junction_id"],
                **{
                    k: v
                    for k, v in vertex.items()
                    if k != "junction_id"
                }
            )

        for edge in data.get("connections", []):

            graph.add_edge(
                edge["source"],
                edge["destination"],
                **{
                    k: v
                    for k, v in edge.items()
                    if k not in ("source", "destination")
                }
            )

        return graph

    # Release C graph memory
    def __del__(self):

        handle = getattr(self, "_handle", None)

        if handle:
            try:
                self._lib.aqt_graph_destroy(handle)
            except Exception:
                pass


# --------------------------------------------------
# Graph Traversal: BFS and DFS
# --------------------------------------------------

def _traversal(graph, start, depth_limit=None, mode=0):

    if not graph.has_vertex(start):
        raise ValueError(f"Unknown starting junction: {start}")

    nodes = list(graph.vertices)

    indexes = {
        node: i
        for i, node in enumerate(nodes)
    }

    edges = graph.get_all_edges()
    n = len(nodes)

    # Convert graph edges into C-compatible arrays
    src = (ctypes.c_int * len(edges))(
        *(indexes[u] for u, v, _ in edges)
    )

    dst = (ctypes.c_int * len(edges))(
        *(indexes[v] for u, v, _ in edges)
    )

    order = (ctypes.c_int * n)()
    distances = (ctypes.c_int * n)()

    used = ctypes.c_int()

    limit = -1 if depth_limit is None else depth_limit

    # Call the C traversal algorithm
    if not library().aqt_traverse(
        n,
        src,
        dst,
        len(edges),
        indexes[start],
        limit,
        mode,
        order,
        distances,
        ctypes.byref(used)
    ):
        raise ValueError("C traversal failed")

    return [
        (nodes[order[i]], distances[order[i]])
        for i in range(used.value)
    ]


# Breadth First Search
def bfs(graph, start, max_depth=None):

    if max_depth is not None and (
        isinstance(max_depth, bool)
        or not isinstance(max_depth, int)
        or max_depth < 0
    ):
        raise ValueError("max_depth must be a non-negative integer")

    return [
        node
        for node, _ in _traversal(graph, start, max_depth, 0)
    ]


# Get downstream nodes
def get_downstream_nodes(graph, start, max_depth=None):

    return [
        n
        for n in bfs(graph, start, max_depth)
        if n != start
    ]


# Get all reachable nodes
def get_reachable_nodes(graph, start, max_depth=None):
    return bfs(graph, start, max_depth)


# Recursive Depth First Search
def dfs_recursive(graph, start):

    return [
        node
        for node, _ in _traversal(graph, start, None, 1)
    ]


# Iterative Depth First Search
def dfs_iterative(graph, start):

    return [
        node
        for node, _ in _traversal(graph, start, None, 2)
    ]


# Get connected region
def get_connected_region(graph, start):
    return dfs_iterative(graph, start)


# --------------------------------------------------
# Downstream Impact Analysis
# --------------------------------------------------

def analyze_downstream_impact(graph, blocked_junction):

    reached = _traversal(graph, blocked_junction)

    affected = [
        (n, d)
        for n, d in reached
        if n != blocked_junction
    ]

    pops = []
    infra = []
    details = []

    # Collect population and infrastructure information
    for node, distance in affected:

        attrs = graph.get_vertex(node)

        pop = float(attrs.get("population_served") or 0)

        importance = float(
            attrs.get("infrastructure_importance") or 0
        )

        pops.append(pop)
        infra.append(importance)

        details.append({
            "junction_id": node,
            "distance": distance,
            "population_served": pop,
            "infrastructure_importance": importance
        })

    # Prepare data for the C impact scoring function
    n = len(pops)

    p = (ctypes.c_double * n)(*pops)
    i = (ctypes.c_double * n)(*infra)

    ps = ctypes.c_double()
    mi = ctypes.c_double()
    cs = ctypes.c_double()
    popscore = ctypes.c_double()

    impact_level = ctypes.c_int()

    # Calculate impact score using C implementation
    score = library().aqt_impact_score(
        n,
        p,
        i,
        ctypes.byref(ps),
        ctypes.byref(mi),
        ctypes.byref(cs),
        ctypes.byref(popscore),
        ctypes.byref(impact_level)
    )

    # Store impact metrics
    metrics = {
        "reachable_location_count": n,
        "population_served_sum": ps.value,
        "mean_infrastructure_importance": mi.value,
        "count_score": cs.value,
        "population_score": popscore.value,
        "capacity_note": (
            "Capacity metadata is retained for future hydraulic analysis; "
            "graph connectivity alone cannot estimate flow or flooding."
        )
    }

    level = ("LOW", "MEDIUM", "HIGH")[impact_level.value]

    return {
        "blocked_junction": blocked_junction,
        "affected_locations": details,
        "total_affected_locations": n,
        "impact_score": score,
        "impact_level": level,
        "contributing_factors": metrics
    }


# Get affected locations
def get_affected_locations(graph, junction):

    return [
        x["junction_id"]
        for x in analyze_downstream_impact(
            graph,
            junction
        )["affected_locations"]
    ]


# Calculate impact score
def calculate_impact_score(graph, junction):

    return analyze_downstream_impact(
        graph,
        junction
    )["impact_score"]


# Get complete impact details
def get_impact_details(graph, junction):
    return analyze_downstream_impact(graph, junction)


# --------------------------------------------------
# Risk Scoring
# --------------------------------------------------

# Default weights assigned to risk factors
DEFAULT_WEIGHTS = {
    "severity": .25,
    "impact": .25,
    "rainfall": .15,
    "population": .15,
    "infrastructure": .10,
    "confidence": .10
}


# Classify risk based on score
def classify_risk(score):

    _validate_range(score, "risk score")

    return _native_risk([float(score)], [1.0])[1]


# Validate that a value is between 0 and 100
def _validate_range(value, name):

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0 <= value <= 100
    ):
        raise ValueError(
            f"{name} must be a number from 0 to 100"
        )

    return float(value)


# Validate risk factor weights
def _validate_weights(weights):

    if (
        not isinstance(weights, dict)
        or not weights
        or any(
            isinstance(v, bool)
            or not isinstance(v, (int, float))
            or v < 0
            for v in weights.values()
        )
        or abs(sum(weights.values()) - 1) > 1e-9
    ):
        raise ValueError(
            "weights must be non-negative numbers that sum to 1"
        )

    return dict(weights)


# Calculate risk using the native C implementation
def _native_risk(values, weights):

    n = len(values)

    v = (ctypes.c_double * n)(*values)
    w = (ctypes.c_double * n)(*weights)

    parts = (ctypes.c_double * n)()

    score = ctypes.c_double()
    priority = ctypes.c_int()

    if not library().aqt_risk_score(
        v,
        w,
        n,
        parts,
        ctypes.byref(score),
        ctypes.byref(priority)
    ):
        raise ValueError("C risk scorer rejected input")

    return (
        score.value,
        _PRIORITIES[priority.value],
        list(parts)
    )


# Get individual risk factor contributions
def get_risk_breakdown(factors, weights=None):

    weights = _validate_weights(weights or DEFAULT_WEIGHTS)

    known = set(DEFAULT_WEIGHTS)

    if set(weights) - known:
        raise ValueError("Unknown risk factor in weights")

    missing = [
        k
        for k in weights
        if factors.get(k) is None
    ]

    if missing:
        raise ValueError(
            "Missing required risk measurements: "
            + ", ".join(missing)
        )

    values = [
        _validate_range(factors[k], k)
        for k in weights
    ]

    _, _, parts = _native_risk(
        values,
        list(weights.values())
    )

    return {
        k: {
            "value": v,
            "weight": weights[k],
            "contribution": part
        }
        for k, v, part in zip(weights, values, parts)
    }


# Calculate overall risk score and priority
def calculate_risk_score(factors, weights=None):

    weights = _validate_weights(weights or DEFAULT_WEIGHTS)

    breakdown = get_risk_breakdown(factors, weights)

    score, priority, _ = _native_risk(
        [x["value"] for x in breakdown.values()],
        [x["weight"] for x in breakdown.values()]
    )

    return {
        "risk_score": score,
        "priority": priority,
        "breakdown": breakdown,
        "interpretation": (
            "Inspection-priority heuristic; "
            "not a statistically calibrated probability of flooding."
        )
    }


# --------------------------------------------------
# Priority Queue
# --------------------------------------------------

class PriorityQueue:
    """C binary max heap with stable ascending-junction-ID tie breaking."""

    def __init__(self, items=None):

        self._lib = library()
        self._handle = self._lib.aqt_heap_create()

        self._items = []

        if not self._handle:
            raise MemoryError("Could not allocate C max heap")

        if items is not None:
            self.heapify(items)

    # Insert an item into the priority queue
    def insert(self, item):

        handle = len(self._items)

        if not self._lib.aqt_heap_push(
            self._handle,
            float(item["risk_score"]),
            str(item["junction_id"]).encode("utf-8"),
            handle
        ):
            raise MemoryError("C max heap insertion failed")

        self._items.append(item)

    # Build the heap from a collection of items
    def heapify(self, items):

        self._items = list(items)

        n = len(self._items)

        scores = (ctypes.c_double * n)(
            *(float(x["risk_score"]) for x in self._items)
        )

        ids = (ctypes.c_char_p * n)(
            *(str(x["junction_id"]).encode("utf-8") for x in self._items)
        )

        handles = (ctypes.c_size_t * n)(
            *range(n)
        )

        if not self._lib.aqt_heap_build(
            self._handle,
            scores,
            ids,
            handles,
            n
        ):
            raise ValueError("C heapify failed")

        return self

    # Remove and return the highest-priority item
    def extract_max(self):

        handle = ctypes.c_size_t()

        return (
            self._items[handle.value]
            if self._lib.aqt_heap_pop(
                self._handle,
                ctypes.byref(handle)
            )
            else None
        )

    # View the highest-priority item without removing it
    def peek(self):

        handle = ctypes.c_size_t()

        return (
            self._items[handle.value]
            if self._lib.aqt_heap_peek(
                self._handle,
                ctypes.byref(handle)
            )
            else None
        )

    # Check whether the priority queue is empty
    def is_empty(self):
        return self.get_size() == 0

    # Get the number of elements in the priority queue
    def get_size(self):
        return self._lib.aqt_heap_size(self._handle)

    # Display all heap elements in priority order
    def display_heap(self):

        items = []

        while not self.is_empty():
            items.append(self.extract_max())

        self.heapify(items)

        return items

    # Release C heap memory
    def __del__(self):

        handle = getattr(self, "_handle", None)

        if handle:
            try:
                self._lib.aqt_heap_destroy(handle)
            except Exception:
                pass
