def list_projects_from_containers(containers):
    """
    List all projects from list of containers.

    :param containers: list of containers
    :return: list of project names
    """
    return list(
        set([c.attrs
            .get('Config', {})
            .get('Labels', {})
            .get('com.docker.compose.project') for c in containers]))


def filter_containers_by_project(containers, project_name):
    """
    Filter containers by project name.

    :param containers: list of containers
    :param project_name: str
    :return: list of containers
    """
    return [c for c in containers if c.attrs
    .get('Config', {})
    .get('Labels', {})
    .get('com.docker.compose.project') == project_name]


def filter_containers_by_status_text(containers, status):
    """
    Filter containers by status.

    :param containers: list of containers
    :param status: str
    :return: list of containers
    """
    return [c for c in containers if c.attrs.get('State', {}).get('Status') == status]
