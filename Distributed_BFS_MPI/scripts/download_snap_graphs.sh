#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/snap"
mkdir -p "$DATA"
base="https://snap.stanford.edu/data"
fetch(){ local name="$1"; local file="$2"; local url="$3"; if [[ ! -s "$DATA/$file" ]]; then echo "Downloading $name ..."; curl -fL --retry 3 "$url" -o "$DATA/$file.gz"; gzip -df "$DATA/$file.gz"; else echo "Found $name"; fi; }
fetch "social: soc-Epinions1" "soc-Epinions1.txt" "$base/soc-Epinions1.txt.gz"
fetch "web: web-Google" "web-Google.txt" "$base/web-Google.txt.gz"
fetch "road: roadNet-CA" "roadNet-CA.txt" "$base/roadNet-CA.txt.gz"
echo "SNAP datasets ready in $DATA"
