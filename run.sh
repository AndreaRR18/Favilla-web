#!/usr/bin/env bash
# Build the site and serve it locally with a single command.
# Usage: ./run.sh [port]   (default port: 8000)
set -euo pipefail

cd "$(dirname "$0")"
PORT="${1:-8000}"

python3 scripts/build.py --out _site
echo "Serving http://localhost:${PORT} — press Ctrl+C to stop."
python3 -m http.server -d _site "$PORT"
