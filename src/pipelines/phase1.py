from __future__ import annotations

import logging
from datetime import datetime, timezone

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 1. Load settings
    logger.info("1. Loading settings...")
    settings = load_settings()

    # 2. Load or fetch raw records (Thành viên 2)
    logger.info("2. Fetching source records...")
    records = fetch_source_records(settings)
    logger.info(f" -> Fetched {len(records)} records.")

    # 3. Clean data (Thành viên 2)
    logger.info("3. Cleaning data...")
    df = build_clean_dataframe(records, datetime.now(timezone.utc))
    logger.info(f" -> Cleaned dataframe shape: {df.shape}")

    # 4. Save clean CSV/JSON
    logger.info("4. Saving clean data...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    df.to_json(settings.paths.clean_json, orient="records", force_ascii=False, indent=2)
    logger.info(f" -> Saved to {settings.paths.clean_csv}")

    # --- Các phần dưới đây sẽ do Thành viên 3 và 4 làm, Thành viên 1 kết nối vào ---
    # 5. Build Chroma index (Thành viên 3)
    logger.info("5. Build Chroma index...")
    from retrieval.index import LocalEmbeddingIndex
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    logger.info(f" -> Built Chroma collection: {index.collection_name}")

    # 6. Tao hoac load evaluation set (Thành viên 4)
    logger.info("6. (TODO) Build/Load evaluation set...")
    # from evaluation.testset import build_test_set
    # test_set = build_test_set(df, settings.paths.eval_testset)

    # 7. Evaluate (Thành viên 4)
    logger.info("7. (TODO) Evaluate...")
    # from evaluation.metrics import evaluate_pipeline
    # evaluate_pipeline(...)

    # 8. Run quality checks (Thành viên 4)
    logger.info("8. (TODO) Run quality checks...")
    # from observability.quality import run_data_quality_checks
    # run_data_quality_checks(...)

    # 9. Create Markdown report (Thành viên 4)
    logger.info("9. (TODO) Create report...")

    # 10. Demo QA Agent (Thành viên 3)
    logger.info("10. Demo QA Agent...")
    from retrieval.agent import build_agent, run_agent_question
    agent = build_agent(settings, index)
    sample_question = "What is the summary of the paper 'Agentic Retrieval-Augmented Generation for Knowledge-Intensive Tasks'?"
    logger.info(f" -> Question: {sample_question}")
    answer = run_agent_question(agent, sample_question)
    logger.info(f" -> Agent Answer: {answer}")

    logger.info("Phase 1 Data Foundation & Indexing Complete!")


if __name__ == "__main__":
    main()
