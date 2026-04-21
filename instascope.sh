#!/usr/bin/env bash
# InstaScope v2.0 — macOS / Linux launcher
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║     📸  InstaScope v2.0 — Instagram Analyzer        ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# ── Python 3 ────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "  [!] python3 not found"
    echo "  macOS : brew install python"
    echo "  Ubuntu: sudo apt install python3"
    exit 1
fi
echo "  [OK] $(python3 --version)"

# ── tkinter ──────────────────────────────────────────────────────────────────
python3 -c "import tkinter" 2>/dev/null || {
    echo "  [!] tkinter missing"
    echo "  macOS : brew install python-tk"
    echo "  Ubuntu: sudo apt install python3-tk"
    exit 1
}
echo "  [OK] tkinter"

# ── matplotlib ───────────────────────────────────────────────────────────────
python3 -c "import matplotlib" 2>/dev/null || {
    echo "  [..] Installing matplotlib..."
    python3 -m pip install --quiet matplotlib && echo "  [OK] matplotlib installed" || echo "  [!]  matplotlib failed — charts disabled"
}

# ── tkinterdnd2 ───────────────────────────────────────────────────────────────
python3 -c "import tkinterdnd2" 2>/dev/null || {
    echo "  [..] Installing tkinterdnd2 (drag & drop)..."
    python3 -m pip install --quiet tkinterdnd2 && echo "  [OK] tkinterdnd2 installed" || echo "  [!]  tkinterdnd2 failed — drag & drop disabled"
}

echo ""
echo "  [OK] Launching InstaScope..."
echo ""
cd "$DIR"
python3 instascope.py &
