from __future__ import annotations

import logging
import pandas as pd
import json
from datetime import datetime, timezone

from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from retrieval.index import LocalEmbeddingIndex
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 1. Load baseline metrics va clean dataset
    logger.info("1. Loading settings & baseline data...")
    settings = load_settings()
    
    clean_df = pd.read_csv(settings.paths.clean_csv)
    with open(settings.paths.baseline_metrics, "r") as f:
        baseline_metrics = json.load(f)

    # 2. Tao corrupted dataframe
    logger.info("2. Corrupting dataframe...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)

    # 3. Save corrupted artifacts
    logger.info("3. Saving corrupted artifacts...")
    corrupted_csv = settings.paths.clean_csv.parent / "corrupted_dataset.csv"
    corrupted_df.to_csv(corrupted_csv, index=False)

    from evaluation.metrics import evaluate_pipeline
    
    # 4. Rebuild index va evaluate (Corrupted)
    logger.info("4. Rebuilding corrupted index...")
    LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    
    corrupted_index = LocalEmbeddingIndex.load(settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers
    )
    corrupted_metrics = corrupted_bundle.summary

    # 5. Run quality checks/freshness tren corrupted data
    logger.info("5. Quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, 'corrupted')
    corrupted_freshness = build_freshness_report(corrupted_df, settings, settings.paths.freshness_report.parent / "corrupted_freshness.json")

    # 6. Repair lai tu raw records
    logger.info("6. Repairing from raw records...")
    records = fetch_source_records(settings)
    repaired_df = build_clean_dataframe(records, datetime.now(timezone.utc))

    # 7. Evaluate repaired dataset
    logger.info("7. Evaluating repaired index...")
    LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    
    repaired_index = LocalEmbeddingIndex.load(settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers
    )
    repaired_metrics = repaired_bundle.summary
    repaired_quality = run_data_quality_checks(repaired_df, settings, 'repaired')
    repaired_freshness = build_freshness_report(repaired_df, settings, settings.paths.freshness_report.parent / "repaired_freshness.json")

    # 8. Tao comparison report
    logger.info("8. Generating comparison report...")
    settings.paths.comparison_report.parent.mkdir(parents=True, exist_ok=True)
    report_path = settings.paths.comparison_report
    
    generate_corruption_report(
        report_path,
        baseline_metrics,
        corrupted_metrics,
        repaired_metrics,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness
    )
    
    logger.info(f"Corruption flow complete! Report saved to {report_path}")

if __name__ == "__main__":
    main()
