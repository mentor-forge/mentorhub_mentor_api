# Stage 1: Build - install deps (needs git + GITHUB_TOKEN for private api-utils) and compile
FROM python:3.12-slim AS build

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./

ARG GITHUB_TOKEN
RUN git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" && \
    pipenv install --deploy --system && \
    pip install --no-cache-dir gunicorn

COPY src/ ./src/
COPY docs/ ./docs/

RUN DATE=$(date +'%Y%m%d-%H%M%S') && echo "${DATE}" > /app/BUILT_AT
RUN pipenv run build

# Stage 2: Production - no git, no token; copy installed packages from build
FROM python:3.12-slim

LABEL org.opencontainers.image.source="{{org.git_host}}/{{org.git_org}}/{{info.slug}}_{{service.name}}_api"

WORKDIR /opt/api_server

COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app/src/ ./src/
COPY --from=build /app/docs/ ./docs/
COPY --from=build /app/BUILT_AT ./

ENV PYTHONPATH=/opt/api_server
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE {{repo.port}}

CMD exec python -m gunicorn --bind 0.0.0.0:{{repo.port}} src.server:app