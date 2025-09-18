import uuid
import json

from kloudia.config import load_config_json
from kloudia.inventory.storage import get_inventory_storage_instance

if __name__ == "__main__":

    domains = load_config_json("domains")

    inventory = []
    inventory_storage = get_inventory_storage_instance()
    for domain in domains:
        print(domain)
        name = domain.get("name")
        if not name:
            continue

        entry = {
            "uuid": str(uuid.uuid4().hex),
            "item_type": "internet_domain",
            "name": name,
            "properties": {
            }
        }
        inventory.append(entry)
        inventory_storage.save_item("internet_domain", entry)

    # save inventory to a file
    with open("data/inventory_internet_domain.json", "w") as f:
        json.dump(inventory, f, indent=4)
