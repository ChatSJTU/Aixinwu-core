FROM mcr.microsoft.com/devcontainers/python:3.9

ENV PYTHONUNBUFFERED 1
RUN sed -i "s/http:\/\/deb.debian.org/https:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list.d/debian.sources
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN apt-get update \
  && apt-get install -y \
  libcairo2 \
  libgdk-pixbuf2.0-0 \
  liblcms2-2 \
  libopenjp2-7 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libssl3 \
  libtiff6 \
  libwebp7 \
  libxml2 \
  libpq5 \
  shared-mime-info \
  mime-support

RUN echo 'image/webp webp' >> /etc/mime.types
RUN echo 'image/avif avif' >> /etc/mime.types

WORKDIR /app
RUN pip install poetry==1.7.0
RUN poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml /app/
RUN poetry source add --priority=default mirrors https://pypi.tuna.tsinghua.edu.cn/simple/
RUN poetry install --no-root
