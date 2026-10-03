from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.retrieval.search import search_chunks
from app.services.tutor import mock_tutor_blocks

router = APIRouter(tags=["tutor"])


class TutorRequest(BaseModel):
    concept_code: str = "BIO.DNA.REPLICATION"
    message: str
    language: Literal["vi", "en"] = "vi"


@router.post("/tutor/respond")
def tutor_respond(
    payload: TutorRequest,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # v0.2 keeps the tutor response itself mocked, but now runs real retrieval
    # and returns provenance. v0.3 can feed the built context into a production LLM.
    retrieved = search_chunks(
        db,
        payload.message,
        concept_code=payload.concept_code,
        language=payload.language,
        top_k=4,
    )
    blocks = mock_tutor_blocks(payload.language, payload.message)
    db.execute(
        text("""
            INSERT INTO usage_ledger(user_id, feature, quantity, metadata)
            VALUES (:user_id, 'ai_tutor_mock', 1, CAST(:metadata AS jsonb))
        """),
        {
            "user_id": user.id,
            "metadata": __import__("json").dumps(
                {
                    "concept_code": payload.concept_code,
                    "retrieved_chunks": len(retrieved),
                }
            ),
        },
    )
    db.commit()
    return {
        "provider": "mock",
        "blocks": blocks,
        "retrieval": {
            "count": len(retrieved),
            "sources": [item.as_dict() for item in retrieved],
        },
    }
