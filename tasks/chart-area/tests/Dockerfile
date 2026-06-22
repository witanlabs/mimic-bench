FROM python:3.12-slim

ARG WITAN_PACKAGE=witan==0.13.0

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "${WITAN_PACKAGE}" pillow numpy scipy uv \
    && witan --version

COPY . /tests/
RUN chmod +x /tests/test.sh /tests/shared_test.sh

CMD ["/tests/test.sh"]
