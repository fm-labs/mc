from typing import Annotated

from fastapi import APIRouter, Query

from kloudia.db.mongodb import mongodb_results_to_json, get_mongo_collection

router = APIRouter()





@router.get("/findings")
async def get_findings(
        resource_type: Annotated[str, Query()] = None,
        resource_id: Annotated[str, Query()] = None,
        resource_name: Annotated[str, Query()] = None,
        check_name: Annotated[str, Query()] = None,
        severity: Annotated[str, Query()] = None,
):
    findings_collection = get_mongo_collection("findings", "findings")

    filters = {}
    if resource_type:
        filters["resource_type"] = resource_type
    if resource_id:
        filters["resource_id"] = resource_id
    if resource_name:
        filters["resource_name"] = resource_name
    if check_name:
        filters["type"] = check_name
    if severity:
        filters["severity"] = severity

    findings = findings_collection.find(filters).sort([("severity", -1), ("timestamp", -1)])
    return mongodb_results_to_json(findings)
