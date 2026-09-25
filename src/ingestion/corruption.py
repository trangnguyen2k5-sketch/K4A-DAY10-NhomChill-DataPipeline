from __future__ import annotations

import pandas as pd
import numpy as np

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    df_corrupted = df.copy()
    
    # 1. Drop mot so latest records (simulate data loss)
    # 2. Blank summary o mot so dong (simulate data quality issue)
    # 3. Add duplicate rows (simulate pipeline retry issue)
    # 4. Ghi corruption log
    
    # Drop first 5 rows (assuming it's sorted by latest first)
    dropped_count = 5 if len(df_corrupted) > 5 else 0
    if dropped_count:
        df_corrupted = df_corrupted.iloc[dropped_count:].copy()
        
    # Blank summary for next 5 rows
    blank_count = 5 if len(df_corrupted) > 5 else 0
    if blank_count:
        df_corrupted.loc[df_corrupted.index[:blank_count], 'summary'] = ""
        
    # Add duplicates of the next 5 rows
    dup_count = 5 if len(df_corrupted) > 5 else 0
    if dup_count:
        dups = df_corrupted.iloc[:dup_count].copy()
        df_corrupted = pd.concat([df_corrupted, dups], ignore_index=True)
        
    # Rebuild `text_for_embedding` if we touched summary
    # Wait, 'text_for_embedding' depends on multiple columns.
    # We will just blank the summary inside text_for_embedding as well.
    if 'text_for_embedding' in df_corrupted.columns:
        # Just a simple string replacement for those blanked summaries
        df_corrupted['text_for_embedding'] = df_corrupted.apply(
            lambda row: f"Title: {row.get('title', '')}\nAuthors: {row.get('authors_joined', '')}\nPublished: {row.get('published', '')}\nCategories: {row.get('categories_joined', '')}\nSummary: {row.get('summary', '')}", 
            axis=1
        )
        
    # Introduce staleness
    if 'age_days' in df_corrupted.columns:
        df_corrupted['age_days'] = df_corrupted['age_days'] + 200 # Make everything older by 200 days
        
    log = {
        "dropped_rows": dropped_count,
        "blank_summary_rows": blank_count,
        "duplicated_rows": dup_count,
        "staleness_injected": 200
    }
    write_json(output_log_path, log)
    
    return df_corrupted
