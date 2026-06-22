FROM python:3.12-slim

WORKDIR /app

RUN useradd -m agent \
    && mkdir -p /app /logs/artifacts \
    && chown -R agent:agent /app /logs

COPY shared_oracle_query.py /usr/local/bin/oracle-query
RUN chmod +x /usr/local/bin/oracle-query

ENV ORACLE_URL=http://oracle-service:8000/query

USER agent
