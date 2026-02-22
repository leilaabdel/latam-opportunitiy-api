#!/bin/bash
# Import Docker images from GitHub Release tar.gz
# Usage: ./scripts/import-images.sh [latam-salesforce-api-bundle.tar.gz]
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Find the most recent matching archive if no argument is provided
ARCHIVE=$(ls -t latam-salesforce-api-bundle*.tar.gz 2>/dev/null | head -n 1)
ARCHIVE=${1:-$ARCHIVE}

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo -e "${RED}❌ No archive found.${NC}"
    echo "Usage: ./scripts/import-images.sh latam-salesforce-api-bundle.tar.gz"
    echo ""
    echo "Download the latest release from GitHub:"
    echo "  gh release download --pattern '*.tar.gz' --repo <owner>/latam-salesforce-api"
    exit 1
fi

echo -e "${GREEN}🚀 Importing Docker Images${NC}"
echo "==========================================="
echo "File: $ARCHIVE"

TEMP_DIR="docker-images-import"
mkdir -p "${TEMP_DIR}"

# 1. Extract the bundle
echo -e "\n${YELLOW}📦 Extracting tarball...${NC}"
tar -xzf "$ARCHIVE" -C "${TEMP_DIR}"

# 2. Load all .tar images found inside
echo -e "\n${YELLOW}📥 Loading Docker images...${NC}"

LOADED=0
for img in "${TEMP_DIR}"/*.tar; do
    if [ -f "$img" ]; then
        echo -e "\n${GREEN}Loading $(basename "$img")...${NC}"
        docker load -i "$img"
        LOADED=$((LOADED + 1))
    fi
done

if [ "$LOADED" -eq 0 ]; then
    echo -e "${RED}❌ No .tar image files found inside the archive.${NC}"
    rm -rf "${TEMP_DIR}"
    exit 1
fi

# 3. Cleanup
echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
rm -rf "${TEMP_DIR}"

echo -e "\n${GREEN}✅ Import complete! (${LOADED} image(s) loaded)${NC}"
echo "==========================================="

echo -e "\n${YELLOW}📋 Loaded images:${NC}"
docker images | grep -E "latam-salesforce-api"

echo -e "\n${YELLOW}🚀 Next steps:${NC}"
echo "1. Copy your .env file to the server"
echo "2. Run: docker run -d --name latam-sf-api --env-file .env -p 8000:8000 <username>/latam-salesforce-api:latest"
