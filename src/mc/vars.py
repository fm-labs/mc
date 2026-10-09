import re

from mc.config import get_env_var
from mc.vault2 import vault_get_value


def replace_env_vars_in_string(s: str) -> str:
    """
    Replace ${VAR_NAME} in the string with the value of the environment variable VAR_NAME.
    Find all occurrences of ${VAR_NAME} and call get_env_var(VAR_NAME) to get the value, then replace it in the string.
    """
    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match):
        var_name = match.group(1)
        return get_env_var(var_name, "")

    return pattern.sub(replacer, s)


def replace_placeholders_in_string(s: str) -> str:
    """
    Replace ${{var.VAR_NAME}}, ${{env.VAR_NAME}} or ${{secret.SECRET_NAME}} in the string
    with the value of the environment variable VAR_NAME.
    Find all occurrences of ${{PREFIX.VAR_NAME}} and call get_placeholder_var(VAR_NAME) to get the value,
    then replace it in the string.
    """
    pattern = re.compile(r"\$\{\{(\w+\.\w+)\}\}")

    def replacer(match):
        var_name = match.group(1)
        return get_placeholder_var(var_name) or ""

    return pattern.sub(replacer, s)


def get_placeholder_var(name: str, default=None) -> str | None:
    """
    Placeholders are prefixed with 'env.', 'var.' or 'secret.' to indicate where to look for the value.
    For example, {{env.VAR_NAME}} will look for the environment variable VAR_NAME,
    {{var.VAR_NAME}} will look for a variable defined in the config file,
    and {{secret.VAR_NAME}} will look for a secret defined in the vault file.
    """
    prefix, name = name.strip().split(".", 1)
    prefix = prefix.lower()
    name = name.upper()

    if prefix == "env":
        # if "environment" in CONFIG and name in CONFIG["environment"]:
        #   return CONFIG["environment"][name]
        return get_env_var(name, default)
    if prefix == "var":
        # if "vars" in CONFIG and name in CONFIG["vars"]:
        #   return CONFIG["vars"][name]
        return get_inventory_var(name, default)
    if prefix == "secret":
        # if "secrets" in CONFIG and name in CONFIG["secrets"]:
        #   return CONFIG["secrets"][name]
        value = vault_get_value(name) or default
        if value is None:
            print(f"Warning: Secret variable {name} is not set in the vault and no default value provided.")
        return value

    print(f"Warning: unknown placeholder prefix '{prefix}' in variable '{name}', returning default value.")
    return default


def get_inventory_var(name: str, default=None) -> str | None:
    """
    Get a variable from the inventory db.
    """
    # storage = get_inventory_storage_instance()
    # item = storage.read("variable", id=name)
    # if item is not None:
    #    return item.get("value", default)

    print(f"Warning: unknown inventory variable '{name}', returning default value.")
    return default
