#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if [[ -x .venv/bin/python ]]; then
  DEMO_PYTHON=.venv/bin/python
elif command -v python3.12 >/dev/null 2>&1; then
  DEMO_PYTHON=python3.12
else
  DEMO_PYTHON=python3
fi
run_exit=0
"$DEMO_PYTHON" run.py setup || run_exit=$?
printf '\n按任意键关闭窗口…'
read -k 1
exit $run_exit
