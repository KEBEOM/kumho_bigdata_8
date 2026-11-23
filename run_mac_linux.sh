#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
for candidate in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python3.9; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" start.py --check >/dev/null 2>&1; then
    exec "$candidate" start.py "$@"
  fi
done
echo "지원하는 64비트 Python 3.9~3.14가 없습니다. README.txt를 확인해 주세요."
exit 1
