# Stage 1: Build - install locked dependencies and compile
FROM python:3.12-slim AS build

WORKDIR /app

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv requirements --hash > requirements.txt && \
    pip install --no-cache-dir --require-hashes -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY src/ ./src/
COPY docs/ ./docs/

RUN python -m compileall -b -f -q src/

# Stage 2: Production - no tokens; copy installed packages from build
FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/mentor-forge/mentorhub_mentor_api"

WORKDIR /opt/api_server

COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app/src/ ./src/
COPY --from=build /app/docs/ ./docs/
ARG BUILT_AT=LOCAL
RUN printf '%s\n' "$BUILT_AT" > BUILT_AT

ENV PYTHONPATH=/opt/api_server
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8391

CMD exec python -m gunicorn --bind 0.0.0.0:8391 src.server:app
