
from mc.config import SSH_CONFIG
from mc.inventory.storage import get_inventory_storage_instance


def dump_ssh_and_ansible_config():

    ssh_config_str = ""
    ssh_config_file = f"{SSH_CONFIG}"

    #ansible_hosts_str = ""
    #ansible_hosts_file = f"{DATA_DIR}/ansible_hosts"

    inv = get_inventory_storage_instance()
    hosts = inv.list_items("host")
    for host in hosts:
        props = host.get("properties", {})
        if not props.get("ssh_enabled", False):
            print(f"Skipping host {props.get('hostname', '')} - SSH not enabled")
            continue

        hostname = props.get("hostname", "")
        print(f"Configuring SSH for host: {props['hostname']} ({props['ip_address']})")

        ssh_key_name = props.get("ssh_key_name", "")
        ssh_key_file = ""
        if ssh_key_name:
            print(f"  Using SSH key from vault: {ssh_key_name}")
            ssh_key_file = f"~/.ssh/{ssh_key_name}"

        ssh_config = {
            "name": props["hostname"],
            "hostname": props.get("ssh_hostname", hostname),
            "ip_address": props["ip_address"],
            "port": props.get("ssh_port", 22),
            "username": props.get("ssh_user", ""),
            "key_file": ssh_key_file,
        }
        ssh_config_str += (
            f"\nHost {ssh_config['name']}\n"
            f"    HostName {ssh_config['hostname']}\n"
            f"    Port {ssh_config['port']}\n"
            f"    StrictHostKeyChecking no\n" # disable hostkey checking
            f"    UserKnownHostsFile /dev/null\n" # do not store hostkeys
        )
        if ssh_config["username"]:
            ssh_config_str += f"    User {ssh_config['username']}\n"
        if ssh_config["key_file"]:
            ssh_config_str += f"    IdentityFile {ssh_config['key_file']}\n"

        # ansible_config = {
        #     "ansible_host": ssh_config["ip_address"],
        #     "ansible_port": ssh_config["port"],
        #     "ansible_user": ssh_config["username"],
        #     "ansible_user_password": props.get("ssh_password", ""),
        #     "ansible_ssh_private_key_file": props.get("ssh_private_key_file", ""),
        #     "ansible_become": props.get("ssh_become", False),
        #     "ansible_become_method": props.get("ssh_become_method", "sudo"),
        #     "ansible_become_user": props.get("ssh_become_user", "root"),
        #     "ansible_become_password": props.get("ssh_become_password", ""),
        # }

    # add default ssh config
    ssh_config_str += (
        f"\nHost *\n"
        #f"    AddKeysToAgent yes\n"
        #f"    IdentityFile ~/.ssh/id_rsa\n"
        #f"    IdentitiesOnly yes\n"
        #f"    PreferredAuthentications publickey,password\n"
        #f"    AddressFamily inet\n"
        #f"    Protocol 2\n"
        #f"    Compression yes\n"
        #f"    ForwardAgent no\n"
        #f"    ServerAliveInterval 60\n"
        #f"    ServerAliveCountMax 5\n"
        f"    StrictHostKeyChecking no\n"
        f"    UserKnownHostsFile /dev/null\n"
        #f"    LogLevel INFO\n"
    )

    # write ssh config file
    with open(ssh_config_file, "w") as f:
        f.write(ssh_config_str)
    print(f"SSH config written to {ssh_config_file}")

    # write ansible hosts file
    #with open(ansible_hosts_file, "w") as f:
    #    f.write(ansible_hosts_str)
    #print(f"Ansible hosts file written to {ansible_hosts_file}")
