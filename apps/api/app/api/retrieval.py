from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.retrieval.search import search_chunks

router = APIRouter(tags=["retrieval"])


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    concept_code: str | None = None
    source_codes: list[str] = []
    language: Literal["vi", "en"] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/retrieval/search")
def retrieval_search(
    payload: RetrievalRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    del user  # authenticated endpoint; no learner state is needed for raw retrieval testing
    results = search_chunks(
        db,
        payload.query,
        concept_code=payload.concept_code,
        source_codes=payload.source_codes or None,
        language=payload.language,
        top_k=payload.top_k,
    )
    return {
        "query": payload.query,
        "count": len(results),
        "results": [item.as_dict() for item in results],
    }
