import logging
from typing import Dict, Optional, Annotated

from bson import ObjectId
from fastapi import HTTPException, Query, Request, Depends, APIRouter

from kloudia.db.mongodb import mongodb_results_to_json, mongodb_result_to_json
from kloudia.plugin.aws.awsgraph import AwsItemGraph
from kloudia.plugin.aws.repo import AwsInventoryRepo


def dep_inventory_repo() -> AwsInventoryRepo:
    return AwsInventoryRepo()


router = APIRouter()


@router.get("/aws/configuration")
async def get_aws_configuration(request: Request):
    return {
        "connectedAccounts": []
    }


@router.get("/aws/{account_id}/resources")
def list_aws_services_in_region(request: Request, account_id: str, ir: AwsInventoryRepo = Depends(dep_inventory_repo)):
    return get_inventory(request, account_id, None, None, None, None, ir)


@router.get("/aws/{account_id}/{region_id}/resources")
def list_aws_services_in_region(request: Request, account_id: str, region_id: str,
                                ir: AwsInventoryRepo = Depends(dep_inventory_repo)):
    return get_inventory(request, account_id, region_id, None, None, None, ir)


@router.get("/aws/{account_id}/{region_id}/{service_id}/resources")
def list_aws_service_resources(request: Request, account_id: str, region_id: str, service_id: str,
                               ir: AwsInventoryRepo = Depends(dep_inventory_repo)):
    return get_inventory(request, account_id, region_id, service_id, None, None, ir)


# @router.get("/aws/{account_id}/{region_id}/services/{service_id}/resources/{resource}")
# async def get_aws_resource_details(request: Request):
#     return {"message": "Get AWS Resource Details - Not Implemented Yet"}

@router.get("/aws/inventory/")
def get_inventory(
        request: Request,
        account_id: Annotated[Optional[str], Query()] = None,
        region_id: Annotated[Optional[str], Query()] = None,
        service_id: Annotated[Optional[str], Query()] = None,
        resource_type: Annotated[Optional[str], Query()] = None,
        properties: Annotated[Optional[str], Query()] = None,
        ir: AwsInventoryRepo = Depends(dep_inventory_repo),
):
    logging.info("REQ QUERY %s", dict(request.query_params))

    # if not account_id:
    #    # Mirror Express behavior: 400 + { error: 'account_id is required' }
    #    raise HTTPException(status_code=400, detail={"error": "account_id is required"})
    filters: Dict[str, str] = {}
    if account_id:
        filters["accountId"] = account_id

    if region_id and region_id not in ("*", "all"):
        filters["regionId"] = region_id

    if service_id and service_id not in ("*", "all"):
        filters["serviceId"] = service_id

    if resource_type and resource_type not in ("*", "all"):
        filters["resourceType"] = resource_type

    # properties is a JSON string representing a dict of key/value pairs to match in the properties field
    if properties:
        try:
            import json
            props = json.loads(properties)
            for k, v in props.items():
                filters[f"properties.{k}"] = v
        except Exception as e:
            raise HTTPException(status_code=400, detail={"error": f"Invalid properties parameter: {str(e)}"})

    logging.info("FIND INVENTORY %s", filters)
    data = ir.find(filters)
    return mongodb_results_to_json(data)


@router.get("/aws/inventory/resource")
def get_inventory_resource(request: Request,
                           id: Annotated[int, Query()] = None,
                           resource_id: Annotated[str, Query()] = None,
                           resource_arn: Annotated[str, Query()] = None,
                           ir: AwsInventoryRepo = Depends(dep_inventory_repo)
                           ):
    logging.info("REQ QUERY %s", dict(request.query_params))

    # if not id:
    #    # Mirror Express behavior: 400 + { error: 'id is required' }
    #    raise HTTPException(status_code=400, detail={"error": "id is required"})

    filters = {}
    if id:
        filters["_id"] = id
    if resource_id:
        filters["resource_id"] = resource_id
    if resource_arn:
        filters["resource_arn"] = resource_arn

    logging.info("FIND INVENTORY RESOURCE %s", filters)
    data = ir.find(filters)
    print(data)
    if not data or len(data) == 0:
        raise HTTPException(status_code=404, detail=f"Resource '{id}' not found")
    return mongodb_result_to_json(data[0])


@router.get("/aws/inventory/item-graph")
def get_inventory_item_graph(id: Annotated[str, Query()],
                             max_depth: Annotated[Optional[int], Query()] = 1,
                             ir: AwsInventoryRepo = Depends(dep_inventory_repo)):
    filters = {"_id": ObjectId(id)}
    items = ir.find(filters)
    if not items or len(items) == 0:
        raise HTTPException(status_code=404, detail=f"Resource '{id}' not found")

    # @todo cache the graph result for this item id
    # and invalidate the cache when the item or related items change

    graph = AwsItemGraph(ir)
    max_depth = min(max_depth, 3)
    graph.process_items(items, max_depth=max_depth)
    return {"nodes": graph.nodes, "edges": graph.edges}
