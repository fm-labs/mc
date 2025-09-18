from typing import List

from fastapi import APIRouter

from kloudia.inventory.clouds.datamodels import KloudiaCloudModel
from kloudia.inventory.storage import get_inventory_storage_instance

router = APIRouter()


@router.get("/inventory/clouds")
async def get_clouds() -> List[KloudiaCloudModel]:
    storage = get_inventory_storage_instance()
    storage.list_items("clouds")
    return [KloudiaCloudModel(**cloud) for cloud in storage.list_items("clouds")]


@router.get("/inventory/clouds/{cloud_name}", response_model=KloudiaCloudModel)
async def get_cloud(cloud_name: str) -> KloudiaCloudModel | None:
    storage = get_inventory_storage_instance()
    item = storage.get_item("clouds", cloud_name)
    if item:
        return KloudiaCloudModel(**item)
    return None
