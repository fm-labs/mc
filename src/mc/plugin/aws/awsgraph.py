from typing import List

from mc.plugin.aws.repo import AwsInventoryRepo

AWS_ITEMS_METADATA = [
    {
        "resource_type": "AWS::CloudFormation::Stack",
        "name": "CloudFormation Stack",
        "icon": "aws.cloudformation",
        "group": "Management",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::EC2::Instance", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::EC2::Vpc", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::ECR::Repository", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::ECS::Cluster", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::IAM::Role", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::IAM::User", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::IAM::InstanceProfile", ["StackId"], ["StackId"]),
            ("one-to-many", "AWS::CloudFormation::StackResource", ["StackId"], ["StackId"]),
        ]
    },
    {
        "resource_type": "AWS::CloudFormation::StackResource",
        "name": "CloudFormation Stack Resource",
        "icon": "aws.cloudformation",
        "group": "Management",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::CloudFormation::Stack", ["StackId"], ["StackId"]),
        ]
    },
    {
        "resource_type": "AWS::ECR::Repository",
        "name": "ECR Repository",
        "icon": "aws.ecr",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::ECR::Image", ["repositoryName", "registryId"], ["repositoryName", "registryId"]),
        ]
    },
    {
        "resource_type": "AWS::ECR::Image",
        "name": "ECR Image",
        "icon": "aws.ecr",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [("many-to-one","AWS::ECR::Repository", ["repositoryName", "registryId"], ["repositoryName", "registryId"])],
    },
    {
        "resource_type": "AWS::EC2::Instance",
        "name": "EC2 Instance",
        "icon": "aws.ec2",
        "group": "Compute",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::EC2::Volume", ["BlockDeviceMappings.{n}.Ebs.VolumeId"], ["VolumeId"]),
            #("many-to-one", "AWS::EC2::Vpc", ["VpcId"], ["VpcId"]),
            ("many-to-one", "AWS::EC2::Subnet", ["SubnetId"], ["SubnetId"]),
            ("many-to-many", "AWS::EC2::SecurityGroup", ["SecurityGroups.{n}.GroupId"], ["GroupId"]),
            ("many-to-one", "AWS::IAM::InstanceProfile", ["IamInstanceProfile.Id"], ["InstanceProfileId"]),
        ]
    },
    {
        "resource_type": "AWS::EC2::Volume",
        "name": "EC2 Volume",
        "icon": "aws.ebs",
        "group": "Storage",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::EC2::Instance", ["Attachments.{n}.InstanceId"], ["InstanceId"]),
        ]
    },
    {
        "resource_type": "AWS::EC2::Vpc",
        "name": "VPC",
        "icon": "aws.vpc",
        "group": "Networking",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::EC2::Subnet", ["VpcId"], ["VpcId"]),
            #("one-to-many", "AWS::EC2::Instance", ["VpcId"], ["VpcId"]),
            ("one-to-many", "AWS::EC2::SecurityGroup", ["VpcId"], ["VpcId"]),
        ]
    },
    {
        "resource_type": "AWS::EC2::Subnet",
        "name": "Subnet",
        "icon": "aws.subnet",
        "group": "Networking",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::EC2::Vpc", ["VpcId"], ["VpcId"]),
            ("one-to-many", "AWS::EC2::Instance", ["SubnetId"], ["SubnetId"]),
        ]
    },
    {
        "resource_type": "AWS::EC2::SecurityGroup",
        "name": "Security Group",
        "icon": "aws.security-group",
        "group": "Networking",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::EC2::Vpc", ["VpcId"], ["VpcId"]),
            ("many-to-many", "AWS::EC2::Instance", ["GroupId"], ["SecurityGroups.{n}.GroupId"]),
        ]
    },
    {
        "resource_type": "AWS::ECS::Cluster",
        "name": "ECS Cluster",
        "icon": "aws.ecs",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::ECS::Service", ["ClusterArn"], ["ClusterArn"]),
            ("one-to-many", "AWS::ECS::TaskDefinition", ["ClusterArn"], ["ClusterArn"]),
        ]
    },
    {
        "resource_type": "AWS::ECS::Service",
        "name": "ECS Service",
        "icon": "aws.ecs",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::ECS::Cluster", ["ClusterArn"], ["ClusterArn"]),
            ("many-to-one", "AWS::ECS::TaskDefinition", ["TaskDefinitionArn"], ["TaskDefinitionArn"]),
        ]
    },
    {
        "resource_type": "AWS::ECS::TaskDefinition",
        "name": "ECS Task Definition",
        "icon": "aws.ecs",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::ECS::Cluster", ["ClusterArn"], ["ClusterArn"]),
            ("one-to-many", "AWS::ECS::Service", ["TaskDefinitionArn"], ["TaskDefinitionArn"]),
        ]
    },
    {
        "resource_type": "AWS::ECS::ContainerInstance",
        "name": "ECS Container Instance",
        "icon": "aws.ecs",
        "group": "Containers",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::ECS::Cluster", ["ClusterArn"], ["ClusterArn"]),
            ("many-to-one", "AWS::EC2::Instance", ["Ec2InstanceId"], ["InstanceId"]),
        ]
    },
    {
        "resource_type": "AWS::IAM::InstanceProfile",
        "name": "IAM Instance Profile",
        "icon": "aws.iam",
        "group": "IAM",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::EC2::Instance", ["InstanceProfileId"], ["IamInstanceProfile.Id"]),
        ]
    },
    {
        "resource_type": "AWS::IAM::Role",
        "name": "IAM Role",
        "icon": "aws.iam",
        "group": "IAM",
        "default_view": "table",
        "related_resources": [
        ]
    },
    {
        "resource_type": "AWS::IAM::User",
        "name": "IAM User",
        "icon": "aws.iam",
        "group": "IAM",
        "default_view": "table",
        "related_resources": [
            ("one-to-many", "AWS::IAM::MFADevice", ["UserName"], ["UserName"]),
            ("one-to-many", "AWS::IAM::VirtualMFADevice", ["UserName"], ["UserName"]),
            ("one-to-many", "AWS::IAM::AccessKey", ["UserName"], ["UserName"]),
            ("many-to-many", "AWS::IAM::Role", ["UserName"], ["RoleName"]),
        ]
    },
    {
        "resource_type": "AWS::IAM::MFADevice",
        "name": "IAM User",
        "icon": "aws.iam",
        "group": "IAM",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::IAM::User", ["UserName"], ["UserName"]),
        ]
    },
    {
        "resource_type": "AWS::IAM::VirtualMFADevice",
        "name": "IAM Virtual MFA Device",
        "icon": "aws.iam",
        "group": "IAM",
        "default_view": "table",
        "related_resources": [
            ("many-to-one", "AWS::IAM::User", ["UserName"], ["UserName"]),
        ]
    },
]

