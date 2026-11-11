FROM node:22-bookworm
COPY --from=golang:1.24-bookworm /usr/local/go /usr/local/go
ENV PATH=/usr/local/go/bin:$PATH
# hadolint ignore=DL3008
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pytest \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g @anthropic-ai/claude-code@2.1.322 @openai/codex@0.167.1 @moonshot-ai/kimi-code@2.5.2 \
 && npm cache clean --force
USER 1000
ENV HOME=/home/node
WORKDIR /work
