#!/bin/bash
# Narração grátis e offline (sherpa-onnx + vozes Piper pt-BR).
# Uso: bash narrar.sh "texto" saida.mp3 [voz] [velocidade]
#   voz: faber-medium (masc, padrão) | dii-high | miro-high | cadu-medium | jeff-medium
#   velocidade: 1.0 normal, 0.9 mais rápido, 1.1 mais lento
set -e
TXT="$1"; OUT="${2:-narracao.mp3}"; VOZ="${3:-faber-medium}"; VEL="${4:-0.92}"
D="${TTS_DIR:-$HOME/tts}"; mkdir -p "$D"; cd "$D"
V=1.12.15; E="sherpa-onnx-v$V-linux-x64-shared"; R=https://github.com/k2-fsa/sherpa-onnx/releases/download
[ -d "$E" ] || curl -sL "$R/v$V/$E.tar.bz2" | tar xj
M="vits-piper-pt_BR-$VOZ"
[ -d "$M" ] || curl -sL "$R/tts-models/$M.tar.bz2" | tar xj
ONNX=$(ls "$M"/*.onnx | head -1)
LD_LIBRARY_PATH="$E/lib" "./$E/bin/sherpa-onnx-offline-tts" --vits-model="$ONNX" --vits-tokens="$M/tokens.txt" \
  --vits-data-dir="$M/espeak-ng-data" --vits-length-scale="$VEL" --output-filename="$D/_tmp.wav" "$TXT" >/dev/null 2>&1
cd - >/dev/null
ffmpeg -y -loglevel error -i "$D/_tmp.wav" -af "highpass=f=70,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-14:TP=-1" -ar 44100 -b:a 192k "$OUT"
echo "$OUT"
