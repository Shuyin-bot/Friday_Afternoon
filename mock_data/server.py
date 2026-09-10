from fastapi import FastAPI, HTTPException
import json
from pathlib import Path
import pandas as pd

# 创建一个名为app的FastAPI应用
app = FastAPI(title="PackFlow Mock Data API", version="1.0")

BASE_DIR = Path(__file__).parent

# 读取json文件的逻辑
def load_json(filepath):
    p = BASE_DIR / filepath
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# 定义当别人访问某个网址时，该返回什么数据
@app.get("/")
def root():
    return {"message": "PackFlow Mock Data API is running", "endpoints": [
        "/seller/company_info",
        "/seller/product_catalog",
        "/seller/past_correspondence",
        "/seller/historical_lead_outcomes",
        "/leads/form_submissions",
        "/leads/email_inbox",
        "/leads/badge_scan_export"
    ]}

@app.get("/seller/company_info")
def get_company_info():
    return load_json("seller/company_info.json")

@app.get("/seller/product_catalog")
def get_product_catalog():
    return load_json("seller/product_catalog.json")

@app.get("/seller/past_correspondence")
def get_past_correspondence():
    return load_json("seller/past_correspondence.json")

@app.get("/seller/historical_lead_outcomes")
def get_historical_lead_outcomes():
    return load_json("seller/historical_lead_outcomes.json")

@app.get("/leads/form_submissions")
def get_form_submissions():
    return load_json("leads/form_submissions.json")

@app.get("/leads/email_inbox")
def get_email_inbox():
    return load_json("leads/email_inbox.json")

@app.get("/leads/badge_scan_export")
def get_badge_scan():
    csv_path = BASE_DIR / "leads/badge_scan_export.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not found")
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")
