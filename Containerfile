FROM python:3.13.4-alpine3.22


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
COPY ./docker/supervisor/supervisord.conf /etc/supervisord.conf
COPY ./docker/supervisor/celery_worker.ini ./docker/supervisor/celery_flower.ini ./docker/supervisor/api.ini ./docker/supervisor/ssh-agent-keepalive.ini ./docker/supervisor/scan.ini /etc/supervisor.d/

# Set a non-root user
RUN addgroup -S app && \
    adduser -S app -G app && \
    adduser app root # to allow docker socket access

# Little hack to add user to docker group
# Add user to docker group (gid = 999)
# on alpine the group is 'ping' with gid 999
RUN adduser app ping

# Set file and directory permissions
RUN mkdir -p /app && chown -R app:app /app && \
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
COPY docker/entrypoint.sh /entrypoint
RUN ["chmod", "+x", "/entrypoint"]
ENTRYPOINT ["/entrypoint"]

# Healthcheck
COPY docker/healthcheck.sh /usr/bin/healthcheck
RUN ["chmod", "+x", "/usr/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/bin/healthcheck"]


# Touch and own /var/run/podman.sock
RUN touch /var/run/podman.sock && chown app:app /var/run/podman.sock



# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

CMD ["supervisor"]
USER app

# API port
EXPOSE 8000
# Flower port
EXPOSE 5555
