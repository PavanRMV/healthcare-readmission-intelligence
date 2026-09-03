import argparse,json
from pathlib import Path
import pandas as pd
from .ingest import fetch_cms,fetch_places
from .clean import clean_hospitals,clean_readmissions,clean_hcahps,clean_places
from .warehouse import build_warehouse
from .analytics import export_all
from .findings import generate
from .reporting import build_kpis

def run(root):
    root=Path(root); raw=root/"data/raw"; db=root/"data/warehouse/healthcare.db"; out=root/"outputs"
    cms,meta=fetch_cms(raw); places_raw,pmeta=fetch_places(raw); meta.append(pmeta)
    hospitals=clean_hospitals(cms["hospital_general"]); readm=clean_readmissions(cms["readmissions"]); hcahps=clean_hcahps(cms["hcahps"]); places=clean_places(places_raw)
    build_warehouse(db,hospitals,readm,hcahps,places,pd.DataFrame(meta)); counts=export_all(db,out)
    quality=build_kpis(db)
    summary={"database":str(db),"tables":counts,"hospital_count":len(hospitals),"readmission_rows":len(readm),"readmission_score_completeness_pct":round(100*readm.score.notna().mean(),2),"places_rows":len(places),"join_safe_matched_hospitals":quality["safe_county_matched_hospitals"],"join_unmatched_hospitals":quality["unmatched_county_hospitals"],"join_ambiguous_hospitals":quality["ambiguous_county_hospitals"],"join_coverage_pct":quality["county_join_coverage_pct"]}
    generate(db,root/"docs/findings.md",out/"findings.json")
    out.mkdir(parents=True,exist_ok=True); (out/"run_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8"); return summary

def main():
    p=argparse.ArgumentParser(); p.add_argument("--root",default=str(Path(__file__).resolve().parents[2])); args=p.parse_args(); print(json.dumps(run(args.root),indent=2))
if __name__=="__main__": main()
