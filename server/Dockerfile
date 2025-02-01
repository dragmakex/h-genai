FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Install system dependencies
RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum install -y \
    gcc \
    gcc-c++ \
    python3-devel \
    cmake \
    git \
    wget \
    tar \
    gzip \
    make

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    cd /usr/local/bin && \
    ln -s /root/.local/bin/poetry

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies with specific settings for Lambda
RUN poetry config virtualenvs.create false && \
    pip install --no-cache-dir onnxruntime && \
    poetry install --no-root --without dev --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Set Python path and ensure logs aren't buffered
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}
ENV PYTHONUNBUFFERED=1

# Lambda handler
CMD [ "api.main.handler" ] 