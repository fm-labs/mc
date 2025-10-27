FROM python:3.13.9-alpine3.22


RUN apk update && apk add --no-cache \
    openssh \
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
    libc-utils


# Supervisor
COPY ./container/supervisor/supervisord.conf /etc/supervisord.conf
COPY ./container/supervisor/celery_worker.ini ./container/supervisor/celery_flower.ini ./container/supervisor/api.ini ./container/supervisor/ssh-agent-keepalive.ini ./container/supervisor/scan.ini /etc/supervisor.d/

# Set a non-root user
RUN addgroup -S app && \
    adduser -S app -G app && \
    adduser app root # to allow docker socket access

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

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

CMD ["supervisor"]
USER app

# API port
EXPOSE 8000
# Flower port
EXPOSE 5555


# Metadata
LABEL org.opencontainers.image.vendor="fmlabs" \
    org.opencontainers.image.url="https://github.com/fm-labs/mc" \
    org.opencontainers.image.source="https://github.com/fm-labs/mc" \
    org.opencontainers.image.title="Mission Control" \
    org.opencontainers.image.description="Smart orchestration tool" \
    org.opencontainers.image.version="v0.1.0" \
    org.opencontainers.image.documentation="https://github.com/fm-labs/mc"