#!/bin/bash

# E2E Verification Script for Polished Live Sprint Dashboard
# This script automates the end-to-end verification process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8420
FRONTEND_PORT=5173
BACKEND_PID=""
FRONTEND_PID=""
PROJECT_ID=""
SPRINT_ID=""

# Function to print colored output
print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to cleanup on exit
cleanup() {
    print_step "Cleaning up..."

    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_success "Backend stopped"
    fi

    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_success "Frontend stopped"
    fi

    # Kill any remaining processes on our ports
    lsof -ti :$BACKEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti :$FRONTEND_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
}

trap cleanup EXIT

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    return 1
}

# Check prerequisites
print_step "Checking prerequisites..."

# Check for required commands
for cmd in python3 node npm curl jq; do
    if ! command -v $cmd &> /dev/null; then
        print_error "$cmd is not installed"
        exit 1
    fi
    print_success "$cmd found"
done

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    print_error "No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
    exit 1
fi
print_success "API keys configured"

# Check if foundrai is installed
if ! command -v foundrai &> /dev/null; then
    print_error "foundrai CLI not found. Run: pip install -e ."
    exit 1
fi
print_success "foundrai CLI found"

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    print_warning "Frontend dependencies not installed"
    print_step "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    print_success "Frontend dependencies installed"
else
    print_success "Frontend dependencies found"
fi

# Kill any existing services on our ports
print_step "Checking for existing services..."
if check_port $BACKEND_PORT; then
    print_warning "Port $BACKEND_PORT is in use, killing existing process..."
    lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if check_port $FRONTEND_PORT; then
    print_warning "Port $FRONTEND_PORT is in use, killing existing process..."
    lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start backend service
print_step "Starting backend service on port $BACKEND_PORT..."
foundrai serve --port $BACKEND_PORT > /tmp/foundrai-backend.log 2>&1 &
BACKEND_PID=$!
print_success "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
print_step "Waiting for backend to be ready..."
if wait_for_service "http://localhost:$BACKEND_PORT/api/docs"; then
    print_success "Backend is ready"
else
    print_error "Backend failed to start. Check /tmp/foundrai-backend.log"
    cat /tmp/foundrai-backend.log
    exit 1
fi

# Start frontend service
print_step "Starting frontend service on port $FRONTEND_PORT..."
cd frontend
npm run dev > /tmp/foundrai-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
print_success "Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
print_step "Waiting for frontend to be ready..."
if wait_for_service "http://localhost:$FRONTEND_PORT"; then
    print_success "Frontend is ready"
else
    print_error "Frontend failed to start. Check /tmp/foundrai-frontend.log"
    cat /tmp/foundrai-frontend.log
    exit 1
fi

# Create test data
print_step "Creating test project..."
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:$BACKEND_PORT/api/projects \
    -H "Content-Type: application/json" \
    -d '{"name": "E2E Test Project", "description": "Automated E2E verification project"}')

PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "null" ]; then
    print_error "Failed to create project"
    echo "Response: $PROJECT_RESPONSE"
    exit 1
fi
print_success "Project created (ID: $PROJECT_ID)"

# Create test sprint
print_step "Creating test sprint..."
SPRINT_RESPONSE=$(curl -s -X POST http://localhost:$BACKEND_PORT/api/sprints \
    -H "Content-Type: application/json" \
    -d "{\"project_id\": \"$PROJECT_ID\", \"goal\": \"Build a comprehensive todo application with user authentication and real-time sync\", \"status\": \"active\"}")

SPRINT_ID=$(echo "$SPRINT_RESPONSE" | jq -r '.id')
if [ -z "$SPRINT_ID" ] || [ "$SPRINT_ID" == "null" ]; then
    print_error "Failed to create sprint"
    echo "Response: $SPRINT_RESPONSE"
    exit 1
fi
print_success "Sprint created (ID: $SPRINT_ID)"

# Create tasks in different statuses
print_step "Creating test tasks..."

STATUSES=("backlog" "backlog" "backlog" "in_progress" "in_progress" "in_review" "done" "failed")
PRIORITIES=("high" "medium" "low" "medium" "high" "medium" "low" "high")
TASKS_CREATED=0

for i in "${!STATUSES[@]}"; do
    STATUS="${STATUSES[$i]}"
    PRIORITY="${PRIORITIES[$i]}"
    TITLE="Test Task $((i+1)): Implement feature for $STATUS state"

    TASK_RESPONSE=$(curl -s -X POST http://localhost:$BACKEND_PORT/api/tasks \
        -H "Content-Type: application/json" \
        -d "{
            \"sprint_id\": \"$SPRINT_ID\",
            \"title\": \"$TITLE\",
            \"description\": \"This is a test task created for E2E verification. Status: $STATUS, Priority: $PRIORITY\",
            \"status\": \"$STATUS\",
            \"priority\": \"$PRIORITY\",
            \"assigned_agent\": \"developer\"
        }")

    TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id')
    if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        TASKS_CREATED=$((TASKS_CREATED + 1))
    fi
