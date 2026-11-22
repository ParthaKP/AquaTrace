import json
import pytest
from core.c_backend import DirectedGraph,bfs,dfs_iterative,dfs_recursive,analyze_downstream_impact,calculate_risk_score,classify_risk,PriorityQueue
from reports.report_manager import ReportManager
from core.maintenance_engine import MaintenanceEngine

def graph_fixture():
    g=DirectedGraph()
    for node,pop in (("A",2000),("B",3000),("C",4000),("D",5000),("Z",100)):
        g.add_vertex(node,population_served=pop,infrastructure_importance=70)
    g.add_edge("A","B"); g.add_edge("A","C"); g.add_edge("B","D"); g.add_edge("C","D"); g.add_edge("D","A")
    return g

def test_graph_update_and_cycles():
    g=graph_fixture(); assert g.get_vertex_count()==5 and g.get_edge_count()==5
    with pytest.raises(ValueError): g.add_vertex("A")
    with pytest.raises(ValueError): g.add_edge("A","missing")
    assert g.remove_vertex("B") and not g.has_edge("A","B")
    assert g.get_edge_count()==3 and not g.remove_edge("A","B")
    empty=DirectedGraph(); assert empty.display_graph()=="(empty graph)"

def test_traversals_and_invalid_start():
    g=graph_fixture(); assert bfs(g,"A")==["A","B","C","D"]
    assert dfs_recursive(g,"A")==dfs_iterative(g,"A")
    assert bfs(g,"A",1)==["A","B","C"]
    assert bfs(g,"Z")==["Z"]
    with pytest.raises(ValueError): dfs_iterative(g,"X")

def test_impact_deduplicates_converging_cycle():
    result=analyze_downstream_impact(graph_fixture(),"A")
    assert result["total_affected_locations"]==3
    assert {x["junction_id"] for x in result["affected_locations"]}=={"B","C","D"}
    assert analyze_downstream_impact(graph_fixture(),"Z")["total_affected_locations"]==0

def test_risk_values_and_classification():
    f={"severity":90,"impact":80,"rainfall":70,"population":60,"infrastructure":50,"confidence":40}
    assert calculate_risk_score(f)["risk_score"]==71.0
    assert [classify_risk(x) for x in (90,70,50,20)]==["CRITICAL","HIGH","MEDIUM","LOW"]
    with pytest.raises(ValueError): calculate_risk_score({**f,"severity":101})
    with pytest.raises(ValueError): calculate_risk_score({k:v for k,v in f.items() if k!="impact"})
    with pytest.raises(ValueError): calculate_risk_score(f,{"severity":.2})

def test_priority_heap_ties_and_scale():
    q=PriorityQueue(); assert q.extract_max() is None
    q.insert({"junction_id":"B","risk_score":90}); q.insert({"junction_id":"A","risk_score":90}); q.insert({"junction_id":"C","risk_score":40})
    assert q.peek()["junction_id"]=="A" and q.extract_max()["junction_id"]=="A"
    q.heapify([{"junction_id":str(i),"risk_score":float(i)} for i in range(300)])
    assert [q.extract_max()["risk_score"] for _ in range(300)]==list(map(float,range(299,-1,-1)))

def test_reports_persistence_and_engine(tmp_path):
    g=graph_fixture(); path=tmp_path/"reports.json"; manager=ReportManager(path,g.has_vertex)
    manager.submit_report({"report_id":1,"junction_id":"A","severity":90,"rainfall":80,"confidence":90,"status":"pending"})
    with pytest.raises(ValueError): manager.submit_report({"report_id":1,"junction_id":"A"})
    manager.update_report(1,{"severity":95}); assert ReportManager(path,g.has_vertex).get_report(1)["severity"]==95
    schedule=MaintenanceEngine(g,manager).generate_maintenance_schedule(); assert schedule[0]["junction_id"]=="A"
    manager.verify_report(1); assert manager.get_pending_reports()[0]["status"]=="verified"
    assert manager.delete_report(1) and not manager.delete_report(1)
    with pytest.raises(ValueError): manager.submit_report({"report_id":2,"junction_id":"X"})
    with pytest.raises(ValueError): manager.submit_report({"report_id":2,"junction_id":"A","severity":101})
    path.write_text("{broken",encoding="utf-8")
    with pytest.raises(ValueError): ReportManager(path)

def test_sample_integration():
    from main import load_app
    graph,manager,engine=load_app()
    assert graph.get_vertex_count()>=20 and graph.get_edge_count()>=25
    schedule=engine.generate_maintenance_schedule()
    assert schedule and schedule[0]["risk_score"]>=schedule[-1]["risk_score"]
    assert {x["priority"] for x in schedule} >= {"CRITICAL","HIGH","MEDIUM","LOW"}
