FROM python:3.12-slim as builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m venv /app/venv

RUN pip3 install --use-deprecated=legacy-resolver -r requirements.txt

FROM python:3.12-slim

WORKDIR /app/

ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=$PYTHONPATH:.

COPY ./ ./builder/
COPY --from=builder /app/venv /venv

ENV PYTHONPATH=$PYTHONPATH:.

CMD [ "python3", "-u", "/app/builder/main.py"]