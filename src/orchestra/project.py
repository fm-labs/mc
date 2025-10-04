import os

from orchestra.settings import PROJECTS_DATA_DIR


def list_projects():
    """
    List all projects in the projects data directory.
    Each project is a directory in the projects data directory.

    :return:
    """
    projects = []
    if os.path.exists(PROJECTS_DATA_DIR):
        for project in os.listdir(PROJECTS_DATA_DIR):
            project_path = os.path.join(PROJECTS_DATA_DIR, project)
            if os.path.isdir(project_path) and not project.startswith(".") and not project.startswith("_"):
                projects.append(project)
    return projects


def get_project_path(project: str):
    """
    Get the path to the project directory.
    :param project: str - name of the project
    :return: str - path to the project directory
    """
    project_path = os.path.join(PROJECTS_DATA_DIR, project)
    if not os.path.exists(project_path):
        raise Exception(f"Project {project} does not exist in {PROJECTS_DATA_DIR}")
    return project_path


