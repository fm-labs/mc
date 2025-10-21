from typing import Dict, List, Any

from kloudia.db.mongodb import get_mongo_collection


class AwsInventoryRepo:

    def find(self, filters: Dict[str, str]) -> List[Dict[str, Any]]:
        db = get_mongo_collection("cloudscan", "aws_resources")
        print("FIND INVENTORY IN DB", filters)
        return list(db.find(filters))
