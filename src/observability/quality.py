from __future__ import annotations

from typing import Any
import great_expectations as gx
from great_expectations.expectations.expectation import ExpectationConfiguration
from great_expectations.expectations.core import (
    ExpectTableRowCountToBeBetween,
    ExpectColumnValuesToNotBeNull,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValueLengthsToBeBetween
)
import pandas as pd

from core.config import Settings
from core.utils import write_json


import json
import pathlib

def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})
    
    suite = context.suites.add(gx.ExpectationSuite(name="papers_suite"))
    
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="title"))
    if "text_for_embedding" in df.columns:
        suite.add_expectation(ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))
    
    validation_definition = context.validation_definitions.add(
        gx.ValidationDefinition(
            name="papers_validation",
            data=batch_def,
            suite=suite,
        )
    )
    
    checkpoint = context.checkpoints.add(
        gx.Checkpoint(
            name="papers_checkpoint",
            validation_definitions=[validation_definition],
        )
    )
    
    result = checkpoint.run(batch_parameters={"dataframe": df})
    
    success = result.success
    results_dict = {
        "success": success,
        "run_id": str(result.run_id) if hasattr(result, 'run_id') and result.run_id else None
    }
    
    report_path = settings.paths.baseline_quality_report.parent / f"{report_name}_gx_report.json"
    write_json(report_path, results_dict)
    
    return {
        "success": success,
        "run_id": results_dict["run_id"],
        "report_path": str(report_path)
    }


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    latest_published = df["published"].max() if "published" in df.columns else None
    oldest_published = df["published"].min() if "published" in df.columns else None
    total_rows = len(df)
    
    stale_rows = 0
    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > 180).sum())
    
    stale_ratio = stale_rows / total_rows if total_rows > 0 else 0
    is_fresh = stale_ratio <= 0.25
    
    payload = {
        "latest_published": str(latest_published),
        "oldest_published": str(oldest_published),
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": is_fresh,
        "stale_ratio": stale_ratio
    }
    
    write_json(report_path, payload)
    return payload
