from pydantic import BaseModel

from mc.db.mongodb import get_mongo_collection


class FindingModel(BaseModel):
    tool: str
    tool_version: str | None = None
    tool_ref: str | None = None
    type: str
    target: str
    title: str
    description: str | None = None
    message: str | None = None
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    category: str
    timestamp: int
    metadata: dict | None = None



def save_finding(finding: dict) -> None:
    collection = get_mongo_collection('kloudia', 'findings')
    collection.insert_one(finding)


