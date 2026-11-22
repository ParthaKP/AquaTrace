"""JSON-backed blockage report CRUD with atomic replacement writes."""
import json, os, tempfile
from pathlib import Path
from utils.validators import validate_range

class ReportManager:
    STATUSES={"pending","verified","rejected","resolved"}
    def __init__(self,path,junction_exists=None): self.path=Path(path); self.junction_exists=junction_exists; self.reports=self._load()
    def _load(self):
        if not self.path.exists(): return {}
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
            records=data.get("reports",data) if isinstance(data,dict) else data
            return {str(r["report_id"]):r for r in records}
        except (json.JSONDecodeError,KeyError,TypeError) as exc: raise ValueError(f"Malformed report JSON in {self.path}: {exc}") from exc
    def _save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(dir=self.path.parent,text=True)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump({"reports":list(self.reports.values()),"data_note":"Synthetic/sample reports are simulated, not verified field measurements."},f,indent=2)
            os.replace(tmp,self.path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def submit_report(self,report=None,**kwargs):
        r=dict(report or kwargs); rid=r.get("report_id"); jid=r.get("junction_id")
        if rid is None or isinstance(rid,bool): raise ValueError("report_id is required")
        key=str(rid)
        if key in self.reports: raise ValueError(f"Report {rid} already exists")
        if not isinstance(jid,str) or not jid.strip(): raise ValueError("junction_id is required")
        if self.junction_exists and not self.junction_exists(jid): raise ValueError(f"Unknown junction: {jid}")
        for field in ("severity","rainfall","confidence"):
            if field in r: r[field]=validate_range(r[field],field)
        status=r.get("status","pending")
        if status not in self.STATUSES: raise ValueError(f"Invalid report status: {status}")
        r["status"]=status; r["report_id"]=rid; r["junction_id"]=jid
        self.reports[key]=r; self._save(); return dict(r)
    def get_report(self,report_id): return self.reports.get(str(report_id))
    def update_report(self,report_id,updates=None,**kwargs):
        key=str(report_id)
        if key not in self.reports: raise KeyError(f"Report {report_id} not found")
        candidate={**self.reports[key],**(updates or kwargs)}
        if "junction_id" in candidate and self.junction_exists and not self.junction_exists(candidate["junction_id"]): raise ValueError("Unknown junction")
        for f in ("severity","rainfall","confidence"):
            if f in candidate: candidate[f]=validate_range(candidate[f],f)
        if candidate.get("status") not in self.STATUSES: raise ValueError("Invalid report status")
        self.reports[key]=candidate; self._save(); return dict(candidate)
    def delete_report(self,report_id):
        if self.reports.pop(str(report_id),None) is None: return False
        self._save(); return True
    def get_all_reports(self): return [dict(r) for r in self.reports.values()]
    def verify_report(self,report_id): return self.update_report(report_id,{"status":"verified"})
    def get_pending_reports(self): return [dict(r) for r in self.reports.values() if r.get("status") in ("pending","verified")]
