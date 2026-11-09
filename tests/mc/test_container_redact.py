from mc.plugin.containers.docker_helper import REDACTED_VALUE, redact_container_envvars


def test_redacts_secret_envvars():
    attrs = {
        "Id": "c1",
        "Config": {
            "Image": "postgres",
            "Env": [
                "POSTGRES_PASSWORD=hunter2",
                "DB_PASS=x",
                "AWS_SECRET_ACCESS_KEY=abc",
                "SSH_PRIVATE_KEY=-----BEGIN",
                "app_secret=lower",
                "SECRET=plain",
                "TOKEN_WITH=EQUALS=sign",
                "BYPASS=1",
                "PASSWORD_FILE=/run/secrets/pw",
                "PATH=/usr/bin",
                "NO_VALUE",
            ],
        },
    }
    result = redact_container_envvars(attrs)
    assert result["Config"]["Env"] == [
        f"POSTGRES_PASSWORD={REDACTED_VALUE}",
        f"DB_PASS={REDACTED_VALUE}",
        f"AWS_SECRET_ACCESS_KEY={REDACTED_VALUE}",
        f"SSH_PRIVATE_KEY={REDACTED_VALUE}",
        f"app_secret={REDACTED_VALUE}",
        f"SECRET={REDACTED_VALUE}",
        "TOKEN_WITH=EQUALS=sign",
        "BYPASS=1",
        "PASSWORD_FILE=/run/secrets/pw",
        "PATH=/usr/bin",
        "NO_VALUE",
    ]
    assert result["Config"]["Image"] == "postgres"
    # the input is not changed
    assert attrs["Config"]["Env"][0] == "POSTGRES_PASSWORD=hunter2"


def test_no_env():
    assert redact_container_envvars({"Id": "c1"}) == {"Id": "c1"}
    assert redact_container_envvars({"Config": None}) == {"Config": None}
    assert redact_container_envvars({"Config": {"Env": None}}) == {"Config": {"Env": None}}
