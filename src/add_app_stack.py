# !/usr/bin/env python3
# compose-project-add.py
# Description: Functions to create and manage Docker Compose applications from templates or git repositories.
# App creation fails if the target directory already exists.
# The template can be a local directory, a git repository, or a URL to a zip/tar.gz archive.
import sys
from pathlib import Path

from mc.inventory.item.app_stack_helper import create_app_stack
from mc.inventory.items import create_inventory_item, read_inventory_item

# def _build_app_dir_path(stack_name: str, stack_name: str) -> str:
#     base_dir = Path(f"data/projects/{stack_name}/apps")
#     app_dir = base_dir / stack_name
#     return str(app_dir)

if __name__ == "__main__":
    # template_git_repo = "myuser/compose-templates"
    # template_git_branch = "main"
    # template_name = "basic"
    #
    # # the archive must contain the contents of the template at its root
    # # e.g. compose.yaml, .env, etc.
    # template_url = "https://example.com/path/to/compose-template.zip"
    #
    # git_repo = "myuser/myrepo"
    # git_branch = "main"
    #
    # stack_name = "my-project"
    #
    # unified app src url scheme:
    # - file://path/to/local/template
    # - git://user/repo.git#branch
    # - https://example.com/path/to/repo.git#branch
    # - https://example.com/path/to/template.zip (zip or tar.gz)
    # - git-template://user/repo.git#branch/template-name
    #
    # # a) create compose-project from template directory
    # create_app_stack_from_template_dir(stack_name="from-template-dir",
    #                              template_dir=template_dir)
    #
    # # b) checkout git repo into compose-project directory
    # create_app_stack_from_git_repo(stack_name="from-git-repo",
    #                                git_repo=git_repo, git_branch=git_branch)
    #
    # # c1) from a git repo
    # create_app_stack_from_git_repo_template(stack_name="from-git-template",
    #                                   template_git_repo=template_git_repo,
    #                                   template_git_branch=template_git_branch,
    #                                   stackfile="compose.yaml")
    #
    # # c2) from a folder in a git repo
    # create_app_stack_from_git_repo_template_folder(stack_name="from-git-template-folder",
    #                                   template_git_repo=template_git_repo,
    #                                   template_git_branch=template_git_branch,
    #                                   stackfile=f"{template_name}/compose.yaml")
    #
    # # d) download a template from a remote URL (zip/tar.gz)
    # create_app_stack_from_url_template(stack_name="from-template-archive",
    #                                    template_url=template_url)

    # read args from command line as src
    if len(sys.argv) < 4:
        print("Usage: python init-app-stack.py <stack-name> <src-url> <stackfile>")
        print("  stack-name: The name of the app stack to create")
        print("  src-url: file://path/to/local/template")
        print("       git://user/repo.git#branch")
        print("       https://github.com/fm-labs/mc.git#dev")
        print("       https://example.com/path/to/template.zip")
        print("       https://example.com/path/to/template.tar.gz")
        print("  stackfile: The path to the stackfile inside the repo (if applicable)")
        print("       e.g. 'basic/compose.yaml' or 'compose.yaml'")
        print("       Defaults to 'compose.yaml' if not specified.")
        sys.exit(1)

    stack_name = sys.argv[1]
    src_url = sys.argv[2]
    stackfile_path = sys.argv[3]

    # lookup in inventory if app with same name already exists
    app_stack = read_inventory_item("app_stack", src_url)
    if app_stack is not None:
        print(f"Error: app_stack with name '{src_url}' already exists in inventory.")
        sys.exit(1)

    # create compose app
    app_stack = create_app_stack(stack_name=stack_name, src=src_url, stackfile=stackfile_path)
    print(app_stack)

    # save to inventory
    create_inventory_item("app_stack", {"name": src_url, "properties": app_stack})
