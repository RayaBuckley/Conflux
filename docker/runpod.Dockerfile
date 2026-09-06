FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/.cache/huggingface

RUN apt-get update -qq && apt-get install -y -qq \
    software-properties-common \
    git curl wget vim \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update -qq && apt-get install -y -qq \
    python3.12 python3.12-venv python3.12-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip

WORKDIR /workspace/conflux

COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY src/ src/
COPY schemas/ schemas/
COPY research/experiments/suites/ research/experiments/suites/
COPY tests/ tests/
COPY scripts/ scripts/
COPY docs/ docs/

RUN pip install -e ".[dev,agentdojo,local-model,verification,openai-compatible]" \
    && pip install bitsandbytes

RUN echo "source /opt/venv/bin/activate" >> /root/.bashrc

CMD ["bash"]
