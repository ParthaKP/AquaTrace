"""Terminal demonstration for AquaTrace (no web or GUI dependencies)."""
import json
from pathlib import Path
from core.c_backend import DirectedGraph,bfs,dfs_iterative,analyze_downstream_impact,calculate_risk_score
from core.maintenance_engine import MaintenanceEngine
from reports.report_manager import ReportManager

ROOT=Path(__file__).resolve().parent
def load_app():
    data=json.loads((ROOT/"data"/"drainage_network.json").read_text(encoding="utf-8")); graph=DirectedGraph.from_dict(data)
    reports=ReportManager(ROOT/"data"/"blockage_reports.json",graph.has_vertex)
    return graph,reports,MaintenanceEngine(graph,reports)
def save_network(graph):
    """Persist interactive graph edits while retaining the synthetic-data note."""
    payload={"data_note":"Contains synthetic demonstration data and any local terminal edits; verify before real-world use.",
             "junctions":graph.get_all_vertices(),
             "connections":[{"source":u,"destination":v,**meta} for u,v,meta in graph.get_all_edges()]}
    (ROOT/"data"/"drainage_network.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
def main():
    graph,reports,engine=load_app()
    while True:
        print("\n"+"="*40+"\nAQUATRACE\nUrban Drainage Risk Prioritization\n"+"="*40)
        print("1. Display Drainage Network\n2. Add Drainage Junction\n3. Add Drainage Connection\n4. Run BFS\n5. Run DFS\n6. Analyze Downstream Impact\n7. Submit Blockage Report\n8. View Blockage Reports\n9. Calculate Risk Score\n10. Generate Maintenance Schedule\n11. View Network Statistics\n12. Run Performance Analysis\n0. Exit")
        choice=input("Select: ").strip()
        try:
            if choice=="0": return
            if choice=="1": print(graph.display_graph())
            elif choice=="2":
                jid=input("Junction ID: ").strip(); graph.add_vertex(jid,population_served=float(input("Population served: ")),infrastructure_importance=float(input("Infrastructure importance (0-100): ")),blockage_severity=0,rainfall_intensity=0,report_confidence=0,blockage_status="clear"); save_network(graph); print(f"Added {jid}")
            elif choice=="3":
                a=input("Source: ").strip(); b=input("Destination: ").strip(); graph.add_edge(a,b,capacity_lps=float(input("Capacity (L/s, 0 if unknown): "))); save_network(graph); print("Connection added")
            elif choice in ("4","5","6"):
                start=input("Junction ID: ").strip()
                if choice=="4": print(" -> ".join(bfs(graph,start)))
                elif choice=="5": print(" -> ".join(dfs_iterative(graph,start)))
                else: print(json.dumps(analyze_downstream_impact(graph,start),indent=2))
            elif choice=="7":
                rid=int(input("Report ID: ")); jid=input("Junction ID: ").strip(); sev=float(input("Severity (0-100): ")); rain=float(input("Rainfall (0-100): ")); conf=float(input("Confidence (0-100): ")); desc=input("Description: ")
                print(reports.submit_report({"report_id":rid,"junction_id":jid,"severity":sev,"rainfall":rain,"confidence":conf,"status":"pending","description":desc}))
            elif choice=="8": print(json.dumps(reports.get_all_reports(),indent=2))
            elif choice=="9":
                factors={k:float(input(f"{k} (0-100): ")) for k in ("severity","impact","rainfall","population","infrastructure","confidence")}; print(json.dumps(calculate_risk_score(factors),indent=2))
            elif choice=="10":
                for item in engine.generate_maintenance_schedule(): print(f"Rank {item['rank']}: {item['junction_id']} | {item['risk_score']:.2f} | {item['priority']}\n  Potentially affected: {', '.join(x['junction_id'] for x in item['impact']['affected_locations']) or 'None'}\n  {item['explanation']}")
            elif choice=="11": print(json.dumps(engine.get_network_summary(),indent=2))
            elif choice=="12":
                from benchmarks.performance_analysis import run_benchmarks
                run_benchmarks()
            else: print("Choose a listed menu number.")
        except (ValueError,KeyError,OSError) as exc: print(f"Could not complete that action: {exc}")
if __name__=="__main__": main()
