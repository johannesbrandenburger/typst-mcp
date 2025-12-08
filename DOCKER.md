# Docker

This project uses a multi-stage Docker build system with a base image containing pre-compiled Typst documentation for faster builds.

## Quick Start

```bash
# Pull and run the pre-built image
docker run --rm -i ghcr.io/johannesbrandenburger/typst-mcp:latest
```

## Building

### Using the build script

```bash
# Build both base and runtime images
./build.sh

# Build only runtime image (for code changes)
./build.sh runtime

# Build only base image (when docs change)
./build.sh base

# Run the container
./build.sh run
```

### Manual build

```bash
# Build base image with Typst documentation
docker build -f Dockerfile.base -t ghcr.io/johannesbrandenburger/typst-mcp-base:latest .

# Build runtime image
docker build -f Dockerfile.runtime -t ghcr.io/johannesbrandenburger/typst-mcp:latest .
```

## Docker Compose

```yaml
version: '3.8'
services:
  typst-mcp:
    image: ghcr.io/johannesbrandenburger/typst-mcp:latest
    stdin_open: true
    tty: false
    restart: unless-stopped
```

## Architecture

- **Base image**: Contains pre-compiled Typst documentation (built from Rust nightly)
- **Runtime image**: Contains the MCP server (built from Python slim, uses base image)

The base image only needs rebuilding when Typst documentation changes, making runtime builds much faster.