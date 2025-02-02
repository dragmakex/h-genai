# Build stage
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11 as builder

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Install only necessary build dependencies
RUN yum install -y \
    gcc \
    python3-devel \
    && yum clean all \
    && rm -rf /var/cache/yum

# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    cd /usr/local/bin && \
    ln -s /root/.local/bin/poetry

# Copy only dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main --no-interaction --no-ansi

# Final stage
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

# Install WeasyPrint dependencies
RUN yum install -y \
    pango \
    pango-devel \
    libffi-devel \
    cairo \
    cairo-devel \
    gobject-introspection-devel \
    harfbuzz-devel \
    && yum clean all \
    && rm -rf /var/cache/yum

# Copy Python dependencies from builder
COPY --from=builder /var/lang/lib/python3.11/site-packages/ /var/lang/lib/python3.11/site-packages/

# Copy only the API code
COPY ./api ./api

# Copy agent directory and its .env file
COPY ./agent ./agent
COPY ./agent/.env ./agent/.env

# Copy template directory
COPY ./template ./template

# Set environment variables
ENV PYTHONPATH=${LAMBDA_TASK_ROOT}
ENV PYTHONUNBUFFERED=1

# Lambda specific optimizations
ENV LAMBDA_RUNTIME_DIR=/var/runtime
ENV LAMBDA_TASK_ROOT=/var/task

# Lambda handler
CMD [ "api.main.handler" ] 