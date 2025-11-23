#!/bin/bash
#
# RTSTT POC Deployment Script
#
# Deploy and run the complete RTSTT stack for proof-of-concept demonstration.
# Manages service startup, health checks, and audio bridge connection.
#
# Usage:
#   ./scripts/deploy-poc.sh [start|stop|restart|status|logs] [options]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Default options
MODE="test"  # test or production
AUDIO_DRIVER="mock"
TEST_DURATION=30
WAIT_TIMEOUT=120

# Service startup order and health check delays
declare -A SERVICE_DELAYS=(
    ["redis"]=5
    ["stt-engine"]=15
    ["nlp-service"]=10
    ["summary-service"]=10
    ["backend"]=10
)

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

usage() {
    cat <<EOF
Usage: $0 COMMAND [OPTIONS]

Commands:
    start       Start all services and audio bridge
    stop        Stop all services
    restart     Restart all services
    status      Show service status
    logs        Show service logs
    test        Run quick test with mock audio (default)

Options:
    --mode MODE         Deployment mode: test or production (default: test)
    --driver DRIVER     Audio driver: mock, wasapi, pulseaudio (default: mock)
    --duration SECONDS  Test duration in seconds (default: 30)
    --skip-build        Skip Docker image rebuild
    --skip-health       Skip health checks
    -h, --help          Show this help message

Examples:
    # Quick test with mock audio
    $0 test

    # Start services only
    $0 start --skip-build

    # Start with real audio on Windows
    $0 start --mode production --driver wasapi

    # View logs
    $0 logs backend

    # Stop everything
    $0 stop
EOF
}

parse_args() {
    COMMAND="${1:-test}"
    shift || true

    SKIP_BUILD=false
    SKIP_HEALTH=false
    LOG_SERVICE=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --driver)
                AUDIO_DRIVER="$2"
                shift 2
                ;;
            --duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-health)
                SKIP_HEALTH=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                LOG_SERVICE="$1"
                shift
                ;;
        esac
    done
}

check_requirements() {
    print_header "Checking Requirements"

    cd "$PROJECT_ROOT"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    print_success "Docker: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose: $(docker-compose --version)"

    # Check compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml not found at $COMPOSE_FILE"
        exit 1
    fi
    print_success "Compose file found"

    # Check if secrets are configured
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Run: ./scripts/setup-secrets.sh"
    else
        print_success ".env file found"
    fi
}

build_images() {
    if [ "$SKIP_BUILD" = true ]; then
        print_warning "Skipping image build (--skip-build)"
        return 0
    fi

    print_header "Building Docker Images"

    cd "$PROJECT_ROOT"

    # Build all images
    docker-compose build

    print_success "Images built successfully"
}

start_service() {
    local service=$1
    local delay=${SERVICE_DELAYS[$service]:-5}

    print_info "Starting $service..."
    docker-compose up -d "$service"

    if [ "$SKIP_HEALTH" = false ]; then
        sleep "$delay"
        check_service_health "$service"
    fi
}

check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=0

    print_info "Checking $service health..."

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps "$service" | grep -q "Up"; then
            local health=$(docker inspect --format='{{.State.Health.Status}}' "rtstt-$service" 2>/dev/null || echo "none")

            if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
                print_success "$service is healthy"
                return 0
            fi
        fi

        attempt=$((attempt + 1))
        sleep 2
    done

    print_warning "$service health check timeout"
    return 1
}

start_all_services() {
    print_header "Starting RTSTT Services"

    cd "$PROJECT_ROOT"

    # Start services in order
    local services=("redis" "stt-engine" "nlp-service" "summary-service" "backend")

    for service in "${services[@]}"; do
        start_service "$service"
    done

    print_success "All services started"
}

stop_all_services() {
    print_header "Stopping RTSTT Services"

    cd "$PROJECT_ROOT"

    docker-compose down

    print_success "All services stopped"
}

show_service_status() {
    print_header "Service Status"

    cd "$PROJECT_ROOT"

    # Show container status
    docker-compose ps

    echo ""

    # Show resource usage
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        $(docker-compose ps -q) 2>/dev/null || print_warning "No running containers"
}

show_logs() {
    local service=$1

    cd "$PROJECT_ROOT"

    if [ -z "$service" ]; then
        docker-compose logs --tail=100 -f
    else
        docker-compose logs --tail=100 -f "$service"
    fi
}

run_health_check() {
    print_header "Running Health Checks"

    cd "$PROJECT_ROOT"

    if [ -f "scripts/health_check.py" ]; then
        python3 scripts/health_check.py
    else
        print_warning "Health check script not found"

        # Basic health check
        print_info "Basic container health check:"
        docker-compose ps
    fi
}

start_audio_bridge() {
    print_header "Starting Audio Bridge"

    cd "$PROJECT_ROOT"

    local bridge_cmd="python -m src.host_audio_bridge.main"
    bridge_cmd="$bridge_cmd --driver $AUDIO_DRIVER"
    bridge_cmd="$bridge_cmd --log-level INFO"

    if [ "$MODE" = "test" ]; then
        bridge_cmd="$bridge_cmd --test-duration $TEST_DURATION"
        bridge_cmd="$bridge_cmd --pattern sine"
    fi

    print_info "Running: $bridge_cmd"
    echo ""

    # Run in backend container
    docker exec -it rtstt-backend $bridge_cmd
}

run_demo() {
    print_header "Running RTSTT POC Demo"

    # Check requirements
    check_requirements

    # Build images
    build_images

    # Start services
    start_all_services

    # Wait for all services to be ready
    if [ "$SKIP_HEALTH" = false ]; then
        sleep 5
        run_health_check
    fi

    # Show status
    show_service_status

    # Start audio bridge
    if [ "$MODE" = "test" ]; then
        print_header "Testing Audio Pipeline"
        print_info "Duration: ${TEST_DURATION}s"
        print_info "Driver: $AUDIO_DRIVER"
        echo ""

        start_audio_bridge

        print_success "Test completed!"
    else
        print_header "Production Mode"
        print_info "Starting audio bridge in production mode..."
        print_warning "Press Ctrl+C to stop"
        echo ""

        start_audio_bridge
    fi
}

print_deployment_info() {
    print_header "RTSTT POC Deployment Info"

    cat <<EOF
Services:
  Backend:         http://localhost:8000
  WebSocket:       ws://localhost:8000/ws
  STT Engine:      gRPC on port 50051
  NLP Service:     gRPC on port 50052
  Summary Service: gRPC on port 50053
  Redis:           localhost:6379

Audio Bridge:
  Driver:          $AUDIO_DRIVER
  Mode:            $MODE
  Sample Rate:     16000 Hz
  Channels:        1 (mono)

Logs:
  View all:        docker-compose logs -f
  View backend:    docker-compose logs -f backend
  View STT:        docker-compose logs -f stt-engine

Management:
  Status:          $0 status
  Stop:            $0 stop
  Restart:         $0 restart
EOF
}

# Main execution
main() {
    parse_args "$@"

    case "$COMMAND" in
        start)
            check_requirements
            build_images
            start_all_services
            run_health_check
            show_service_status
            print_deployment_info
            ;;
        stop)
            stop_all_services
            ;;
        restart)
            stop_all_services
            sleep 2
            check_requirements
            build_images
            start_all_services
            run_health_check
            show_service_status
            print_deployment_info
            ;;
        status)
            show_service_status
            ;;
        logs)
            show_logs "$LOG_SERVICE"
            ;;
        test)
            run_demo
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
