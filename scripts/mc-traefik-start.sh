#!/bin/bash

set -euax

MC_HOME=$(realpath "${MC_HOME:?MC_HOME is required}")
if [ ! -d "${MC_HOME}" ]; then
   echo "MC_HOME directory does not exist: ${MC_HOME}"
   exit 1
fi

mkdir -p ${MC_HOME}/etc/traefik
mkdir -p ${MC_HOME}/etc/traefik/dynamic
TRAEFIK_DIR="${MC_HOME}/etc/traefik"

TRAEFIK_DASHBOARD_ADMIN_USER=${TRAEFIK_DASHBOARD_ADMIN_USER:-admin}
TRAEFIK_DASHBOARD_ADMIN_PASSWORD=${TRAEFIK_DASHBOARD_ADMIN_PASSWORD:-$(openssl rand -base64 12)}

# create traefik config
cat > "${TRAEFIK_DIR}/traefik.yml" << 'EOF'
# Traefik static configuration
# Mounted at /etc/traefik/traefik.yml (Traefik's default lookup path, no CLI args needed)

api:
  dashboard: false
  insecure: false

providers:
  docker:
    endpoint: "tcp://socket-proxy:2375"
    exposedByDefault: false
    network: traefik
  file:
    directory: /etc/traefik/dynamic
    watch: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"
    http:
      middlewares:
        - security-headers@file

certificatesResolvers:
  le:
    acme:
      email: acme@example.org
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

accessLog:
  format: common

log:
  level: INFO
  format: common
  noColor: true
EOF


# create traefik dynamic middleware config
cat > "${TRAEFIK_DIR}/dynamic/middleware.yml" << 'EOF'
# Traefik dynamic configuration (file provider)
# Mounted at /etc/traefik/dynamic/middlewares.yml

http:
  middlewares:
    security-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        frameDeny: true
        contentTypeNosniff: true
        referrerPolicy: no-referrer
        customResponseHeaders:
          Server: ""          # empty value = strip header
          X-Powered-By: ""
          # Permissions-Policy: "geolocation=(), microphone=()"
        # contentSecurityPolicy: "default-src 'self';"

    admin-auth:
      basicAuth:
        usersFile: /etc/traefik/users.htpasswd

EOF


# create users.htpasswd
if [[ ! -f "${TRAEFIK_DIR}/users.htpasswd" ]]; then
  randpw=$(openssl rand -base64 12)
  htpasswd -nbB admin "$randpw" > "${TRAEFIK_DIR}/users.htpasswd"
  echo "Generated random password for admin: $randpw"
  echo "!!! Change the password immediately !!!"
fi

docker container stop mc-traefik || true
docker container rm mc-traefik || true

docker network create traefik 2>/dev/null || true
docker volume create mc_traefik_letsencrypt

#exec docker container run -d \
#  --name mc-traefik \
#  --restart unless-stopped \
#  --network traefik \
#  -p 80:80 \
#  -p 443:443 \
#  -v mc_traefik_letsencrypt:/letsencrypt \
#  -v "${TRAEFIK_DIR}/traefik.yml:/etc/traefik/traefik.yml:ro" \
#  -v "${TRAEFIK_DIR}/dynamic:/etc/traefik/dynamic:ro" \
#  -v "${TRAEFIK_DIR}/users.htpasswd:/etc/traefik/users.htpasswd:ro" \
#  traefik:v3.6.2


exec docker run -d \
  --name mc-traefik \
  --restart unless-stopped \
  --network traefik \
  -p 80:80 \
  -p 443:443 \
  -p 8080:8080 \
  -v mc_traefik_letsencrypt:/letsencrypt \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -l traefik.enable=true \
  -l traefik.docker.network=traefik \
  -l "traefik.http.middlewares.admin-auth.basicauth.users=${TRAEFIK_DASHBOARD_ADMIN_USER:?Variable not set}:${TRAEFIK_DASHBOARD_ADMIN_PASSWORD:?Variable not set}" \
  -l "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000" \
  -l "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true" \
  -l "traefik.http.middlewares.security-headers.headers.stsPreload=true" \
  -l "traefik.http.middlewares.security-headers.headers.frameDeny=true" \
  -l "traefik.http.middlewares.security-headers.headers.contentTypeNosniff=true" \
  -l "traefik.http.middlewares.security-headers.headers.referrerPolicy=no-referrer" \
  -l "traefik.http.middlewares.security-headers.headers.customResponseHeaders.Server=" \
  -l "traefik.http.middlewares.security-headers.headers.customResponseHeaders.X-Powered-By=" \
  "traefik:${TRAEFIK_VERSION:-v3.6.2}" \
  --api \
  --api.dashboard="${TRAEFIK_DASHBOARD_ENABLED:-false}" \
  --api.insecure="${TRAEFIK_DASHBOARD_INSECURE:-false}" \
  --providers.docker \
  --providers.docker.exposedbydefault=false \
  --providers.docker.endpoint=${DOCKER_HOST:-unix:///var/run/docker.sock} \
  --entrypoints.web.address=:80 \
  --entrypoints.web.http.redirections.entryPoint.to=websecure \
  --entrypoints.web.http.redirections.entryPoint.scheme=https \
  --entrypoints.web.http.redirections.entryPoint.permanent=true \
  --entrypoints.websecure.address=:443 \
  --entrypoints.websecure.http.middlewares=security-headers@docker \
  --certificatesresolvers.le.acme.email="${TRAEFIK_LETSENCRYPT_EMAIL:-acme@example.org}" \
  --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json \
  --certificatesresolvers.le.acme.httpchallenge.entrypoint=web \
  --accesslog=true \
  --accesslog.format=common \
  --log \
  --log.level="${TRAEFIK_LOG_LEVEL:-INFO}" \
  --log.format=common \
  --log.nocolor=true