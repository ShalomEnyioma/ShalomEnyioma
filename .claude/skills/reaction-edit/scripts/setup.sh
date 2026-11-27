#!/usr/bin/env bash
# One-time setup for the reaction-edit skill (about 1.1 GB of models, cached).
#   bash .claude/skills/reaction-edit/scripts/setup.sh [MODELS_DIR]
set -euo pipefail
M="${1:-${REACTION_MODELS:-$HOME/.cache/reaction-edit/models}}"
mkdir -p "$M"
pip install -q sherpa-onnx scipy "opencv-python-headless<5" numpy noisereduce soundfile
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
[ -f "$M/silero_vad.onnx" ] || curl -sSL -o "$M/silero_vad.onnx" "$REL/silero_vad.onnx"
P=sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8   # English ASR with word timestamps
if [ ! -d "$M/$P" ]; then
  curl -sSL -o "$M/$P.tar.bz2" "$REL/$P.tar.bz2" && tar xjf "$M/$P.tar.bz2" -C "$M" && rm "$M/$P.tar.bz2"
fi
command -v ffmpeg >/dev/null || { echo "ffmpeg is required (apt-get install -y ffmpeg)"; exit 1; }
fc-list | grep -qi "Inter Black" || echo "note: 'Inter Black' font not found; pass --font to render.py"
echo "models ready in $M"
