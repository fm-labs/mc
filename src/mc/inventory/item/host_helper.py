def host_item_to_ansible_host(host: dict, return_as: str = "dict") -> str | dict:
    """
    Convert a host inventory item to Ansible host format.

    :param host: Host inventory item dictionary.
    :param return_as: 'str' to return as Ansible inventory string, 'dict' to return as dictionary of Ansible variables.
    :return: Ansible host representation as string or dictionary.
    """
    props = host.get("properties", {})
    hostname = props.get("hostname")
    ip_address = props.get("ip_address", props.get("public_ip"))
    ssh_hostname = props.get("ssh_hostname", hostname)
    ssh_user = props.get("ssh_user", "")
    ssh_port = props.get("ssh_port", "22")

    ssh_key_path = props.get("ssh_key_path", "")  # deprecated
    ssh_key_name = props.get("ssh_key_name", "")
    if ssh_key_name:
        ssh_key_path = f"~/.ssh/{ssh_key_name}"

    python_path = props.get("pythonPath", "/usr/bin/python3")
    # ansible_become_method = props.get("ansible_become_method", "sudo")
    ansible_become_user = props.get("ansible_become_user", "root")
    ansible_become_password = props.get("ansible_become_password", "")
    ansible_become = props.get("ansible_become", "false")

    if return_as == "str":
        return f"{hostname} ansible_connection=ssh ansible_host={ssh_hostname} ansible_user={ssh_user} ansible_ssh_private_key_file={ssh_key_path} ansible_port={ssh_port} ansible_become={ansible_become} ansible_become_user={ansible_become_user} ansible_python_interpreter={python_path} \n"

    if return_as == "dict":
        return {
            "ansible_connection": "ssh",
            "ansible_host": ssh_hostname,
            "ansible_user": ssh_user,
            "ansible_ssh_private_key_file": ssh_key_path,
            "ansible_port": ssh_port,
            "ansible_python_interpreter": python_path,
            "ansible_become": ansible_become,
            "ansible_become_user": ansible_become_user,
            "ansible_become_password": ansible_become_password,
        }

    raise ValueError(f"Unsupported return_as {return_as} (must be 'str' or 'dict')")
