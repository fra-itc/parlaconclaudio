#!/bin/bash
# Wave 2 Status Checker
# Shows progress across all 3 parallel terminals

echo "════════════════════════════════════════════════════════════"
echo "           WAVE 2 PROGRESS STATUS"
echo "════════════════════════════════════════════════════════════"
echo ""

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Terminal 1: Docker Secrets
echo -e "${BLUE}🔵 TERMINAL 1: Docker Secrets Management${NC}"
if [ -d "/home/frisco/projects/RTSTT-secrets" ]; then
    cd /home/frisco/projects/RTSTT-secrets
    echo "   Branch: $(git branch --show-current)"
    echo "   Status: $(git status --short | wc -l) uncommitted files"
    if [ -f ".READY_FOR_SYNC" ]; then
        echo -e "   ${GREEN}✅ READY FOR SYNC${NC}"
    else
        echo "   ⏳ In progress..."
    fi
    echo "   Latest: $(git log --oneline -1 2>/dev/null || echo 'No commits yet')"
else
    echo "   ❌ Worktree not found"
fi
echo ""

# Terminal 2: Audio Testing
echo -e "${GREEN}🟢 TERMINAL 2: Real-time Audio Testing${NC}"
if [ -d "/home/frisco/projects/RTSTT-audio-tests" ]; then
    cd /home/frisco/projects/RTSTT-audio-tests
    echo "   Branch: $(git branch --show-current)"
    echo "   Status: $(git status --short | wc -l) uncommitted files"
    if [ -f ".READY_FOR_SYNC" ]; then
        echo -e "   ${GREEN}✅ READY FOR SYNC${NC}"
    else
        echo "   ⏳ In progress..."
    fi
    echo "   Latest: $(git log --oneline -1 2>/dev/null || echo 'No commits yet')"
else
    echo "   ❌ Worktree not found"
fi
echo ""

# Terminal 3: MUI Frontend
echo -e "${YELLOW}🟡 TERMINAL 3: MUI Frontend Development${NC}"
if [ -d "/home/frisco/projects/RTSTT-frontend" ]; then
    cd /home/frisco/projects/RTSTT-frontend
    echo "   Branch: $(git branch --show-current)"
    echo "   Status: $(git status --short | wc -l) uncommitted files"
    if [ -f ".READY_FOR_SYNC" ]; then
        echo -e "   ${GREEN}✅ READY FOR SYNC${NC}"
    else
        echo "   ⏳ In progress..."
    fi
    echo "   Latest: $(git log --oneline -1 2>/dev/null || echo 'No commits yet')"
else
    echo "   ❌ Worktree not found"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════════"
READY_COUNT=0
[ -f "/home/frisco/projects/RTSTT-secrets/.READY_FOR_SYNC" ] && ((READY_COUNT++))
[ -f "/home/frisco/projects/RTSTT-audio-tests/.READY_FOR_SYNC" ] && ((READY_COUNT++))
[ -f "/home/frisco/projects/RTSTT-frontend/.READY_FOR_SYNC" ] && ((READY_COUNT++))

echo "Ready for sync: $READY_COUNT / 3"
echo ""

if [ $READY_COUNT -eq 3 ]; then
    echo -e "${GREEN}✅ ALL TERMINALS READY! Run sync agent:${NC}"
    echo "   bash /home/frisco/projects/RTSTT/scripts/wave2-sync-agent.sh"
else
    echo "⏳ Waiting for terminals to complete..."
    echo "   Run this script again to check progress"
fi
echo ""
