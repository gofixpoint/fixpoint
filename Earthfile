VERSION 0.7

pnpm-base-deps:
    FROM node:18-alpine
    WORKDIR /app

    RUN apk add --no-cache libc6-compat
    RUN corepack enable && corepack prepare pnpm@latest --activate
    RUN pnpm version


docs-base:
    FROM +pnpm-base-deps

    COPY ./docs/package.json ./docs/package.json
    COPY ./docs/pnpm-lock.yaml ./docs/pnpm-lock.yaml

    WORKDIR /app/docs
    RUN pnpm install

    SAVE ARTIFACT ./docs/node_modules


docs-build:
    FROM +docs-base

    WORKDIR /app
    COPY ./docs/ ./docs/
    WORKDIR /app/docs
    RUN pnpm build
    SAVE ARTIFACT ./.next
    SAVE ARTIFACT ./node_modules
    SAVE ARTIFACT ./package.json


docs:
    FROM +docs-base

    WORKDIR /app
    COPY +docs-build/.next ./.next
    COPY +docs-build/node_modules ./node_modules
    COPY +docs-build/package.json ./package.json

    EXPOSE 3000
    ENTRYPOINT ["pnpm", "run", "start"]

    ARG TAG=latest
    # GCP
    ARG IMAGE_REPO_BASE=us-central1-docker.pkg.dev/production-413901/fixpoint
    # AWS
    # ARG IMAGE_REPO_BASE=851725343267.dkr.ecr.us-east-2.amazonaws.com/fixpoint
    SAVE IMAGE --push $IMAGE_REPO_BASE/docs:$TAG
