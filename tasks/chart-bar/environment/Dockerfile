FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates nodejs npm \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m agent \
    && mkdir -p /app /logs/artifacts \
    && chown -R agent:agent /app /logs

COPY shared_oracle_query.py /usr/local/bin/oracle-query
RUN chmod +x /usr/local/bin/oracle-query

ENV ORACLE_URL=http://oracle-service:8000/query
ENV PATH=/home/agent/.local/bin:/app/node_modules/.bin:$PATH
ENV PIP_USER=1

USER agent
