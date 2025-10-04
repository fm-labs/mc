from kloudia.plugin.docker.tasks import deploy_template_to_container_host

def handle_container_host_deploy_template(item: dict, action_params: dict) -> dict:
    host_url = item.get("properties", {}).get("url")
    if not host_url:
        raise ValueError("Container host URL not found in item properties.")

    template_name = action_params.get("template_name")
    if not template_name:
        raise ValueError("Template name not provided in action parameters.")
    return deploy_template_to_container_host(host_url=host_url, template_name=template_name, template_args=action_params)



actions = {
    "deploy_template": handle_container_host_deploy_template,
}