from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


import json
import pathlib

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """TODO(student): tao bo data quality checks.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    row_count = len(df)
    paper_id_ok = bool(df["paper_id"].notna().all() and df["paper_id"].is_unique)
    title_ok = bool(df["title"].notna().all())
    summary_ok = bool((df["summary"].fillna("").str.len() > 0).all()) if "summary" in df.columns else False
    freshness_ok = bool((df["age_days"] >= 0).all()) if "age_days" in df.columns else False
    
    success = paper_id_ok and title_ok and summary_ok and freshness_ok
    
    report = {
        "success": success,
        "row_count": row_count,
        "paper_id_ok": paper_id_ok,
        "title_ok": title_ok,
        "summary_ok": summary_ok,
        "freshness_ok": freshness_ok
    }
    
    report_file = settings.paths.quality_dir / f"{report_name}.json"
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """TODO(student): tong hop freshness report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    if "published_date" in df.columns:
        latest = df["published_date"].max()
        oldest = df["published_date"].min()
        latest_str = latest.isoformat() if hasattr(latest, "isoformat") else str(latest)
        oldest_str = oldest.isoformat() if hasattr(oldest, "isoformat") else str(oldest)
    else:
        latest_str, oldest_str = None, None
        
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
    total_rows = len(df)
    is_fresh = stale_rows == 0
    
    payload = {
        "latest_published": latest_str,
        "oldest_published": oldest_str,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh
    }
    
    pathlib.Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        
    return payload
