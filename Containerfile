## UI Build stage
FROM node:24-alpine AS ui-builder
RUN npm install -g pnpm
WORKDIR /builder
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY ui/ .
RUN pnpm run build


FROM python:3.14.3-slim

LABEL org.opencontainers.image.vendor="fmlabs" \
    org.opencontainers.image.title="mission control 🚀" \
    org.opencontainers.image.description="Smart orchestration tool" \
    org.opencontainers.image.version="v0.1.0" \
    org.opencontainers.image.url="https://github.com/fm-labs/mc" \
    org.opencontainers.image.source="https://github.com/fm-labs/mc" \
    org.opencontainers.image.documentation="https://github.com/fm-labs/mc"

# Environment variables
ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

ENV RESOURCES_DIR=/app/resources
ENV DATA_DIR=/opt/mc
ENV CONFIG_DIR=/opt/mc/etc

# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
#ENV UV_COMPILE_BYTECODE=1

# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install system dependencies
RUN apt update && apt install -yy \
    htop \
    procps \
    bash \
    curl \
    git \
    openssh-client \
    autossh \
    supervisor \
    nginx \
    podman \
    openssl \
    rsync \
    iputils-ping \
    ca-certificates \
    awscli \
    redis-server \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && . /etc/os-release \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $VERSION_CODENAME stable" \
      > /etc/apt/sources.list.d/docker.list \
    && apt update \
    && apt install -y --no-install-recommends \
      docker-ce-cli \
      docker-compose-plugin \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
#RUN pip install --no-cache-dir uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Working directory
WORKDIR /app

# Install python dependencies
COPY ./pyproject.toml ./uv.lock /app/
RUN uv sync --no-cache-dir --frozen --no-install-project

# Copy the rest of the files
COPY ./src /app/src
COPY ./resources /app/resources

# Entry point script
COPY ./container/entrypoint.sh /entrypoint
RUN ["chmod", "+x", "/entrypoint"]
ENTRYPOINT ["/entrypoint"]

# Healthcheck
COPY ./container/healthcheck.sh /usr/bin/healthcheck
RUN ["chmod", "+x", "/usr/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/bin/healthcheck"]

# Create a non-root user and group and set permissions for app and home directory
RUN groupadd --gid 33333 app && useradd --uid 33333 -g app app && \
    usermod -aG root app && \
    mkdir -p /app && \
    mkdir -p /home/app && \
    mkdir -p /var/log/supervisor && \
    mkdir -p /opt/mc && \
    chown -R app:app /app && \
    chown -R app:app /home/app && \
    chown -R app:app /var/log/supervisor && \
    chmod -R 755 /var/log/supervisor && \
    chown -R app:app /run && \
    chown app:app /opt/mc

# SSH - Prepare /etc/ssh/ssh_config
#RUN echo "Host *\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null\n" >> /etc/ssh/ssh_config && \
#    chown app:app /etc/ssh/ssh_config && \
#    chmod 644 /etc/ssh/ssh_config
RUN mkdir -p /home/app/.ssh && chown -R app:app /home/app/.ssh && chmod 700 /home/app/.ssh

# SSHAgent - pre-create a directory for the SSH agent socket
RUN mkdir -p /ssh-agent && chown -R app:app /ssh-agent
ENV SSH_AUTH_SOCK=/ssh-agent/agent.sock

# Supervisor
COPY ./container/supervisord.conf /etc/supervisord.conf
COPY ./container/supervisor/* /etc/supervisor.d/

# Nginx
COPY ./container/nginx/site.default.conf /etc/nginx/sites-available/default
RUN mkdir -p /etc/nginx/ssl/ && \
    mkdir -p /var/log/nginx/ && \
    mkdir -p /var/log/nginx && \
    chown -R app:app /var/lib/nginx /var/log/nginx

# Redis
RUN mkdir -p /redis && chown app:redis /redis
COPY ./container/redis/redis.conf /etc/redis/redis.conf
RUN chown app:redis /etc/redis/redis.conf
RUN usermod -aG redis app

# UI
# Copy from the builder stage and configure nginx
COPY --from=ui-builder /builder/dist/ /var/www/html/

CMD ["supervisor"]
USER app

# Nginx port
EXPOSE 3080
#EXPOSE 3443
# API port
#EXPOSE 5000
# Flower port
#EXPOSE 5555
