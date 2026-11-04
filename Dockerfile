ARG MC_VERSION=v2.4.3
ARG PYTHON_IMAGE=docker.io/library/python:3.14-alpine
ARG NODEJS_IMAGE=docker.io/library/node:25-alpine

## UI Build stage
FROM ${NODEJS_IMAGE} AS ui-builder
RUN npm install -g pnpm
WORKDIR /builder
COPY ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY ui/ .
RUN echo "VITE_FEAT_TOOLS_ENABLED=true" > .env
RUN pnpm run build


#FROM python:3.14-alpine AS builder
#WORKDIR /builder
#
## Install build dependencies for pyinstaller
#RUN apk add --no-cache \
#    bash \
#    build-base \
#    python3-dev
## Install uv
#COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
#
## Install python dependencies
#COPY ./pyproject.toml ./uv.lock /builder/
#RUN uv sync --no-cache-dir --frozen --no-install-project --no-dev
#
## Copy the rest of the files
#COPY ./src /builder/src
#COPY ./build_bin.sh /builder/build_bin.sh
#RUN ls -la /builder
#RUN mkdir -p ./build && mkdir -p ./dist && \
#    chmod +x /builder/build_bin.sh && \
#    bash /builder/build_bin.sh


FROM ${PYTHON_IMAGE} AS app-builder

# Install python dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1

WORKDIR /app
COPY ./pyproject.toml ./uv.lock /app/
RUN uv sync --no-cache-dir --no-dev --locked --no-install-project

# Copy the rest of the files
COPY ./src /app/src
RUN uv sync --no-cache-dir --no-dev --locked --no-editable


FROM ${PYTHON_IMAGE} AS final

RUN apk update  \
 && apk upgrade --no-cache \
 && python -m pip uninstall -y pip setuptools wheel py-urllib 2>/dev/null || true \
 && rm -rf /usr/local/bin/pip* \
           /usr/local/lib/python3.*/ensurepip \
           /root/.cache \
 && apk add --no-cache \
    file \
    bash \
    openssl \
    apache2-utils \
    supervisor \
    git \
    curl \
    rsync \
    iputils \
    nginx \
    ca-certificates \
    docker-cli \
    docker-cli-buildx \
    docker-compose \
    aws-cli \
    openssh-client \
    && rm -rf /var/cache/apk/*


# pre-create a directory for the SSH agent socket
#RUN mkdir -p /ssh-agent && chown -R app:app /ssh-agent
#ENV SSH_AUTH_SOCK=/ssh-agent/agent.sock

# Touch and own /var/run/podman.sock
#RUN touch /var/run/podman.sock && chown app:app /var/run/podman.sock

# Prepare /etc/ssh/ssh_config
#RUN echo "Host *\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile=/dev/null\n" >> /etc/ssh/ssh_config && \
#    chown app:app /etc/ssh/ssh_config && \
#    chmod 644 /etc/ssh/ssh_config

# Prepare /home/app/.ssh directory
#RUN mkdir -p /home/app/.ssh && chown -R app:app /home/app/.ssh && chmod 700 /home/app/.ssh


WORKDIR /app
COPY --from=app-builder --chown=app:app /app /app

# UI
COPY --from=ui-builder /builder/dist/ /app/ui

# Binaries
COPY ./container/bin/* /app/bin/
COPY ./scripts/* /app/bin/

# Nginx configuration
COPY ./container/nginx/site.default.conf /etc/nginx/http.d/default.conf
COPY ./container/nginx/site.ssl.conf /etc/nginx/http.d/ssl.conf

# Supervisor
COPY ./container/supervisord.conf /etc/supervisord.conf
COPY ./container/supervisor/* /etc/supervisor.d/

# Set a non-root user
RUN addgroup --gid 33333 -S app && \
    adduser --uid 33333 -S app -G app && \
    adduser app root # to allow docker socket access
    
# Set file and directory permissions
RUN mkdir -p /app && \
    chown -R app:app /app && \
    chmod +x /app/bin/* && \
    mkdir -p /mc && \
    mkdir -p /mc/etc && \
    mkdir -p /mc/stacks && \
    mkdir -p /mc/var && \
    chown -R app:app /mc && \
    mkdir -p /var/log/supervisor && \
    chown -R app:app /var/log/supervisor && \
    chmod -R 755 /var/log/supervisor && \
    chown -R app:app /run && \
    mkdir -p /etc/nginx/ssl/ && \
    mkdir -p /var/www/html/ && \
    mkdir -p /var/log/nginx/ && \
    mkdir -p /var/lib/nginx/logs && \
    touch /var/lib/nginx/logs/error.log && \
    touch /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx/logs/error.log && \
    chown -R app:app /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx /var/lib/nginx/logs /run/nginx /etc/nginx/ssl && \
    mkdir -p /ssh-agent && \
    chown app:app /ssh-agent

# Entry point script
COPY ./container/entrypoint.sh /usr/local/bin/entrypoint
RUN ["chmod", "+x", "/usr/local/bin/entrypoint"]
ENTRYPOINT ["/usr/local/bin/entrypoint"]

# Healthcheck
COPY ./container/healthcheck.sh /usr/local/bin/healthcheck
RUN ["chmod", "+x", "/usr/local/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/local/bin/healthcheck"]

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PATH=/app/.venv/bin:/app/bin:$PATH

ENV MC_ALPINE=1
ENV MC_DOCKER=1
ENV MC_HOME=/mc
ENV MC_CONFIG_DIR=/mc/etc
ENV MC_BIN_DIR=/app/bin
ENV MC_UI_HTML_DIR=/app/ui

CMD ["supervisor"]
USER app

# Nginx port
EXPOSE 3080
EXPOSE 3443
# API port
#EXPOSE 5000
# MCP port
#EXPOSE 5001
# Flower port
#EXPOSE 5555

LABEL org.opencontainers.image.vendor="fmlabs" \
    org.opencontainers.image.title="mission control 🚀" \
    org.opencontainers.image.description="Container orchestration tool" \
    org.opencontainers.image.version="${MC_VERSION}" \
    org.opencontainers.image.url="https://github.com/fm-labs/mc" \
    org.opencontainers.image.source="https://github.com/fm-labs/mc" \
    org.opencontainers.image.documentation="https://github.com/fm-labs/mc"
