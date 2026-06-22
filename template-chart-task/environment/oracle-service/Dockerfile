FROM python:3.12-slim

ARG WITAN_PACKAGE=witan==0.13.0

WORKDIR /srv/oracle

RUN pip install --no-cache-dir "${WITAN_PACKAGE}" pillow && witan --version

COPY tests/shared_oracle_runtime.py tests/oracle_task.py /srv/oracle/
COPY environment/oracle-service/shared_oracle_service.py /srv/oracle/shared_oracle_service.py

CMD ["python", "/srv/oracle/shared_oracle_service.py"]
