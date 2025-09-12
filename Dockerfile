FROM python:3.13.4-alpine3.22


RUN apk update && apk add --no-cache \
    openssh \
    bash \
    supervisor \
    docker-cli \
    git \
    curl


# Working directory
WORKDIR /app

# Install python dependencies
RUN pip install --no-cache-dir uv
COPY ./pyproject.toml ./uv.lock /app/
COPY ./libs /app/libs
RUN uv sync --no-cache-dir

# Copy the rest of the files
COPY ./src /app/src

# Supervisor
COPY ./docker/supervisor/supervisord.conf /etc/supervisord.conf
COPY ./docker/supervisor/celery_worker.ini ./docker/supervisor/celery_flower.ini ./docker/supervisor/api.ini /etc/supervisor.d/

# Set a non-root user
RUN addgroup -S app && \
    adduser -S app -G app && \
    adduser app root # to allow docker socket access

# Set file and directory permissions
RUN chown -R app:app /app && \
    mkdir -p /data && \
    chown app:app /data && \
    mkdir -p /var/log/supervisor && \
    chown -R app:app /var/log/supervisor && \
    chmod -R 755 /var/log/supervisor && \
    chown -R app:app /run


# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Entry point script
COPY docker/entrypoint.sh /entrypoint
RUN ["chmod", "+x", "/entrypoint"]
ENTRYPOINT ["/entrypoint"]

# Healthcheck
COPY docker/healthcheck.sh /usr/bin/healthcheck
RUN ["chmod", "+x", "/usr/bin/healthcheck"]
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
  CMD ["/usr/bin/healthcheck"]

CMD ["supervisor"]
USER app

# API port
EXPOSE 8000
# Flower port
EXPOSE 5555
