import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests
from .config import CMS_DATASETS, CMS_META_URL, CDC_URL, CDC_MEASURES

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def download(url, path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with requests.get(url,stream=True,timeout=(30,300)) as r:
        r.raise_for_status()
        with open(path,"wb") as f:
            for chunk in r.iter_content(1024*1024): f.write(chunk)
    return path

def fetch_cms(raw_dir):
    frames={}; meta=[]
    for name,dataset_id in CMS_DATASETS.items():
        resp=requests.get(CMS_META_URL.format(dataset_id=dataset_id),timeout=60); resp.raise_for_status(); info=resp.json()
        url=info["distribution"][0]["downloadURL"]; path=download(url,Path(raw_dir)/f"{name}.csv")
        frames[name]=pd.read_csv(path,dtype=str,low_memory=False)
        meta.append({"source_name":name,"dataset_id":dataset_id,"source_url":url,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"source_modified":info.get("modified"),"source_released":info.get("released"),"sha256":sha256(path),"bytes":path.stat().st_size,"rows":len(frames[name])})
    return frames,meta

def fetch_places(raw_dir):
    records=[]; offset=0; limit=50000
    where="measureid in("+",".join(repr(x) for x in sorted(CDC_MEASURES))+") AND datavaluetypeid in('AgeAdjPrv','CrdPrv')"
    while True:
        r=requests.get(CDC_URL,params={"$limit":limit,"$offset":offset,"$where":where,"$order":"year DESC"},timeout=180); r.raise_for_status(); batch=r.json(); records.extend(batch)
        if len(batch)<limit: break
        offset+=limit
    raw=Path(raw_dir)/"cdc_places.json"; raw.parent.mkdir(parents=True,exist_ok=True); raw.write_text(json.dumps(records),encoding="utf-8")
    df=pd.DataFrame(records); meta={"source_name":"cdc_places","dataset_id":"swc5-untb","source_url":r.url,"retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"source_modified":None,"source_released":None,"sha256":sha256(raw),"bytes":raw.stat().st_size,"rows":len(df)}
    return df,meta
