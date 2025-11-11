import os
from typing import List
import configparser

from mc import config
from mc.credentials import add_credentials


# from pydantic import BaseModel
#
#
# class KloudiaAwsAccountModel(BaseModel):
#     account_id: str
#     regions: List[str]
#
#
# class KloudiaGcpAccountModel(BaseModel):
#     project_id: str
#     regions: List[str]
#
#
# class KloudiaAzureAccountModel(BaseModel):
#     subscription_id: str
#     regions: List[str]
#
#
# class KloudiaCloudModel(BaseModel):
#     name: str
#     platform: str
#     aws: KloudiaAwsAccountModel | None = None
#     gcp: KloudiaGcpAccountModel | None = None
#     azure: KloudiaAzureAccountModel | None = None

def read_ini_file(file_path: str) -> configparser.ConfigParser:
    """
    Read an INI file and return a ConfigParser object.

    :param file_path: Path to the INI file.
    :return: ConfigParser object with the INI file contents.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        return config  # Return empty config if file does not exist

    with open(file_path, "r") as config_file:
        config.read_file(config_file)
    return config


def write_ini_file(file_path: str, config: configparser.ConfigParser) -> None:
    """
    Write a ConfigParser object to an INI file.

    :param file_path: Path to the INI file.
    :param config: ConfigParser object to write.
    """
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as config_file:
        config.write(config_file)


def update_ini_section(file_path: str, section: str, kv: dict) -> None:
    """
    Add a section to an INI file.

    :param file_path: Path to the INI file.
    :param section: Section name to add.
    :param kv: Key-value pairs to add under the section.
    """
    config = read_ini_file(file_path)
    if "section" in config:
        print(f"Section '{section}' already exists in {file_path}. Overwriting.")
    config[section] = kv
    write_ini_file(file_path, config)


def handle_cloud_configure_aws_profile(item: dict, action_params: dict) -> dict:
    """
    Handle AWS profile configuration.
    Writes AWS config to ~/.aws/config

    :param item: Item to configure.
    :param action_params: Action parameters.
    """
    item_name = item.get("name", "")
    cloud_provider = item.get("properties", {}).get("provider", "")
    account_id = item.get("properties", {}).get("account_id", "")
    if cloud_provider.lower() != "aws":
        raise Exception(f"Unsupported cloud provider: {cloud_provider}")
    if not account_id:
        raise Exception("Missing 'account_id' in item for AWS profile configuration.")

    aws_profile_name = f"cloud-profile-aws-{item_name}-{account_id}"
    aws_config_path = action_params.get("aws_config_path", "~/.aws/config")
    aws_config_path = os.path.expanduser(aws_config_path)

    aws_region = item.get("region", "us-east-1")
    aws_output = item.get("output", "json")
    section_name = f"profile {aws_profile_name}"
    kv = action_params
    kv.update({
        "region": aws_region,
        "output": aws_output,
    })
    # filter empty values
    kv = {k: v for k, v in kv.items() if v is not None and v != ""}
    update_ini_section(aws_config_path, section_name, kv)

    # add to credentials vault as well
    vault_file = f"{config.VAULT_FILE}.yaml"
    add_credentials(vault_file, aws_profile_name, kv)

    return {
        "status": "configured",
        "message": f"AWS profile '{aws_profile_name}' configured in {aws_config_path}.",
        "aws_profile": aws_profile_name,
    }



def handle_cloud_configure_aws_profile_sso(item: dict, action_params: dict) -> None:
    """
    Handle AWS SSO profile configuration.
    Writes AWS config to ~/.aws/config

    :param item: Item to configure.
    :param action_params: Action parameters.
    """
    pass


actions = {
    "configure_aws_profile": handle_cloud_configure_aws_profile,
    "configure_aws_profile_sso": handle_cloud_configure_aws_profile_sso,
}