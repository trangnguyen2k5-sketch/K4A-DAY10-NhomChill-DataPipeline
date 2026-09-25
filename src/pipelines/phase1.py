from __future__ import annotations

import logging
from datetime import datetime, timezone

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 1. Load settings
    logger.info("1. Loading settings...")
    settings = load_settings()

    # 2. Load or fetch raw records
    logger.info("2. Fetching source records...")
    records = fetch_source_records(settings)
    logger.info(f" -> Fetched {len(records)} records.")

    # 3. Clean data
    logger.info("3. Cleaning data...")
    df = build_clean_dataframe(records, datetime.now(timezone.utc))
    logger.info(f" -> Cleaned dataframe shape: {df.shape}")

    # 4. Save clean CSV/JSON
    logger.info("4. Saving clean data...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", force_ascii=False, indent=2)
    logger.info(f" -> Saved to {settings.paths.clean_csv}")

    # 5. Build Chroma index
    logger.info("5. Build Chroma index...")
    LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)

    # 6. Tao hoac load evaluation set
    logger.info("6. Build/Load evaluation set...")
    test_set = build_test_set(df, settings.paths.eval_testset)
    logger.info(f" -> Evaluation set size: {len(test_set)}")

    # 7. Evaluate
    logger.info("7. Evaluate...")
    from evaluation.metrics import evaluate_pipeline
    index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
    eval_bundle = evaluate_pipeline(
        settings, 
        index, 
        settings.paths.eval_testset, 
        settings.paths.baseline_metrics, 
        settings.paths.baseline_answers
    )
    metrics = eval_bundle.summary

    # 8. Run quality checks
    logger.info("8. Run quality checks & freshness...")
    quality = run_data_quality_checks(df, settings, 'baseline')
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report.parent / "baseline_freshness.json")

    # 9. Create Markdown report
    logger.info("9. Create report...")
    source_summary = {"total_rows": len(df)}
    settings.paths.baseline_report.parent.mkdir(parents=True, exist_ok=True)
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        metrics,
        quality,
        freshness
    )

    logger.info("Phase 1 Data Foundation Complete!")


if __name__ == "__main__":
    main()
