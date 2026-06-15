FROM python:3.12-slim

ARG WITAN_PACKAGE=witan==0.12.0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "${WITAN_PACKAGE}" \
    && witan --version

COPY . /tests/
RUN chmod +x /tests/test.sh /tests/shared_test.sh

CMD ["/tests/test.sh"]
