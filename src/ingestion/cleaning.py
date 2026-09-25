from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame([asdict(r) for r in records])
    
    df['title'] = df['title'].str.strip()
    df['summary'] = df['summary'].str.strip()
    
    df['published_dt'] = pd.to_datetime(df['published'], errors='coerce')
    run_date_naive = run_date.replace(tzinfo=None)
    df['age_days'] = (run_date_naive - df['published_dt']).dt.days
    
    df['authors_joined'] = df['authors'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df['categories_joined'] = df['categories'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
    df['summary_chars'] = df['summary'].str.len()
    
    df['text_for_embedding'] = (
        "Title: " + df['title'] + "\n" +
        "Authors: " + df['authors_joined'] + "\n" +
        "Published: " + df['published_dt'].dt.strftime('%Y-%m-%d').fillna("") + "\n" +
        "Categories: " + df['categories_joined'] + "\n" +
        "Summary: " + df['summary']
    )
    
    df = df.drop_duplicates(subset=['paper_id'], keep='first')
    df = df.dropna(subset=['paper_id', 'title', 'summary'])
    df = df[df['summary_chars'] >= 30]
    
    df = df.sort_values(by='published_dt', ascending=False).reset_index(drop=True)
    df = df.drop(columns=['published_dt'])
    
    return df
