"""Measure graph/heap operations; values are measured at runtime, never preset."""
import random,time,tracemalloc
from core.c_backend import DirectedGraph,bfs,dfs_iterative,analyze_downstream_impact,PriorityQueue

def synthetic_graph(size,seed=7):
    rng=random.Random(seed); g=DirectedGraph()
    for i in range(size): g.add_vertex(f"N{i:05d}",population_served=rng.randrange(10000),infrastructure_importance=rng.randrange(101))
    for i in range(size-1): g.add_edge(f"N{i:05d}",f"N{i+1:05d}")
    for _ in range(size):
        a=rng.randrange(size); b=rng.randrange(size)
        if a!=b and not g.has_edge(f"N{a:05d}",f"N{b:05d}"): g.add_edge(f"N{a:05d}",f"N{b:05d}")
    return g
def run_benchmarks():
    print("nodes | build(s) | BFS(s) | DFS(s) | impact(s) | heap insert(s) | extract(s) | peak MiB")
    for n in (100,500,1000,5000,10000):
        tracemalloc.start(); t=time.perf_counter(); g=synthetic_graph(n); build=time.perf_counter()-t
        start="N00000"; t=time.perf_counter(); bfs(g,start); bt=time.perf_counter()-t
        t=time.perf_counter(); dfs_iterative(g,start); dt=time.perf_counter()-t
        t=time.perf_counter(); analyze_downstream_impact(g,start); it=time.perf_counter()-t
        q=PriorityQueue(); t=time.perf_counter()
        for i in range(n): q.insert({"junction_id":f"N{i:05d}","risk_score":float(i%101)})
        ins=time.perf_counter()-t; t=time.perf_counter()
        while not q.is_empty(): q.extract_max()
        ext=time.perf_counter()-t; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
        print(f"{n:5} | {build:8.4f} | {bt:6.4f} | {dt:6.4f} | {it:9.4f} | {ins:14.4f} | {ext:10.4f} | {peak/1048576:8.2f}")
    from main import load_app
    _, reports, engine = load_app()
    items = reports.get_pending_reports()
    fifo = [r["junction_id"] for r in items]
    severity = [r["junction_id"] for r in sorted(items,key=lambda r:(-r.get("severity",0),r["junction_id"]))]
    aquatrace = [r["junction_id"] for r in engine.generate_maintenance_schedule()]
    print("\nPrioritization strategies (same bundled simulated report set):")
    print("FIFO:          " + " -> ".join(fifo))
    print("Severity-based:" + " -> ".join(severity))
    print("AquaTrace:     " + " -> ".join(aquatrace))
if __name__=="__main__": run_benchmarks()
