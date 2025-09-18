from typing import List

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_findings() -> List[dict]:
    return []

