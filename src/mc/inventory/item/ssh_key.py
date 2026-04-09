import os

from mc.config import DATA_DIR


def handle_ssh_key_action_set_content(item: dict, action_params: dict) -> dict:
    """
    Handle the 'set_content' action for an SSH key item.

    Args:
        item (dict): The SSH key item to update.
        content (str): The new content for the SSH key.

    Returns:
        dict: The updated SSH key item with the new content.
    """
    content = action_params.get("content", None)
    passphrase = action_params.get("passphrase", None) # todo - implement passphrase handling for encrypted keys
    if content is None:
        raise ValueError("Missing 'content' parameter for 'set_content' action")

    target_file_path = f"{DATA_DIR}/etc/ssh_keys/{item['id']}.pem"
    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
    with open(target_file_path, "w") as f:
        f.write(content)
    # Set file permissions to read/write for owner only
    os.chmod(target_file_path, 0o600)

    return {
        "status": "success",
        "message": f"SSH key content updated and saved to {target_file_path}",
    }

def handle_ssh_key_action_clear_content(item: dict, action_params: dict) -> dict:
    """
    Delete the SSH key item and its associated file.

    Args:
        item (dict): The SSH key item to delete.
    Returns:
        dict: An empty dictionary indicating successful deletion.
    """
    target_file_path = f"{DATA_DIR}/etc/ssh_keys/{item['id']}.pem"
    if os.path.exists(target_file_path):
        os.remove(target_file_path)

    return {
        "status": "success",
        "message": f"SSH key item and associated file deleted successfully.",
    }

actions = {
    "set_content": handle_ssh_key_action_set_content,
    "clear_content": handle_ssh_key_action_clear_content,
}