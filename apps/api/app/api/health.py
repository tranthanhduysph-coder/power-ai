from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    vector = db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")) .scalar_one_or_none()
    return {"status": "ok", "database": "ok", "pgvector": vector or "missing"}
