FROM python:3-alpine

LABEL org.opencontainers.image.title="apollonia: ingestor" \
      org.opencontainers.image.description="Ingests newly added files and pushes the data to AMQP." \
      org.opencontainers.image.authors="robert@simplicityguy.com" \
      org.opencontainers.image.source="https://github.com/SimplicityGuy/apollonia/blob/main/ingestor/Dockerfile" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.created="$(date +'%Y-%m-%d')" \
      org.opencontainers.image.base.name="docker.io/library/python:3-alpine"

RUN addgroup -S apollonia && \
    adduser -S apollonia -G apollonia

USER apollonia:apollonia

WORKDIR /app
VOLUME /data

COPY --chown=apollonia:apollonia . .

RUN pip install --upgrade --no-cache-dir --requirement requirements.txt

# format: amqp://user:pass@server:port
ENV AMQP_CONNECTION=""

CMD ["python3", "ingestor.py"]
