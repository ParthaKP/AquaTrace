"""Connect graph impact, risk scoring, report management, and heap ranking."""
from core.c_backend import analyze_downstream_impact,calculate_risk_score,PriorityQueue

class MaintenanceEngine:
    def __init__(self,graph,report_manager): self.graph=graph; self.report_manager=report_manager
    def analyze_report(self,report):
        node=self.graph.get_vertex(report["junction_id"])
        if node is None: raise ValueError(f"Report references unknown junction {report['junction_id']}")
        impact=analyze_downstream_impact(self.graph,report["junction_id"])
        pop=float(node.get("population_served") or 0); pop_score=min(100,pop/100)
        factors={"severity":report.get("severity",node.get("blockage_severity")),"impact":impact["impact_score"],"rainfall":report.get("rainfall",node.get("rainfall_intensity")),"population":pop_score,"infrastructure":node.get("infrastructure_importance"),"confidence":report.get("confidence",node.get("report_confidence"))}
        scored=calculate_risk_score(factors)
        return {"report_id":report["report_id"],"junction_id":report["junction_id"],**scored,"impact":impact,"factors":factors,"explanation":self._explain(factors,impact)}
    @staticmethod
    def _explain(factors,impact):
        reasons=[]
        for name,label in (("severity","Reported blockage severity"),("rainfall","Rainfall conditions"),("infrastructure","Infrastructure importance"),("confidence","Report confidence")):
            if factors.get(name) is not None and factors[name]>=70: reasons.append(f"High {label.lower()}.")
        reasons.append(f"{impact['total_affected_locations']} potentially affected downstream location(s); connectivity does not establish flooding.")
        return " ".join(reasons)
    def generate_maintenance_schedule(self):
        heap=PriorityQueue()
        for report in self.report_manager.get_pending_reports(): heap.insert(self.analyze_report(report))
        result=[]
        while not heap.is_empty(): result.append(heap.extract_max())
        for i,item in enumerate(result,1): item["rank"]=i
        return result
    def get_highest_priority_location(self):
        schedule=self.generate_maintenance_schedule(); return schedule[0] if schedule else None
    def get_critical_locations(self): return [x for x in self.generate_maintenance_schedule() if x["priority"]=="CRITICAL"]
    def get_network_summary(self): return {"junction_count":self.graph.get_vertex_count(),"connection_count":self.graph.get_edge_count(),"report_count":len(self.report_manager.get_all_reports()),"pending_or_verified_count":len(self.report_manager.get_pending_reports())}
