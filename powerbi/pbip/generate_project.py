import json, os, shutil, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "Healthcare Readmission Intelligence.Report"
MODEL = ROOT / "Healthcare Readmission Intelligence.SemanticModel"
SCHEMA_VIS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json"


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n" if not isinstance(value, str) else value, encoding="utf-8")


def lit(value):
    return {"expr": {"Literal": {"Value": value}}}


def source(entity):
    return {"SourceRef": {"Entity": entity}}


def field(entity, prop, kind="Column"):
    return {kind: {"Expression": source(entity), "Property": prop}}


def projection(entity, prop, kind="Column", display=None):
    p = {"field": field(entity, prop, kind), "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if display: p["displayName"] = display
    return p


def title_objects(title):
    return {"title": [{"properties": {"show": lit("true"), "text": lit("'" + title.replace("'", "''") + "'"),
        "fontColor": {"solid": {"color": lit("'#16324F'")}}, "fontSize": lit("'12'"),
        "fontFamily": lit("'Segoe UI Semibold'")}}],
        "background": [{"properties": {"show": lit("true"), "transparency": lit("0D"),
        "color": {"solid": {"color": lit("'#FFFFFF'")}}}}],
        "border": [{"properties": {"show": lit("true"), "color": {"solid": {"color": lit("'#D7E3EC'")}}, "radius": lit("6D")}}]}


def visual(name, vtype, x, y, w, h, query_state=None, title=None, objects=None):
    v = {"visualType": vtype}
    if query_state:
        v["query"] = {"queryState": query_state}
    if objects: v["objects"] = objects
    if title: v["visualContainerObjects"] = title_objects(title)
    v["drillFilterOtherVisuals"] = True
    return {"$schema": SCHEMA_VIS, "name": name, "position": {"x": x, "y": y, "z": 1000, "height": h, "width": w}, "visual": v}


def textbox(name, text, x, y, w, h, size="22pt", color="#16324F", bold=True):
    style={"fontSize": size, "color": color}
    if bold: style["fontWeight"]="bold"
    return visual(name,"textbox",x,y,w,h,objects={"general":[{"properties":{"paragraphs":[{"textRuns":[{"value":text,"textStyle":style}]}]}}]})


def card(name, entity, measure, title, x, y, w=230, h=105):
    qs={"Values":{"projections":[projection(entity,measure,"Measure")]}}
    obj={"labels":[{"properties":{"fontSize":lit("'24'"),"color":{"solid":{"color":lit("'#0B6E99'")}}}}],
         "categoryLabels":[{"properties":{"show":lit("false")}}]}
    return visual(name,"card",x,y,w,h,qs,title,obj)


def table(name, columns, title, x, y, w, h):
    qs={"Values":{"projections":[projection(*c) for c in columns]}}
    return visual(name,"tableEx",x,y,w,h,qs,title)


def bar(name, category, measure, title, x, y, w, h):
    qs={"Category":{"projections":[projection(*category)]},"Y":{"projections":[projection(*measure)]}}
    return visual(name,"barChart",x,y,w,h,qs,title)


def slicer(name, entity, prop, title, x, y, w, h):
    qs={"Values":{"projections":[projection(entity,prop,"Column")]}}
    objects={"selection":[{"properties":{"singleSelect":lit("true"),"selectAllCheckboxEnabled":lit("false")}}]}
    return visual(name,"slicer",x,y,w,h,qs,title,objects)

# clean only generated project artifacts, preserving this generator
for p in [REPORT, MODEL]:
    if p.exists(): shutil.rmtree(p)

write(ROOT / "Healthcare Readmission Intelligence.pbip", {
 "$schema":"https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json","version":"1.0",
 "artifacts":[{"report":{"path":"Healthcare Readmission Intelligence.Report"}}],"settings":{"enableAutoRecovery":True}})
write(REPORT / "definition.pbir", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json","version":"4.0","datasetReference":{"byPath":{"path":"../Healthcare Readmission Intelligence.SemanticModel"}}})
write(REPORT / "definition/version.json", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json","version":"2.0.0"})
write(REPORT / "definition/report.json", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
 "themeCollection":{"baseTheme":{"name":"CY20SU09","reportVersionAtImport":{"visual":"1.8.52","report":"2.0.52","page":"1.3.52"},"type":"SharedResources"}},
 "resourcePackages":[{"name":"SharedResources","type":"SharedResources","items":[{"name":"CY20SU09","path":"BaseThemes/CY20SU09.json","type":"BaseTheme"}]}],
 "settings":{"useStylableVisualContainerHeader":True,"exportDataMode":"AllowSummarized","defaultDrillFilterOtherVisuals":True,"allowChangeFilterTypes":True,"useEnhancedTooltips":True},
 "slowDataSourceSettings":{"isCrossHighlightingDisabled":False,"isSlicerSelectionsButtonEnabled":False,"isFilterSelectionsButtonEnabled":False,"isFieldWellButtonEnabled":False,"isApplyAllButtonEnabled":False}})
write(REPORT / ".platform", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json","metadata":{"type":"Report","displayName":"Healthcare Readmission Intelligence"},"config":{"version":"2.0","logicalId":"6de2d25b-3629-4fb4-93f1-421b08ec4704"}})
write(MODEL / ".platform", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json","metadata":{"type":"SemanticModel","displayName":"Healthcare Readmission Intelligence"},"config":{"version":"2.0","logicalId":"2be63fa7-08c0-43b0-a857-ef0241b4bf51"}})
theme_src=ROOT/"assets/CY20SU09.json"
theme_dst=REPORT/"StaticResources/SharedResources/BaseThemes/CY20SU09.json"
theme_dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(theme_src,theme_dst)

pages={
 "ExecutiveOverview": [
  textbox("title_exec","Healthcare Readmission Intelligence",35,15,1210,54),
  textbox("sub_exec","Executive Overview  •  CMS hospital performance with county health context",35,68,1210,36,"11pt","#52677B",False),
  card("kpi_hosp","Metrics","Hospitals","Hospitals",35,110),
  card("kpi_readm","Metrics","Available Readmission Rows","Available readmission scores",285,110),
  card("kpi_rate","Metrics","HF Readmission Rate","HF 30-day readmission rate",535,110),
  card("kpi_hcahps","Metrics","Nurse Communication Always %","Nurse communication — Always",785,110),
  card("kpi_complete","Metrics","Readmission Completeness %","Readmission completeness",1035,110,210,105),
  bar("state_hf",("dim_hospital","state","Column"),("Metrics","HF Readmission Rate","Measure"),"HF readmission rate by state (single measure)",35,240,590,410),
  bar("state_rating",("dim_hospital","state","Column"),("Metrics","Average Hospital Rating","Measure"),"Average hospital rating by state",655,240,590,410)],
 "HospitalOpportunity": [
  textbox("title_opp","Hospital Opportunity",35,15,1210,54),
  textbox("sub_opp","Compare like with like: charts use fixed, clinically coherent measures; hospital and state slicers cross-filter the page.",35,68,1210,36,"11pt","#52677B",False),
  slicer("slicer_state","dim_hospital","state","State",35,110,220,95),
  slicer("slicer_hospital","dim_hospital","facility_name","Hospital",275,110,500,95),
  card("opp_hf","Metrics","HF Readmission Rate","HF 30-day readmission rate",795,110,215,95),
  card("opp_nurse","Metrics","Nurse Communication Always %","Nurse communication — Always",1030,110,215,95),
  bar("hospital_hf",("dim_hospital","facility_name","Column"),("Metrics","HF Readmission Rate","Measure"),"Hospital HF readmission rate — fixed READM_30_HF",35,230,590,420),
  bar("hospital_nurse",("dim_hospital","facility_name","Column"),("Metrics","Nurse Communication Always %","Measure"),"Hospital nurse communication — fixed H_COMP_1_A_P",655,230,590,420)],
 "DataQualityProvenance": [
  textbox("title_dq","Data Quality & Provenance",35,15,1210,54),
  textbox("sub_dq","Refresh controls, coverage metrics, and curated source inventory. County context excludes blank/ambiguous keys before aggregation.",35,68,1210,36,"11pt","#52677B",False),
  card("dq_complete","Metrics","Readmission Completeness %","Readmission completeness",35,110,250,100),
  card("dq_unmatched","Metrics","Unmatched Hospital Rows","Unmatched hospital rows",305,110,250,100),
  card("dq_hcahps","Metrics","Hospitals With HCAHPS","Hospitals with nurse communication score",575,110,300,100),
  card("dq_counties","Metrics","Counties With Context","Counties with safe context",895,110,300,100),
  table("dq_table",[("Data Quality","metric","Column"),("Data Quality","value","Column")],"Warehouse quality checks",35,240,520,390),
  table("source_table",[("Source Snapshot","dataset","Column"),("Source Snapshot","source_url","Column"),("Source Snapshot","retrieved_at","Column"),("Source Snapshot","row_count","Column")],"Curated source snapshot",585,240,660,390)]}

page_order=[]
for i,(pid, visuals) in enumerate(pages.items()):
    page_order.append(pid)
    page_dir=REPORT/"definition/pages"/pid
    display={"ExecutiveOverview":"Executive Overview","HospitalOpportunity":"Hospital Opportunity","DataQualityProvenance":"Data Quality / Provenance"}[pid]
    write(page_dir/"page.json", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json","name":pid,"displayName":display,"displayOption":"FitToPage","height":720,"width":1280,
      "objects":{"background":[{"properties":{"color":{"solid":{"color":lit("'#F4F7FA'")}},"transparency":lit("0D")}}]}})
    for v in visuals: write(page_dir/"visuals"/v["name"]/"visual.json",v)
write(REPORT/"definition/pages/pages.json", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json","pageOrder":page_order,"activePageName":"ExecutiveOverview"})

# Semantic model (TMDL)
write(MODEL/"definition.pbism", {"$schema":"https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json","version":"4.2","settings":{"qnaEnabled":True}})
write(MODEL/"definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n\n")
write(MODEL/"definition/model.tmdl", "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\nannotation PBI_QueryOrder = [\"ProjectRoot\",\"dim_hospital\",\"dim_county\",\"fact_readmission\",\"fact_hcahps\",\"fact_county_health\",\"Data Quality\",\"Source Snapshot\",\"Metrics\"]\n\nannotation PBI_ProTooling = [\"DevMode\"]\n\nref table dim_hospital\nref table dim_county\nref table fact_readmission\nref table fact_hcahps\nref table fact_county_health\nref table 'Data Quality'\nref table 'Source Snapshot'\nref table Metrics\n\nref expression ProjectRoot\n\n")
write(MODEL/"definition/expressions.tmdl", "/// Repository root containing the outputs folder. Update after cloning; no username-specific path is committed.\nexpression ProjectRoot = \"SET_TO_REPOSITORY_ROOT\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]\n\tannotation PBI_ResultType = Text\n\n")

TABLES={
"dim_hospital": [("facility_id","string"),("facility_name","string"),("address","string"),("city","string"),("state","string"),("zip_code","string"),("county","string"),("hospital_type","string"),("ownership","string"),("emergency_services","string"),("overall_rating","double"),("readm_measure_count","double"),("county_key","string")],
"fact_readmission": [("facility_id","string"),("measure_id","string"),("measure_name","string"),("score","double"),("denominator","double"),("number_of_patients","double"),("number_returned","double"),("compared_to_national","string"),("footnote","string"),("start_date","string"),("end_date","string")],
"fact_hcahps": [("facility_id","string"),("measure_id","string"),("measure_name","string"),("answer_description","string"),("score","double"),("answer_percent","double"),("completed_surveys","double"),("response_rate","double"),("footnote","string"),("start_date","string"),("end_date","string")],
"fact_county_health": [("year","int64"),("state","string"),("county","string"),("county_fips","string"),("measure_id","string"),("measure_name","string"),("value_type","string"),("data_value","double"),("low_ci","double"),("high_ci","double"),("population","int64"),("county_key","string")],
"Data Quality": [("metric","string"),("value","double")],
"Source Snapshot": [("dataset","string"),("source_url","string"),("retrieved_at","string"),("row_count","int64"),("sha256","string")]
}
FILES={"dim_hospital":"dim_hospital.csv","fact_readmission":"fact_readmission.csv","fact_hcahps":"fact_hcahps.csv","fact_county_health":"fact_county_health.csv","Data Quality":"data_quality.csv","Source Snapshot":"source_snapshot.csv"}

def q(s): return "'"+s.replace("'","''")+"'" if " " in s or "-" in s else s

def table_tmdl(name, cols, filename, filter_m=None):
    out=[f"table {q(name)}",f"\tlineageTag: {uuid.uuid4()}",""]
    for col,typ in cols:
        out += [f"\tcolumn {q(col)}",f"\t\tdataType: {typ}",f"\t\tlineageTag: {uuid.uuid4()}","\t\tsummarizeBy: none",f"\t\tsourceColumn: {col}","","\t\tannotation SummarizationSetBy = Automatic",""]
    types=", ".join('{"'+c+'", '+{"string":"type text","double":"type number","int64":"Int64.Type"}[t]+'}' for c,t in cols)
    out += [f"\tpartition {q(name+' Import')} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet", f'\t\t\t\t    CsvPath = ProjectRoot & "\\\\outputs\\\\{filename}",', '\t\t\t\t    Source = Csv.Document(File.Contents(CsvPath),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),', "\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),"]
    typed_source = "Promoted"
    if name == "Source Snapshot":
        out += ['\t\t\t\t    Renamed = Table.RenameColumns(Promoted,{{"source_name", "dataset"}, {"retrieved_at_utc", "retrieved_at"}, {"rows", "row_count"}}),']
        typed_source = "Renamed"
    out += [f"\t\t\t\t    Typed = Table.TransformColumnTypes({typed_source},{{{types}}})"]
    if filter_m: out += [f"\t\t\t\t    ,Filtered = {filter_m}","\t\t\t\tin","\t\t\t\t    Filtered"]
    else: out += ["\t\t\t\tin","\t\t\t\t    Typed"]
    out += ["","\tannotation PBI_ResultType = Table",""]
    return "\n".join(out)

for name,cols in TABLES.items():
    filt=None
    if name=="fact_hcahps": filt='Table.SelectRows(Typed, each [measure_id] = "H_COMP_1_A_P")'
    if name=="fact_county_health": filt='Table.SelectRows(Typed, each [county_key] <> null and [county_key] <> "")'
    write(MODEL/"definition/tables"/(name.replace(" ","_")+".tmdl"),table_tmdl(name,cols,FILES[name],filt))

# Safe one-row-per-county dimension derived only from nonblank, valid aggregate county export keys.
dim_county='''table dim_county
\tlineageTag: %s

\tcolumn county_key
\t\tdataType: string
\t\tlineageTag: %s
\t\tsummarizeBy: none
\t\tsourceColumn: county_key

\tcolumn state
\t\tdataType: string
\t\tlineageTag: %s
\t\tsummarizeBy: none
\t\tsourceColumn: state

\tcolumn county
\t\tdataType: string
\t\tlineageTag: %s
\t\tsummarizeBy: none
\t\tsourceColumn: county

\tcolumn county_fips
\t\tdataType: string
\t\tlineageTag: %s
\t\tsummarizeBy: none
\t\tsourceColumn: county_fips

\tpartition 'dim_county Import' = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    CsvPath = ProjectRoot & "\\outputs\\fact_county_health.csv",
\t\t\t\t    Source = Csv.Document(File.Contents(CsvPath),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
\t\t\t\t    Selected = Table.SelectColumns(Promoted,{"county_key","state","county","county_fips"}),
\t\t\t\t    Valid = Table.SelectRows(Selected, each [county_key] <> null and [county_key] <> ""),
\t\t\t\t    DistinctRows = Table.Distinct(Valid, {"county_key"})
\t\t\t\tin
\t\t\t\t    DistinctRows

\tannotation PBI_ResultType = Table
''' % tuple(uuid.uuid4() for _ in range(5))
write(MODEL/"definition/tables/dim_county.tmdl",dim_county)

metrics='''table Metrics
\tlineageTag: %s

\tmeasure Hospitals = DISTINCTCOUNT(dim_hospital[facility_id])
\t\tformatString: #,0
\t\tlineageTag: %s

\tmeasure 'Available Readmission Rows' = COUNT(fact_readmission[score])
\t\tformatString: #,0
\t\tlineageTag: %s

\tmeasure 'HF Readmission Rate' = DIVIDE(CALCULATE(AVERAGE(fact_readmission[score]), KEEPFILTERS(fact_readmission[measure_id] = "READM_30_HF")), 100)
\t\tformatString: 0.0%%

\t\tlineageTag: %s

\tmeasure 'Nurse Communication Always %%' = DIVIDE(CALCULATE(AVERAGE(fact_hcahps[answer_percent]), KEEPFILTERS(fact_hcahps[measure_id] = "H_COMP_1_A_P")), 100)
\t\tformatString: 0.0%%

\t\tlineageTag: %s

\tmeasure 'Completed Surveys (Hospital Grain)' = SUMX(VALUES(dim_hospital[facility_id]), CALCULATE(MAX(fact_hcahps[completed_surveys])))
\t\tformatString: #,0

\t\tlineageTag: %s

\tmeasure 'Readmission Completeness %%' = DIVIDE(COUNT(fact_readmission[score]), COUNTROWS(fact_readmission))
\t\tformatString: 0.0%%
\t\tlineageTag: %s

\tmeasure 'Average Hospital Rating' = AVERAGE(dim_hospital[overall_rating])
\t\tformatString: 0.0
\t\tlineageTag: %s

\tmeasure 'Unmatched Hospital Rows' = CALCULATE(MAX('Data Quality'[value]), 'Data Quality'[metric] = "unmatched_hospitals")
\t\tformatString: #,0
\t\tlineageTag: %s

\tmeasure 'Hospitals With HCAHPS' = COUNTROWS(FILTER(VALUES(dim_hospital[facility_id]), NOT ISBLANK([Nurse Communication Always %%])))
\t\tformatString: #,0
\t\tlineageTag: %s

\tmeasure 'Counties With Context' = DISTINCTCOUNT(dim_county[county_key])
\t\tformatString: #,0
\t\tlineageTag: %s

\tpartition Metrics = calculated
\t\tmode: import
\t\tsource = ROW("_placeholder", 1)
''' % tuple(uuid.uuid4() for _ in range(11))
write(MODEL/"definition/tables/Metrics.tmdl",metrics)
rels=[]
for frm,to in [("fact_readmission.facility_id","dim_hospital.facility_id"),("fact_hcahps.facility_id","dim_hospital.facility_id"),("fact_county_health.county_key","dim_county.county_key"),("dim_hospital.county_key","dim_county.county_key")]:
    rels += [f"relationship {uuid.uuid4()}",f"\tfromColumn: {frm}",f"\ttoColumn: {to}",""]
write(MODEL/"definition/relationships.tmdl","\n".join(rels))
print(f"Generated {ROOT / 'Healthcare Readmission Intelligence.pbip'}")
