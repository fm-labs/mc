from typing import List

from pydantic import BaseModel


class KloudiaAwsAccountModel(BaseModel):
    account_id: str
    regions: List[str]


class KloudiaGcpAccountModel(BaseModel):
    project_id: str
    regions: List[str]


class KloudiaAzureAccountModel(BaseModel):
    subscription_id: str
    regions: List[str]


class KloudiaCloudModel(BaseModel):
    name: str
    platform: str
    aws: KloudiaAwsAccountModel = None
    gcp: KloudiaGcpAccountModel = None
    azure: KloudiaAzureAccountModel = None
