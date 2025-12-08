#!/bin/bash

# Typst MCP Docker Build Script
# This script helps build the base and runtime images separately

set -e

# Allow custom registry via environment variable
REGISTRY="${TYPST_MCP_REGISTRY:-ghcr.io/johannesbrandenburger/typst-mcp}"

echo "🏗️  Typst MCP Docker Build Script"
echo "================================="

# Function to build base image
build_base() {
    echo "📚 Building base image with Typst documentation..."
    docker build -f Dockerfile.base -t ${REGISTRY}-base:latest .
    echo "✅ Base image built successfully!"
}

# Function to build runtime image
build_runtime() {
    echo "🚀 Building runtime image..."
    docker build -f Dockerfile.runtime --build-arg BASE_IMAGE=${REGISTRY}-base:latest -t ${REGISTRY}:latest .
    echo "✅ Runtime image built successfully!"
}

# Function to build both images
build_all() {
    echo "🏗️  Building both base and runtime images..."
    build_base
    build_runtime
}

# Function to push images
push_images() {
    echo "📤 Pushing images to registry..."
    docker push ${REGISTRY}-base:latest
    docker push ${REGISTRY}:latest
    echo "✅ Images pushed successfully!"
}

# Function to run the container
run_container() {
    echo "🏃 Running Typst MCP container..."
    docker run --rm -i ${REGISTRY}:latest
}

# Function to show help
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  base     - Build only the base image with Typst docs"
    echo "  runtime  - Build only the runtime image"
    echo "  all      - Build both base and runtime images (default)"
    echo "  push     - Push both images to registry"
    echo "  run      - Run the Typst MCP container"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Build both images"
    echo "  $0 base         # Build only base image"
    echo "  $0 runtime      # Build only runtime image"
    echo "  $0 push         # Push images to registry"
    echo "  $0 run          # Run the container"
}

# Main script logic
case "${1:-all}" in
    "base")
        build_base
        ;;
    "runtime")
        build_runtime
        ;;
    "all")
        build_all
        ;;
    "push")
        push_images
        ;;
    "run")
        run_container
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac