from typing import List

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "OK"}


@router.get("/info")
async def info() -> dict:
    return dict({
        "name": "Kloudia API Service",
        "status": "running",
        "version": "0.1.0",
    })
