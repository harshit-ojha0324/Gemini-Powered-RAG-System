# syntax=docker/dockerfile:1

# Backend image for the Smart Document Q&A API.
#
# Two stages: "builder" installs the Python dependencies into a virtualenv,
# "runtime" copies only that virtualenv and the application code, so the
# compiler toolchain never reaches the final image.
#
# Keep PYTHON_VERSION in step with .github/workflows/ci.yml and pyrightconfig.json.
ARG PYTHON_VERSION=3.10
ARG DEBIAN_RELEASE=trixie

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE} AS builder

# Only needed for dependencies without a prebuilt wheel for the target platform
# (more likely on arm64 than amd64); it stays in this stage. Versions are left
# unpinned on purpose: Debian drops superseded versions from its mirrors, so pins
# break rebuilds, and nothing from this stage ships in the final image.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
COPY requirements.txt .

# The fallback embeddings run on CPU (device='cpu'), but the PyPI torch wheel
# for Linux pulls in several GB of CUDA libraries. Install the CPU-only builds of
# the pinned torch and torchvision first (they must come from the same index to
# be ABI-compatible); requirements.txt's "torch==X" is then already satisfied by
# "X+cpu". Pass --build-arg TORCH_INDEX_URL=https://pypi.org/simple to get the
# CUDA builds instead.
#
# --no-deps: take only these two wheels from the PyTorch index. Its mirrors of
# their dependencies (jinja2, typing-extensions, ...) fail pip's metadata checks,
# so those come from PyPI in the next install, and pip check confirms nothing
# was left out.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
# The $(grep ...) is unquoted on purpose: each pin becomes its own argument.
# hadolint ignore=SC2046
RUN pip install --no-deps --index-url "$TORCH_INDEX_URL" $(grep -E '^(torch|torchvision)==' requirements.txt) \
    && pip install -r requirements.txt \
    && pip check \
    && python -m spacy download en_core_web_lg


FROM python:${PYTHON_VERSION}-slim-${DEBIAN_RELEASE} AS runtime

# Fixed, non-root UID/GID. 1000 matches the usual first user on a Linux host, so
# the bind-mounted ./data in docker-compose.yml stays writable; override with
# --build-arg APP_UID=... if yours differs.
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid app --create-home --shell /usr/sbin/nologin app

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
# Code stays root-owned and read-only to the app user; only data/ is writable.
COPY . .
RUN mkdir -p data/documents data/vectorstore data/logs \
    && chown -R app:app data

USER ${APP_UID}:${APP_GID}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
