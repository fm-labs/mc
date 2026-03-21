## UI Build stage
FROM docker.io/library/node:25-alpine AS ui-builder
RUN npm install -g pnpm
WORKDIR /builder
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY ui/ .
RUN pnpm run build


FROM python:3.14-alpine AS builder
WORKDIR /builder

# Install build dependencies for pyinstaller
RUN apk add --no-cache \
    bash \
    build-base \
    python3-dev
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install python dependencies
COPY ./pyproject.toml ./uv.lock /builder/
RUN uv sync --no-cache-dir --frozen --no-install-project --no-dev

# Copy the rest of the files
COPY ./src /builder/src
COPY ./build_bin.sh /builder/build_bin.sh
RUN ls -la /builder
RUN mkdir -p ./build && mkdir -p ./dist && \
    chmod +x /builder/build_bin.sh && \
    bash /builder/build_bin.sh


FROM alpine:3.23

LABEL org.opencontainers.image.vendor="fmlabs" \
    org.opencontainers.image.title="mission control 🚀" \
    org.opencontainers.image.description="Container orchestration tool" \
    org.opencontainers.image.version="v2.0.0" \
    org.opencontainers.image.url="https://github.com/fm-labs/mc" \
    org.opencontainers.image.source="https://github.com/fm-labs/mc" \
    org.opencontainers.image.documentation="https://github.com/fm-labs/mc"


# Set a non-root user
RUN addgroup --gid 33333 -S app && \
    adduser --uid 33333 -S app -G app && \
    adduser app root # to allow docker socket access


RUN apk update && apk add --no-cache \
    file \
    bash \
    supervisor \
    git \
    curl \
    rsync \
    iputils \
    nginx \
    ca-certificates \
    docker-cli \
    docker-compose \
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

# Copy binaries
COPY --from=builder /builder/dist/bin/* /usr/bin/
COPY ./resources /app/resources

# UI
COPY --from=ui-builder /builder/dist/ /var/www/html/

# Nginx configuration
COPY ./container/nginx/site.default.conf /etc/nginx/http.d/default.conf

# Supervisor
COPY ./container/supervisord.conf /etc/supervisord.conf
COPY ./container/supervisor/* /etc/supervisor.d/

# Set file and directory permissions
RUN mkdir -p /app && \
    mkdir -p /app/config && \
    chown -R app:app /app && \
    mkdir -p /opt/mc && \
    chown -R app:app /opt/mc && \
    mkdir -p /var/log/supervisor && \
    chown -R app:app /var/log/supervisor && \
    chmod -R 755 /var/log/supervisor && \
    chown -R app:app /run && \
    mkdir -p /etc/nginx/ssl/ && \
    mkdir -p /var/log/nginx/ && \
    mkdir -p /var/lib/nginx/logs && \
    touch /var/lib/nginx/logs/error.log && \
    touch /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx/logs/error.log && \
    chown -R app:app /var/lib/nginx/logs/access.log && \
    chown -R app:app /var/lib/nginx /var/lib/nginx/logs /run/nginx /etc/nginx/ssl && \
    chmod +x /usr/bin/*


# Entry point script
COPY ./container/entrypoint.sh /usr/bin/entrypoint
RUN ["chmod", "+x", "/usr/bin/entrypoint"]
ENTRYPOINT ["/usr/bin/entrypoint"]

# Healthcheck
COPY ./container/healthcheck.sh /usr/bin/healthcheck
RUN ["chmod", "+x", "/usr/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/bin/healthcheck"]

# Environment variables
ENV MC_ALPINE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

ENV RESOURCES_DIR=/app/resources
ENV DATA_DIR=/opt/mc
ENV CONFIG_DIR=/opt/mc/etc

CMD ["supervisor"]
USER app

# Nginx port
EXPOSE 3080
EXPOSE 3443
# API port
#EXPOSE 5000
# Flower port
#EXPOSE 5555

