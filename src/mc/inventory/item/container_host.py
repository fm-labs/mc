from pathlib import Path

from mc.apps.compose_app import create_compose_app_from_template_dir
from mc.config import RESOURCES_DIR
from mc.plugin.containers.tasks import deploy_compose_project_to_container_host

def handle_container_host_deploy_template(item: dict, action_params: dict) -> dict:
    host_url = item.get("properties", {}).get("url")

    if not host_url:
        raise ValueError("Container host URL not found in item properties.")

    template_name = action_params.get("template_name")
    if not template_name:
        raise ValueError("Template name not provided in action parameters.")

    project_name = action_params.get("project_name")
    if not project_name:
        raise ValueError("Project name not provided in action parameters.")

    app_name = action_params.get("app_name")
    if not app_name:
        raise ValueError("App name not provided in action parameters.")


    create_app = action_params.get("create_app", "false").lower() == "true"
    template_dir_path = Path(RESOURCES_DIR) / "compose-templates" / template_name

    if not create_app:
        if not template_dir_path.exists() or not template_dir_path.is_dir():
            raise FileNotFoundError(f"{template_dir_path} does not exist")

        return deploy_compose_project_to_container_host(host_url=host_url,
                                                        app_name=app_name, app_dir=template_dir_path.name)
    else:
        # the app dir is where the compose app will be created
        app_dir = Path(f"data/projects/{project_name}/apps/{app_name}")
        item = create_compose_app_from_template_dir(app_name=app_name,
                                             app_dir=app_dir.name,
                                             template_dir=template_dir_path.name)
        item.update({
            "project": project_name,
            "name": app_name,
        })

        return deploy_compose_project_to_container_host(host_url=host_url,
                                                        app_name=app_name, app_dir=app_dir.name)



actions = {
    "deploy_template": handle_container_host_deploy_template,
}