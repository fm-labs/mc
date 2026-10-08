# App Stacks


## App Stack Specification (Container)

```json
{
  "id": "my-redis-container",
  "type": "container",
  "label": "My Redis Container",
  "image": "redis:latest",
  "env": {
    "REDIS_ADMIN_USER": "",
    "REDIS_ADMIN_PASSWORD": ""
  },
  "ports": [
    "6379/tcp"
  ],
  "volumes": [
    {
      "name": "redis-data",
      "persistent": true,
      "container": "/data"
    }
  ],
  "networks": [
    "my-custom-network"
  ]
}
```



## App Stack Specification (Compose)

```json
{
  "id": "my-wordpress-stack",
  "type": "compose",
  "label": "My WordPress Stack",
  "repository": {
    "type": "git",
    "url": "https://github.com/fm-labs/mc-templates.git",
    "branch": "main",
    "composefile": "stacks/wordpress/compose.yaml",
    "private": false
  },
  "env": {
    "WP_ADMIN_USER": "",
    "WP_ADMIN_PASSWORD": ""
  },
  "ports": [
    "8080/tcp"
  ],
  "volumes": [
    {
      "name": "wp-data",
      "bind": "/opt/mc/volumes/my-wordpress-stack-wp-data",
      "persistent": true
    },
    {
      "name": "db-data",
      "persistent": true
    }
  ],
  "networks": [
    "my-custom-network"
  ],
  "domain": "my-wordpress-stack.local",
  "proxy": {
    "enabled": true,
    "network": "proxy-network",
    "http": false,
    "https": true
  },
  "routes": [
    {
      "serviceName": "wordpress",
      "containerPort": 8080
    }
  ],
  "template": "https://github.com/fm-labs/mc-launchpacks/blob/main/stacks/wordpress/template.json"
}
```

## App Stack Template Specification

Easy to use templates for popular app stacks.

```json
{
  "id": "wordpress-template",
  "type": "compose",
  "title": "WordPress Template",
  "description": "A template for a WordPress stack with a MySQL database.",
  "note": "",
  "categories": [
    "Blogging",
    "CMS"
  ],
  "platform": "linux",
  "logo": "",
  "repository": {
    "url": "https://github.com/fm-labs/mc-launchpacks",
    "stackfile": "stacks/wordpress/compose.yaml"
  },
  "env": [
    {
      "name": "WP_ADMIN_USER",
      "label": "WordPress admin username",
      "default": "admin"
    },
    {
      "name": "WP_ADMIN_PASSWORD",
      "label": "WordPress admin password",
      "secret": true
    }
  ],
  "ports": [
    "8080:8080/tcp"
  ],
  "volumes": [
    {
      "name": "wp-data",
      "persistent": true
    },
    {
      "name": "db-data",
      "persistent": true
    }
  ],
  "routes": [
    {
      "serviceName": "wordpress",
      "containerPort": 8080
    }
  ]
}
```


## Create new app stack with the CLI

```bash
mc app create my-wordpress-stack --template "http://url-to-template.json"

# configure
mc app configure my-wordpress-stack --env WP_ADMIN_USER=admin --env WP_ADMIN_PASSWORD=supersecretpassword
mc app configure my-wordpress-stack --port 8080:8080/tcp
mc app configure my-wordpress-stack --volume wp-data:/opt/mc/volumes/my-wordpress-stack-wp-data --persistent
mc app configure my-wordpress-stack --volume db-data --persistent
mc app configure my-wordpress-stack --network default
mc app configure my-wordpress-stack --domain my-wordpress-stack.local
mc app configure my-wordpress-stack --proxy --proxy-network default --proxy-http false --proxy-https true
mc app configure my-wordpress-stack --route wordpress:8080

# configure interactively (e.g. set environment variables)
mc app configure --interactive my-wordpress-stack

# dump current configuration to a JSON file
mc app inspect my-wordpress-stack --output json > my-wordpress-stack-config.json

# sync app repository (e.g. pull latest changes from the compose file)
mc app sync my-wordpress-stack

# deploy the stack
mc app deploy my-wordpress-stack

# view logs
mc app logs my-wordpress-stack

# stop the stack
mc app stop my-wordpress-stack

# remove the stack
mc app remove my-wordpress-stack
```