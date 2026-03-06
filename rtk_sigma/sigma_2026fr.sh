#!/bin/bash

# ==============================================================================
# Path Configuration
# ==============================================================================
SIGMA_TOOL_DIR="/home/rtk/Documents/sigma_tool"
WFA_DIR="/tmp/wfa"
WFA_SCRIPT="./wfa_test.sh"
LINUX_STABLE_DIR="/home/rtk/Documents/linux-stable"
RELOAD_SCRIPT="./reload_all.sh"

# Monitoring Constants
DRIVER_NAME="rtw89"

# ==============================================================================
# Global Configuration & Visual Styles
# ==============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

ICON_INFO="${BLUE}ℹ${NC}"
ICON_SUCCESS="${GREEN}✔${NC}"
ICON_WARN="${YELLOW}⚠${NC}"
ICON_ERROR="${RED}✖${NC}"

# ==============================================================================
# Helper Functions (Logging & UI)
# ==============================================================================
log_info()    { echo -e "${BLUE}[ INFO    ]${NC} ${CYAN}$1${NC}"; }
log_success() { echo -e "${GREEN}[ SUCCESS ]${NC} ${GREEN}$1${NC}"; }
log_warn()    { echo -e "${YELLOW}[ WARNING ]${NC} ${YELLOW}$1${NC}"; }
log_error()   { echo -e "${RED}[ ERROR   ]${NC} ${RED}$1${NC}"; }

print_banner() {
    echo -e "${PURPLE}┌────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${PURPLE}│${NC}  ${BOLD}${WHITE}SIGMA TOOL - 2026 FR Edition${NC}                                      ${PURPLE}│${NC}"
    echo -e "${PURPLE}└────────────────────────────────────────────────────────────────────┘${NC}"
}

# ==============================================================================
# Privilege Management
# ==============================================================================
init_sudo() {
    log_warn "This script requires administrative privileges."
    sudo -v
    while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
    log_success "Sudo privilege authenticated."
}

# ==============================================================================
# Core Action Functions
# ==============================================================================

do_status() {
    log_info "Checking Sigma Tool Environment Status..."

    # 1. Kernel Module Check
    echo -e "\n${BOLD}${WHITE}1. Kernel Module ($DRIVER_NAME):${NC}"
    if lsmod | grep -q "$DRIVER_NAME"; then
        echo -e "   Status: ${GREEN}✔ Loaded${NC}"
        lsmod | grep "$DRIVER_NAME" | sed 's/^/   /'
    else
        echo -e "   Status: ${RED}✖ Not Found${NC}"
    fi

    # 2. Core WFA Processes Check
    echo -e "\n${BOLD}${WHITE}2. WFA Components Status:${NC}"

    DUT_PID=$(pgrep "wfa_dut" | xargs)
    [ -n "$DUT_PID" ] && echo -e "   [ ${GREEN}OK${NC} ] wfa_dut is running (PID: $DUT_PID)" || echo -e "   [ ${RED}!!${NC} ] wfa_dut is ${RED}MISSING${NC}"

    CA_PID=$(pgrep "wfa_ca" | xargs)
    [ -n "$CA_PID" ] && echo -e "   [ ${GREEN}OK${NC} ] wfa_ca  is running (PID: $CA_PID)" || echo -e "   [ ${RED}!!${NC} ] wfa_ca  is ${RED}MISSING${NC}"

    WPAS_PID=$(pgrep "wpa_supplicant" | xargs)
    [ -n "$WPAS_PID" ] && echo -e "   [ ${GREEN}OK${NC} ] wpa_supplicant is running (PID: $WPAS_PID)" || echo -e "   [ ${RED}!!${NC} ] wpa_supplicant is ${RED}MISSING${NC}"

    # 3. Network Ports Check
    echo -e "\n${BOLD}${WHITE}3. Port Listening:${NC}"
    if command -v ss >/dev/null; then
        DUT_PORT=$(ss -tunlp | grep :8000)
        CA_PORT=$(ss -tunlp | grep :9000)
    else
        DUT_PORT=$(netstat -tunlp | grep :8000)
        CA_PORT=$(netstat -tunlp | grep :9000)
    fi
    [ -n "$DUT_PORT" ] && echo -e "   Port 8000 (DUT): ${GREEN}LISTEN${NC}" || echo -e "   Port 8000 (DUT): ${RED}CLOSED${NC}"
    [ -n "$CA_PORT" ]  && echo -e "   Port 9000 (CA) : ${GREEN}LISTEN${NC}" || echo -e "   Port 9000 (CA) : ${RED}CLOSED${NC}"

    # 4. Debug Snippet
    echo -e "\n${BOLD}${WHITE}4. Latest Kernel Debug Messages:${NC}"
    sudo dmesg | grep -E "$DRIVER_NAME" | tail -n 5 | sed 's/^/   /'
    echo ""
}