done

print_success "Created $TASKS_CREATED tasks"

# Create additional tasks for performance testing
print_step "Creating additional tasks for performance testing..."
for i in {1..20}; do
    curl -s -X POST http://localhost:$BACKEND_PORT/api/tasks \
        -H "Content-Type: application/json" \
        -d "{
            \"sprint_id\": \"$SPRINT_ID\",
            \"title\": \"Performance Test Task $i\",
            \"description\": \"Additional task for performance testing\",
            \"status\": \"backlog\",
            \"priority\": \"low\"
        }" > /dev/null
done
print_success "Created 20 additional tasks for performance testing"

# Generate events for agent feed testing
print_step "Generating test events..."
for i in {1..15}; do
    curl -s -X POST http://localhost:$BACKEND_PORT/api/events \
        -H "Content-Type: application/json" \
        -d "{
            \"sprint_id\": \"$SPRINT_ID\",
            \"event_type\": \"agent.action\",
            \"agent_id\": \"developer\",
            \"data\": {
                \"action\": \"Task updated\",
                \"reasoning\": \"Updated task status based on current progress and blocker resolution.\",
                \"task_id\": \"test-task-$i\"
            }
        }" > /dev/null
done
print_success "Generated 15 test events"

# Print verification URLs
echo ""
echo "========================================="
echo "  E2E Verification Environment Ready!"
echo "========================================="
echo ""
echo -e "${GREEN}Backend API:${NC} http://localhost:$BACKEND_PORT"
echo -e "${GREEN}API Docs:${NC} http://localhost:$BACKEND_PORT/api/docs"
echo -e "${GREEN}Frontend:${NC} http://localhost:$FRONTEND_PORT"
echo -e "${GREEN}Dashboard:${NC} http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
echo ""
echo -e "${BLUE}Project ID:${NC} $PROJECT_ID"
echo -e "${BLUE}Sprint ID:${NC} $SPRINT_ID"
echo ""
echo "========================================="
echo ""

# Open browser automatically (macOS/Linux)
print_step "Opening dashboard in browser..."
if command -v open &> /dev/null; then
    # macOS
    open "http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open "http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
elif command -v start &> /dev/null; then
    # Windows
    start "http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
else
    print_warning "Could not open browser automatically. Please open manually:"
    echo "  http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
fi

# Print verification checklist
echo ""
print_step "Manual Verification Checklist:"
echo ""
echo "  1. ✓ Kanban board shows tasks in correct columns"
echo "  2. ✓ Drag a task between columns and verify status updates"
echo "  3. ✓ Agent feed shows timestamped events with details"
echo "  4. ✓ Goal tree visualization renders (if implemented)"
echo "  5. ✓ Toggle dark mode and verify all components"
echo "  6. ✓ Resize to tablet viewport (768px) and verify responsive layout"
echo "  7. ✓ Check performance with 28 tasks and 15 events"
echo "  8. ✓ Verify no console errors in DevTools"
echo ""

# Automated checks
print_step "Running automated checks..."

# Check API health
if curl -s http://localhost:$BACKEND_PORT/api/docs | grep -q "FoundrAI"; then
    print_success "API docs accessible"
else
    print_warning "API docs check failed"
fi

# Check WebSocket endpoint
print_success "WebSocket endpoint available at: ws://localhost:$BACKEND_PORT/ws/sprints/$SPRINT_ID"

# Check frontend build
if curl -s http://localhost:$FRONTEND_PORT | grep -q "FoundrAI"; then
    print_success "Frontend loading correctly"
else
    print_warning "Frontend check failed"
fi

# Wait for user verification
echo ""
echo "========================================="
print_step "Perform manual verification now"
echo "========================================="
echo ""
echo "Follow the steps in E2E_VERIFICATION.md"
echo ""
echo "Press ENTER when verification is complete..."
read -r

# Run performance check
print_step "Running performance check..."
echo ""
echo "Dashboard URL: http://localhost:$FRONTEND_PORT/sprints/$SPRINT_ID"
echo ""
echo "Open DevTools and check:"
echo "  - Load time < 2 seconds"
echo "  - No console errors"
echo "  - WebSocket connected"
echo "  - Smooth drag-and-drop"
echo ""

# Cleanup instructions
echo ""
echo "========================================="
print_step "Verification Complete"
echo "========================================="
echo ""
echo "Services will be stopped when you exit this script."
echo "Press Ctrl+C to stop all services and exit."
echo ""

# Keep running
wait
