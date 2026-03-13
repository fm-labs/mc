import os

from mc.util.ini_util import update_ini_section


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
    #vault_file = f"{config.VAULT_FILE}.yaml"
    #add_credentials(vault_file, aws_profile_name, kv)

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