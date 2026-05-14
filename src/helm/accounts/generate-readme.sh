#!/usr/bin/env bash

if ! docker image ls | grep readme-generator-for-helm; then
  git clone https://github.com/bitnami/readme-generator-for-helm.git /tmp/readme-generator-for-helm
  cd /tmp/readme-generator-for-helm || exit
  docker build -t readme-generator-for-helm:latest .
  cd $(dirname -- "${BASH_SOURCE[0]}") || exit
fi
docker run --rm -it -v .:/source -w /source readme-generator-for-helm:latest readme-generator -v values.yaml -r README.md
