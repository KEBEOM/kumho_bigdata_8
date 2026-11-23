#!/bin/bash
cd -- "$(dirname -- "$0")"
bash run_mac_linux.sh "$@"
code=$?
if [ "$code" -ne 0 ]; then
  read -r -p "오류를 확인한 뒤 Enter를 눌러 닫으세요. " _answer
fi
exit "$code"
