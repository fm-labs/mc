## UI Build stage
FROM node:24-alpine AS ui-builder
RUN npm install -g bun
WORKDIR /builder
COPY ui/package.json ui/bun.lock ./
RUN bun install --frozen-lockfile
COPY ui/ .
RUN bun run build


FROM python:3.13.11-alpine3.23 AS final

LABEL org.opencontainers.image.vendor="fmlabs" \
    org.opencontainers.image.title="mission control 🚀" \
    org.opencontainers.image.description="Smart orchestration tool" \
    org.opencontainers.image.version="v0.1.0" \
    org.opencontainers.image.url="https://github.com/fm-labs/mc" \
    org.opencontainers.image.source="https://github.com/fm-labs/mc" \
    org.opencontainers.image.documentation="https://github.com/fm-labs/mc"


# Set a non-root user
RUN addgroup -S app && \
    adduser -S app -G app && \
    adduser app root # to allow docker socket access


RUN apk update && apk add --no-cache \
    file \
    openssh \
    autossh \
    bash \
    supervisor \
    docker-cli \
    docker-compose \
    podman \
    openssl \
    git \
    curl \
    rsync \
    iputils \
    libc-utils \
    nginx \
    aws-cli \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Install the MCP Gateway CLI (docker-mcp) to the Docker plugin path
RUN mkdir -p /home/app/.docker/cli-plugins \
 && curl -fL -o /tmp/docker-mcp.tar.gz \
      https://github.com/docker/mcp-gateway/releases/download/v0.30.0/docker-mcp-linux-amd64.tar.gz \
 && tar -xzf /tmp/docker-mcp.tar.gz -C /home/app/.docker/cli-plugins/ \
 && chmod +x /home/app/.docker/cli-plugins/docker-mcp \
 && rm /tmp/docker-mcp.tar.gz


# Little hack to add user to docker group
# Add user to docker group (gid = 999)
# on alpine the group is 'ping' with gid 999
RUN adduser app ping


# Set file and directory permissions
RUN mkdir -p /app && mkdir -p /app/config && chown -R app:app /app && \
    mkdir -p /data && \
    chown app:app /data && \
    mkdir -p /var/log/supervisor && \
    chown -R app:app /var/log/supervisor && \
    chmod -R 755 /var/log/supervisor && \
    chown -R app:app /run

# pre-create a directory for the SSH agent socket
RUN mkdir -p /ssh-agent && chown -R app:app /ssh-agent
ENV SSH_AUTH_SOCK=/ssh-agent/agent.sock

# Working directory
WORKDIR /app

# Install python dependencies
RUN pip install --no-cache-dir uv
COPY ./pyproject.toml ./uv.lock /app/
COPY ./libs /app/libs
RUN uv sync --no-cache-dir

# Copy the rest of the files
COPY ./src /app/src
COPY ./resources /app/resources

RUN chown -R app:app /app


# Entry point script
COPY ./container/entrypoint.sh /entrypoint
RUN ["chmod", "+x", "/entrypoint"]
ENTRYPOINT ["/entrypoint"]

# Healthcheck
COPY ./container/healthcheck.sh /usr/bin/healthcheck
RUN ["chmod", "+x", "/usr/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/bin/healthcheck"]


# Touch and own /var/run/podman.sock
RUN touch /var/run/podman.sock && chown app:app /var/run/podman.sock

# Prepare /etc/ssh/ssh_config
RUN echo "Host *\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null\n" >> /etc/ssh/ssh_config && \
    chown app:app /etc/ssh/ssh_config && \
    chmod 644 /etc/ssh/ssh_config

# Prepare /home/app/.ssh directory
RUN mkdir -p /home/app/.ssh && chown -R app:app /home/app/.ssh && chmod 700 /home/app/.ssh

# UI
# Copy from the builder stage and configure nginx
COPY --from=ui-builder /builder/dist/ /var/www/html/
COPY ./container/nginx/site.default.conf /etc/nginx/http.d/default.conf


# Supervisor
COPY ./container/supervisord.conf /etc/supervisord.conf
COPY ./container/supervisor/* /etc/supervisor.d/

# Change ownership to non-root user
RUN mkdir -p /etc/nginx/ssl/ && \
    mkdir -p /var/log/nginx/ && \
    mkdir -p /var/lib/nginx/logs && \
    touch /var/lib/nginx/logs/error.log && \
    touch /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx/logs/error.log && \
    chown -R app:app /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx /var/lib/nginx/logs /run/nginx


# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

ENV CONFIG_DIR=/app/config
ENV RESOURCES_DIR=/app/resources
ENV DATA_DIR=/data

CMD ["supervisor"]
USER app

# Nginx port
EXPOSE 80
# API port
EXPOSE 5000
# Flower port
EXPOSE 5555

