import argparse
import getpass

from mc.config import RESOURCES_DIR
from orchestra.orchestra import ko_playbook_run

if __name__ == "__main__":
    # todos:
    # - parse command line argument
    # - connect via ssh to host with given credentials (privileged user)
    # - perform initial setup tasks (update packages, configure firewall, create users, etc.)
    #   -> ansible or bash scripts
    # - optional: create / update inventory item in db

    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="Target host for the playbook e.g. ssh://user@hostname")
    parser.add_argument("--check", action="store_true", help="Run in check mode")
    parser.add_argument("--become", action="store_true", help="Whether to use privilege escalation (become)")
    parser.add_argument("--become-user", help="Become user. Defaults to 'root'")
    parser.add_argument("--become-pass", action="store_true", help="Prompt become password")
    parser.add_argument("--port", help="Alternative SSH port", default="22")
    parser.add_argument("--key-path", help="SSH private key path", default="~/.ssh/id_rsa")
    parser.add_argument("--pub-key-path", help="The public key to be installed in the authorized_keys file of the unprivileged user")
    args = parser.parse_args()

    target = args.target
    if not target.startswith("ssh://"):
        raise ValueError("Target must start with ssh://")
    target = target[len("ssh://"):]
    if "@" in target:
        ssh_user, hostname = target.split("@", 1)
    else:
        raise ValueError("Target must be in the format ssh://user@hostname")

    check = args.check
    ssh_key_path = args.key_path
    ssh_port = args.port
    python_path = "/usr/bin/python3"
    ansible_become = "true" if args.become else "false"
    ansible_become_user = args.become_user if args.become_user else "root"
    ansible_become_password = ""
    if args.become_pass:
        ansible_become_password = getpass.getpass(prompt="Enter become password: ")

    ansible_host = {
            "ansible_connection": "ssh",
            "ansible_host": hostname,
            "ansible_user": ssh_user,
            "ansible_ssh_private_key_file": ssh_key_path,
            "ansible_port": ssh_port,
            "ansible_python_interpreter": python_path,
            "ansible_become": ansible_become,
            "ansible_become_user": ansible_become_user,
            "ansible_become_password": ansible_become_password,
        }

    extravars = {"target": hostname}
    if args.pub_key_path:
        with open(args.pub_key_path, "r") as f:
            pub_key_content = f.read().strip()
        extravars["deploy_pubkey"] = pub_key_content

    result = ko_playbook_run(
        project_path=f"{RESOURCES_DIR}/ansible",
        playbook=f"playbooks/baseline-deploy.yml",
        inventory={'project': {'hosts': {hostname: ansible_host}}},
        extravars=extravars,
        cmdline="--check" if check else "",
    )
    print(result)