do_boot() {
    log_info "Executing boot sequence (Driver Reload)..."
    if cd "$LINUX_STABLE_DIR"; then
        log_info "Running reload script: $RELOAD_SCRIPT"
        sudo $RELOAD_SCRIPT
        log_success "Driver modules reloaded."
    else
        log_error "Failed to access directory: $LINUX_STABLE_DIR"
        log_warn "Please check the variable 'LINUX_STABLE_DIR' in the Path Configuration section."
        exit 1
    fi
    do_start
}

do_stop() {
    log_info "Initiating shutdown of services..."
    if cd "$WFA_DIR"; then
        sudo $WFA_SCRIPT stop
        log_success "Service stop signal sent to $WFA_SCRIPT."
    else
        log_error "Could not access WFA directory: $WFA_DIR"
        log_warn "Please check the variable 'WFA_DIR' in the Path Configuration section."
        exit 1
    fi
}

do_start() {
    log_info "Step 1: Switching to project directory..."
    if cd "$SIGMA_TOOL_DIR"; then
        echo -e "          ${WHITE}→ Path:${NC} ${BLUE}$(pwd)${NC}"
    else
        log_error "Failed to access directory: $SIGMA_TOOL_DIR"
        log_warn "Please check the variable 'SIGMA_TOOL_DIR' in the Path Configuration section."
        exit 1
    fi

    log_info "Step 2: Running 'make install'..."
    if sudo make install; then
        log_success "Build and installation completed successfully."
    else
        log_error "Make install failed. Execution aborted."
        exit 1
    fi

    log_info "Step 3: Triggering WFA test script..."
    if cd "$WFA_DIR"; then
        if sudo $WFA_SCRIPT start-sta; then
            log_success "WFA service is now UP and RUNNING."
        else
            log_error "WFA script execution failed."
            exit 1
        fi
    else
        log_error "Could not find WFA directory: $WFA_DIR"
        log_warn "Please check the variable 'WFA_DIR' in the Path Configuration section."
        exit 1
    fi
}

do_restart() {
    log_warn "Restarting the services (Stop -> Boot -> Start)..."
    do_stop
    sleep 1
    do_boot
}

# ==============================================================================
# Main Entry Point
# ==============================================================================
main() {
    if [ -z "$1" ]; then
        echo -e "${RED}Usage:${NC} $0 {boot|start|stop|restart|status}"
        exit 1
    fi

    init_sudo
    print_banner

    START_TIME=$(date +%s)

    case "$1" in
        "boot")    do_boot ;;
        "start")   do_start ;;
        "stop")    do_stop ;;
        "restart") do_restart ;;
        "status")  do_status ;;
        *)
            log_error "Invalid parameter: $1"
            echo "Usage: $0 {boot|start|stop|restart|status}"
            exit 1
            ;;
    esac

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo -e "\n"
    echo -e "${GREEN}${ICON_SUCCESS}${NC}  ${BOLD}${WHITE}Execution Finished Successfully${NC}"
    echo -e "${GREEN}│${NC}"
    echo -e "${GREEN}├─${NC} Command  : ${CYAN}$1${NC}"
    echo -e "${GREEN}├─${NC} Duration : ${DURATION}s"
    echo -e "${GREEN}└────────────────────────────────────────────────────────────────────${NC}"
}

main "$@"