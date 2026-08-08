#!/bin/bash
# Paper Collector 快捷运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/scripts/collect.py" "$@"
