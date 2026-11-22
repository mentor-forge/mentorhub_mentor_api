#!/usr/bin/env sh
set -e

root=$(cd "$(dirname "$0")/.." && pwd)
image="${MENTOR_API_IMAGE:-ghcr.io/mentor-forge/mentorhub_mentor_api:latest}"
exec docker build -t "$image" -f "$root/Dockerfile" "$root"
