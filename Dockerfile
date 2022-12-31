# Build Go programs (only corrupter at the moment)
FROM golang:1-alpine AS go-build
RUN apk add --no-cache git

# Create a parent directory and set it as the working directory
RUN mkdir -p /caligo
WORKDIR /caligo

# Create a Go module and download the corrupter package
RUN go mod init github.com/vincreator/caligo && go mod download github.com/r00tman/corrupter

# Build and install the corrupter binary
RUN go install github.com/r00tman/corrupter

# Build Python package and dependencies
FROM python:3.9-alpine AS python-build
RUN apk add --no-cache \
        git \
        libffi-dev \
        musl-dev \
        gcc \
        g++ \
        make \
        zlib-dev \
        tiff-dev \
        freetype-dev \
        libpng-dev \
        libjpeg-turbo-dev \
        lcms2-dev \
        libwebp-dev \
        openssl-dev
RUN mkdir -p /opt/venv
WORKDIR /opt/venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir -p /src
WORKDIR /src

# Install bot package and dependencies
COPY . .
RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install aiohttp[speedups]
RUN pip install uvloop
RUN pip install .


# Package everything
FROM python:3.9-alpine AS final
# Update system first
RUN apk update

# Install optional native tools (for full functionality)
RUN apk add --no-cache \
        curl \
        neofetch \
        git \
        nss
# Install native dependencies
RUN apk add --no-cache \
        libffi \
        musl \
        gcc \
        g++ \
        make \
        tiff \
        freetype \
        libpng \
        libjpeg-turbo \
        lcms2 \
        libwebp \
        openssl \
        zlib \
        busybox \
        sqlite \
        libxml2 \
        libssh2 \
        ca-certificates \
        ffmpeg

# Create bot user
RUN adduser -D caligo

# Copy Go programs
COPY --from=go-build /go/bin/corrupter /usr/local/bin

# Copy Python venv
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=python-build /opt/venv /opt/venv

# Tell system that we run on container
ENV CONTAINER="True"

# Clone the repo so update works
RUN git clone https://github.com/adekmaulana/caligo /home/caligo
RUN chmod +x /home/caligo/bot
RUN cp /home/caligo/bot /usr/local/bin

# Download aria with sftp and gzip support
ARG ARIA2=aria2-1.36.0-r0.apk
RUN curl -LJO https://raw.githubusercontent.com/adekmaulana/docker/master/aria2/$ARIA2
RUN apk add --allow-untrusted --no-cache $ARIA2

# Certs for aria2 https websocket
RUN mkdir -p /home/caligo/.cache/caligo/.certs

# Initialize mkcert
RUN curl -LJO https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64
RUN mv mkcert-v1.4.3-linux-amd64 /usr/local/bin/mkcert
RUN chmod +x /usr/local/bin/mkcert

RUN mkcert -install
RUN mkcert -key-file /home/caligo/.cache/caligo/.certs/key.pem -cert-file /home/caligo/.cache/caligo/.certs/cert.pem localhost 127.0.0.1

# Change permission of home folder
RUN chown -hR caligo /home/caligo

# Set runtime settings
USER caligo
WORKDIR /home/caligo
CMD ["bash", "bot"]
