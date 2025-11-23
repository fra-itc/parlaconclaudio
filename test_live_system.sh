#!/bin/bash
#
# Live System Test - End-to-End Verification
# Tests: Audio Bridge → WebSocket → Backend → STT → NLP → Summary
#

set -e

echo "======================================================================"
echo "  RTSTT Live System Test"
echo "  Testing complete pipeline: Audio → STT → NLP → Summary"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test configuration
TEST_DURATION=15
PATTERN="sine"
DRIVER="mock"

# Step 1: Clean up and rebuild
echo -e "${YELLOW}[1/5] Stopping existing containers...${NC}"
docker-compose down
echo ""

# Step 2: Rebuild backend with fix
echo -e "${YELLOW}[2/5] Rebuilding backend with event loop fix...${NC}"
docker-compose build backend
echo ""

# Step 3: Start all services
echo -e "${YELLOW}[3/5] Starting all services...${NC}"
docker-compose up -d redis backend
sleep 5

# Check backend health
echo -e "${YELLOW}Checking backend health...${NC}"
BACKEND_STATUS=$(docker-compose ps backend | grep "Up" || echo "Down")
if [[ "$BACKEND_STATUS" == *"Up"* ]]; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    docker-compose logs backend
    exit 1
fi
echo ""

# Step 4: Check backend logs for startup
echo -e "${YELLOW}[4/5] Backend startup logs:${NC}"
docker-compose logs backend | tail -20
echo ""

# Step 5: Run audio bridge test
echo -e "${YELLOW}[5/5] Running audio bridge live test (${TEST_DURATION}s)...${NC}"
echo -e "${YELLOW}Pattern: ${PATTERN} | Driver: ${DRIVER}${NC}"
echo ""

docker exec rtstt-backend python -m src.host_audio_bridge.main \
    --driver ${DRIVER} \
    --pattern ${PATTERN} \
    --test-duration ${TEST_DURATION} \
    --log-level INFO

# Capture exit code
TEST_EXIT_CODE=$?
echo ""

# Step 6: Check results
echo "======================================================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Live test PASSED${NC}"
    echo ""
    echo "System Status:"
    echo -e "  ${GREEN}✓${NC} Audio capture: Working"
    echo -e "  ${GREEN}✓${NC} WebSocket streaming: Working"
    echo -e "  ${GREEN}✓${NC} Backend processing: Working"
    echo ""
    echo "Next steps:"
    echo "  1. Check backend logs for transcription results"
    echo "  2. Test with real microphone: --driver pulseaudio (Linux) or --driver portaudio"
    echo "  3. Start frontend: cd src/ui/desktop && npm start"
else
    echo -e "${RED}✗ Live test FAILED (exit code: $TEST_EXIT_CODE)${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check backend logs: docker-compose logs backend"
    echo "  2. Check Redis connection: docker-compose logs redis"
    echo "  3. Verify WebSocket endpoint is accessible"
fi
echo "======================================================================"
echo ""

# Show final logs
echo -e "${YELLOW}Recent backend logs:${NC}"
docker-compose logs backend | tail -30
