from typing import Literal

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

router = APIRouter()


class CreateAppRequest(BaseModel):
    name: str
    type: Literal["container", "compose"]
    image: str | None = None # (only container)
    stackfile: str | None = None # stackfile body (only compose)


@router.post("/apps/new/scratch")
def create_app_from_scratch():
    """New app from scratch"""
    pass


@router.post("/apps/new/bundle")
def create_app_from_bundle():
    """New app from a tar bundle file"""
    pass