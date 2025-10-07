# !/usr/bin/env python3
# compose-app-add.py
# Description: Functions to create and manage Docker Compose applications from templates or git repositories.
# App creation fails if the target directory already exists.
# The template can be a local directory, a git repository, or a URL to a zip/tar.gz archive.
import sys
from pathlib import Path

from kloudia.apps.compose_app import create_compose_app
from kloudia.inventory.items import create_inventory_item, read_inventory_item


# def _build_app_dir_path(project_name: str, app_name: str) -> str:
#     base_dir = Path(f"data/projects/{project_name}/apps")
#     app_dir = base_dir / app_name
#     return str(app_dir)

if __name__ == "__main__":
    # template_git_repo = "myuser/compose-templates"
    # template_git_branch = "main"
    # template_name = "basic"
    # template_dir = f"resources/compose-templates/{template_name}"
    #
    # # the archive must contain the contents of the template at its root
    # # e.g. compose.yaml, .env, etc.
    # template_url = "https://example.com/path/to/compose-template.zip"
    #
    # git_repo = "myuser/myrepo"
    # git_branch = "main"
    #
    # project_name = "my-project"
    # app_name = "my-compose-app"
    # app_dir = f"data/projects/{project_name}/apps/{app_name}"

    # unified app src url scheme:
    # - file://path/to/local/template
    # - git://user/repo.git#branch
    # - https://example.com/path/to/repo.git#branch
    # - https://example.com/path/to/template.zip (zip or tar.gz)
    # - git-template://user/repo.git#branch/template-name

    # # a) create compose-app from template directory
    # create_compose_app_from_template_dir(app_name="from-template-dir",
    #                              app_dir=_build_app_dir_path(project_name, "from-template-dir"),
    #                              template_dir=template_dir)
    #
    # # b) checkout git repo into compose-app directory
    # create_compose_app_from_git_repo(app_name="from-git-repo",
    #                          app_dir=_build_app_dir_path(project_name, "from-git-repo"),
    #                          git_repo=git_repo, git_branch=git_branch)
    #
    # # c) checkout a template repo info temp dir and copy into compose-app directory
    # # c1) from a git repo
    # create_compose_app_from_git_repo_template(app_name="from-git-template",
    #                                   app_dir=_build_app_dir_path(project_name, "from-git-template"),
    #                                   template_git_repo=template_git_repo,
    #                                   template_git_branch=template_git_branch,
    #                                   template_name=template_name)
    # # c2) from a folder in a git repo
    # create_compose_app_from_git_repo_template_folder(app_name="from-git-template-folder",
    #                                          app_dir=_build_app_dir_path(project_name, "from-git-template-folder"),
    #                                          template_git_repo=template_git_repo,
    #                                          template_git_branch=template_git_branch,
    #                                          template_folder=f"resources/compose-templates/{template_name}")
    #
    # # d) download a template from a remote URL (zip/tar.gz)
    # create_compose_app_from_url_template(app_name="from-template-archive",
    #                              app_dir=_build_app_dir_path(project_name, "from-template-archive"),
    #                              template_url=template_url)

    # read args from command line as src
    if len(sys.argv) < 4:
        print("Usage: python compose-app-add.py <project_name> <app_name> <src>")
        print("  src: file://path/to/local/template")
        print("       git://user/repo.git#branch")
        print("       https://example.com/path/to/repo.git#branch")
        print("       https://example.com/path/to/template.zip (zip or tar.gz)")
        print("       git-template://user/repo.git#branch/template-name")
        sys.exit(1)

    project_name = sys.argv[1]
    app_name = sys.argv[2]
    src = sys.argv[3]

    # lookup in inventory if app with same name already exists
    compose_app = read_inventory_item("compose_app", app_name)
    if compose_app is not None:
        print(f"Error: compose_app with name '{app_name}' already exists in inventory.")
        sys.exit(1)

    # create compose app
    compose_app = create_compose_app(app_name=app_name, project_name=project_name, src=src)
    print(compose_app)

    # save to inventory
    create_inventory_item("compose_app", { "name": app_name, "properties": compose_app})

    print("Successfully created compose app and added to inventory.")
    print("You can now deploy it using the 'rx deploy' command.")
    print("e.g. to deploy to local docker-compose:")
    print(f"  rx deploy compose-app --name {app_name} --target local-docker-compose")
    # print("or to deploy to a remote server:")
    # print(f"  rx deploy compose-app --name {app_name} --target my-remote-server")
    print("or to deploy to cloud providers (requires credentials in environment variables):")
    print(f"  rx deploy compose-app --name {app_name} --target aws-ecs")
    print(f"  rx deploy compose-app --name {app_name} --target digitalocean-app-platform")
    print(f"  rx deploy compose-app --name {app_name} --target google-cloud-run")

