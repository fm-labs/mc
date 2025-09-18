

# from pydantic import BaseModel
#
# from kloudia.db.mongodb import get_mongo_collection
#
#
# class FindingModel(BaseModel):
#     tool: str
#     type: str
#     target: str
#     title: str
#     description: str
#     severity: str # LOW, MEDIUM, HIGH, CRITICAL
#     category: str
#     timestamp: int
#     metadata: dict | None = None
#
#
#
# def save_finding(finding: dict) -> None:
#     collection = get_mongo_collection('kloudia', 'findings')
#     collection.insert_one(finding)


