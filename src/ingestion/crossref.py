from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        paper_id = item.get("DOI", "")
        titles = item.get("title", [])
        title = titles[0] if titles else ""
        
        abstract = item.get("abstract", "")
        # Clean basic XML tags like <jats:p>
        abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "").strip()
        
        authors_list = item.get("author", [])
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in authors_list]
        
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else ""
        
        # Published date
        published_parts = item.get("published", {}).get("date-parts", [[]])[0]
        if len(published_parts) >= 3:
            published = f"{published_parts[0]:04d}-{published_parts[1]:02d}-{published_parts[2]:02d}"
        else:
            published = "2000-01-01"
            
        updated = item.get("created", {}).get("date-time", "")
        abs_url = item.get("URL", "")
        
        if not paper_id or not title:
            continue
            
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=abstract,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url="",
                comment="",
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    payload = None
    
    if settings.refresh_source:
        try:
            base_url = "https://api.crossref.org/works"
            params = {
                "query": settings.source_query,
                "filter": settings.source_filter,
                "rows": settings.max_results
            }
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            
            settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
            with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to fetch from API: {e}. Falling back to snapshot.")
            
    if payload is None:
        try:
            with open(settings.paths.raw_api_response, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except FileNotFoundError:
            return []
            
    records = parse_crossref_payload(payload)
    
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**r) for r in data]
