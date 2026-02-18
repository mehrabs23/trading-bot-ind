#!/bin/bash

# Configuration
PROJECT_DIR="/home/mehrab/trading-bot-ind"
VENV_DIR="$PROJECT_DIR/.venv"
LOG_DIR="$PROJECT_DIR/logs"
REPORT_DIR="$PROJECT_DIR/reports"
UNIVERSE="$PROJECT_DIR/universe/nifty50.txt" # Default universe, change as needed
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/daily_$DATE.log"

# Ensure directories exist
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Daily Trading Bot Execution..."

# 1. Activate Virtual Environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    log "Virtual environment activated."
else
    log "ERROR: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Move to project directory
cd "$PROJECT_DIR" || exit

# 2. Fetch Latest Data
log "Fetching latest data for universe: $UNIVERSE"
python3 -m scripts.fetch_yahoo_bulk --universe "$UNIVERSE" --interval 5m --period 5d >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "Data fetch completed successfully."
else
    log "ERROR: Data fetch failed."
    # Decide if we should continue? For now, yes, maybe partial data works.
fi

# 3. Generate Signals
log "Generating Signals (Strategy: ALL)..."
python3 main.py --mode signal --universe "$UNIVERSE" --strategy all --min_avg_volume 500000 --min_avg_value 5000000 >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "Signal generation completed."
else
    log "ERROR: Signal generation failed."
fi

# 4. Run Daily Backtest (Optional - for performance tracking)
log "Running Daily Backtest/Performance Check..."
python3 main.py --mode backtest --universe "$UNIVERSE" --strategy all --report_dir "$REPORT_DIR/backtests" >> "$LOG_FILE" 2>&1

log "Daily execution finished."
