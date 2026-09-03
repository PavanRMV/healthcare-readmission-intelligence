import re
import unicodedata
import pandas as pd
from .config import READMISSION_MEASURES, CDC_MEASURES

MISSING = {"", "not available", "nan", "none", "n/a", "--"}

def facility_id(value):
    if pd.isna(value): return None
    return str(value).strip().split(".")[0].zfill(6)

def parse_numeric(value):
    if value is None or str(value).strip().lower() in MISSING: return float("nan")
    return pd.to_numeric(str(value).replace(",", "").replace("%", ""), errors="coerce")

def normalize_county_key(county, state):
    if pd.isna(county) or pd.isna(state): return None
    text = unicodedata.normalize("NFKD", str(county)).encode("ascii", "ignore").decode()
    text = re.sub(r"\b(COUNTY|PARISH|BOROUGH|CENSUS AREA|MUNICIPALITY)\b", "", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
    return f"{str(state).strip().upper()}|{text}" if text else None

def col(df, name, default=None):
    return df[name] if name in df else pd.Series([default] * len(df), index=df.index)

def clean_hospitals(df):
    out = pd.DataFrame({"facility_id": col(df,"Facility ID").map(facility_id), "facility_name": col(df,"Facility Name"), "address": col(df,"Address"), "city": col(df,"City/Town"), "state": col(df,"State"), "zip_code": col(df,"ZIP Code").astype("string"), "county": col(df,"County/Parish"), "hospital_type": col(df,"Hospital Type"), "ownership": col(df,"Hospital Ownership"), "emergency_services": col(df,"Emergency Services"), "overall_rating": col(df,"Hospital overall rating").map(parse_numeric), "readm_measure_count": col(df,"Count of Facility READM Measures").map(parse_numeric)})
    out["county_key"] = [normalize_county_key(c,s) for c,s in zip(out.county,out.state)]
    return out.drop_duplicates("facility_id")

def clean_readmissions(df):
    x=df.loc[col(df,"Measure ID").isin(READMISSION_MEASURES)]
    return pd.DataFrame({"facility_id": col(x,"Facility ID").map(facility_id), "measure_id": col(x,"Measure ID"), "measure_name": col(x,"Measure Name"), "score": col(x,"Score").map(parse_numeric), "denominator": col(x,"Denominator").map(parse_numeric), "number_of_patients": col(x,"Number of Patients").map(parse_numeric), "number_returned": col(x,"Number of Patients Returned").map(parse_numeric), "compared_to_national": col(x,"Compared to National"), "footnote": col(x,"Footnote"), "start_date": col(x,"Start Date"), "end_date": col(x,"End Date")}).reset_index(drop=True)

def clean_hcahps(df):
    x=df
    return pd.DataFrame({"facility_id":col(x,"Facility ID").map(facility_id), "measure_id":col(x,"HCAHPS Measure ID"), "measure_name":col(x,"HCAHPS Question"), "answer_description":col(x,"HCAHPS Answer Description"), "score":col(x,"Patient Survey Star Rating").map(parse_numeric), "answer_percent":col(x,"HCAHPS Answer Percent").map(parse_numeric), "completed_surveys":col(x,"Number of Completed Surveys").map(parse_numeric), "response_rate":col(x,"Survey Response Rate Percent").map(parse_numeric), "footnote":col(x,"Patient Survey Star Rating Footnote"), "start_date":col(x,"Start Date"),"end_date":col(x,"End Date")})

def clean_places(df):
    x=df[col(df,"measureid").isin(CDC_MEASURES)].copy(); x["data_value"] = col(x,"data_value").map(parse_numeric); x["rank"] = col(x,"datavaluetypeid").map({"AgeAdjPrv":0,"CrdPrv":1}).fillna(2)
    x=x.sort_values(["year","locationid","measureid","rank"]).drop_duplicates(["year","locationid","measureid"])
    out=pd.DataFrame({"year":pd.to_numeric(col(x,"year"),errors="coerce").astype("Int64"),"state":col(x,"stateabbr"), "county":col(x,"locationname"),"county_fips":col(x,"locationid").astype("string"),"measure_id":col(x,"measureid"), "measure_name":col(x,"measure"),"value_type":col(x,"datavaluetypeid"),"data_value":x["data_value"], "low_ci":col(x,"low_confidence_limit").map(parse_numeric),"high_ci":col(x,"high_confidence_limit").map(parse_numeric), "population":col(x,"totalpopulation").map(parse_numeric)})
    out["county_key"]=[normalize_county_key(c,s) for c,s in zip(out.county,out.state)]
    return out.reset_index(drop=True)