def get_ir():
    return AwsInventoryRepo()


class AwsItemGraph:

    def __init__(self, ir: AwsInventoryRepo):
        self.repo = ir
        self.nodes = []
        self.edges = []
        self.last_node_id = 0
        self.node_item_map = {}
        self.visited_items = set()

    @staticmethod
    def get_item_meta(resource_type: str):
        for m in AWS_ITEMS_METADATA:
            if m["resource_type"] == resource_type:
                return m
        return None

    @staticmethod
    def lookup_related_items(item, rel):
        rel_type, rel_resource, local_keys, remote_keys = rel
        # Build filter for related resources
        rel_filters = {}
        val = item.get("properties", {})
        for lk, rk in zip(local_keys, remote_keys):
            print(lk, rk)
            # Support nested keys like Attachments.InstanceId
            local_value = val
            for part in lk.split('.'):
                print("Part:", part, type(local_value))
                if part == "{n}":
                    # Handle list part - take first element for now
                    if isinstance(local_value, list) and len(local_value) > 0:
                        local_value = local_value[0]
                    else:
                        local_value = None
                        break
                    continue
                local_value = local_value.get(part, None)
                if local_value is None:
                    print("> missing local key part:", part)
                    break
            if local_value is not None:
                rel_filters[f"properties.{rk}"] = local_value
                print("> found local value for", lk, "=", local_value)
        return rel_filters


    def get_item_node_id(self, item):
        # lookup in node_item_map
        item_id = str(item.get("_id"))
        node_id = self.node_item_map.get(item_id, None)
        if node_id is None:
            self.last_node_id += 1
            node_id = str(self.last_node_id)
            self.node_item_map[item_id] = node_id
        return node_id


    def add_node(self, item):
        item_id = str(item.get("_id"))
        node_id = self.get_item_node_id(item)
        if node_id not in [n["id"] for n in self.nodes]:
            self.nodes.append({
                "id": node_id,
                "item_id": item_id,
                "label": item.get('name', ''),
                "type": item.get("resourceType"),
            })
            return True
        return False


    def add_edge(self, from_id, to_id, label):
        _from_id = str(from_id)
        _to_id = str(to_id)
        if _from_id == _to_id:
            raise ValueError("Can't add edge to same node")

        edge_id = f"{_from_id}->{_to_id}"
        if edge_id not in [e["id"] for e in self.edges]:
            self.edges.append({
                "id": edge_id,
                "from": _from_id,
                "to": _to_id,
                "label": label,
            })
            return True
        return False

    def count_in_edges(self, node_id):
        return len([e for e in self.edges if e["to"] == node_id])
    def count_out_edges(self, node_id):
        return len([e for e in self.edges if e["from"] == node_id])
    def count_node_edges(self, node_id):
        return len([e for e in self.edges if e["from"] == node_id or e["to"] == node_id])



    def process_items(self, items: List[dict], depth=1, max_depth=1):

        for item in items:
            item_id = str(item.get("_id"))
            if item_id in self.visited_items:
                print("Skipping already visited item", item_id)
                continue
            self.visited_items.add(item_id)

            item_type = item.get("resourceType")
            print(item_id, item.get("resourceType"), item.get("name"))
            self.add_node(item)

            item_meta = self.get_item_meta(item.get("resourceType"))
            if item_meta:
                print("> found meta:", item_meta.get("name"))
                for rel in item_meta.get("related_resources", []):
                    print(">> processing relation:", rel)
                    rel_filters = self.lookup_related_items(item, rel)
                    print(">>> related filters:", rel_filters)
                    related_items = self.repo.find({"resourceType": rel[1], **rel_filters})
                    print(f">>> found {len(related_items)} related items of type {rel[1]}")
                    for ritem in related_items:
                        print(">>>>", ritem.get("_id"), ritem.get("resourceType"), ritem.get("name"))
                        if self.add_node(ritem):
                            edge_from_id = self.get_item_node_id(item)
                            edge_to_id = self.get_item_node_id(ritem)
                            self.add_edge(edge_from_id, edge_to_id, f"{item_type}-[{rel[0]}]->{rel[1]}")

                    if depth < max_depth:
                        self.process_items(related_items, depth=depth+1, max_depth=max_depth)
            else:
                print("> no meta found for", item.get("resourceType"))
