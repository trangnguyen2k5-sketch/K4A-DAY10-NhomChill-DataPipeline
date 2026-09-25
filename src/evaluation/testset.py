from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from core.utils import first_sentence

def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict]:
    test_set = []
    
    if len(df) > 0:
        for idx, row in df.iterrows():
            # Generate different types of questions deterministically based on index
            q_type = idx % 4
            title = row.get('title', 'Unknown')
            paper_id = row.get('paper_id')
            
            if q_type == 0:
                q = f"Who authored the paper '{title}'?"
                ans = str(row.get('authors_joined', ''))
                type_name = "author"
            elif q_type == 1:
                q = f"When was the paper '{title}' published?"
                ans = str(row.get('published', ''))
                type_name = "date"
            elif q_type == 2:
                q = f"What categories does the paper '{title}' belong to?"
                ans = str(row.get('categories_joined', ''))
                type_name = "category"
            else:
                q = f"What is the summary of '{title}'?"
                ans = first_sentence(str(row.get('summary', '')))
                type_name = "summary"
                
            test_set.append({
                "id": f"q_{paper_id}_{type_name}",
                "question_type": type_name,
                "question": q,
                "ground_truth": ans,
                "ground_truth_doc_ids": [paper_id]
            })
            
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(test_set, f, indent=2)
        
    return test_set
