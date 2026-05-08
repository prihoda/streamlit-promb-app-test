FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    openjdk-21-jdk \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L -o /tmp/miniforge.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh \
    && bash /tmp/miniforge.sh -b -p /opt/miniforge3
ENV PATH="/opt/miniforge3/bin:${PATH}"

COPY pyproject.toml .
COPY ovo_promb ovo_promb

RUN pip3 install .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "ovo_promb/demo.py", "--server.port=8501", "--server.address=0.0.0.0"]
