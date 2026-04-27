#!/usr/bin/env bash
# v0.5 demo smoke test. Run AFTER `uvicorn main:app --port 8000`.
# Checks every new endpoint and reports status. Does not require LLM credentials
# for the structural endpoints (status/verify); the LLM-bound ones (multi-lens,
# persona) will report whether OPENROUTER_API_KEY is set.

set -u
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"
URL="http://$HOST:$PORT"

ok=0; fail=0
print() { printf "  %s\n" "$1"; }
green(){ printf "\033[32m%s\033[0m" "$1"; }
red()  { printf "\033[31m%s\033[0m" "$1"; }

check() {
  local name="$1"; local cmd="$2"
  printf "%-32s … " "$name"
  if eval "$cmd" >/dev/null 2>&1; then
    green "PASS"; printf "\n"; ok=$((ok+1))
  else
    red "FAIL"; printf "\n"; fail=$((fail+1))
  fi
}

echo "== Backend reachability =="
check "GET /api/health"      "curl -fs $URL/api/health"
check "GET /api/v05/status"  "curl -fs $URL/api/v05/status"

echo
echo "== v0.5 endpoints (no LLM required) =="
check "POST /api/verify (HH eq.)" \
  "curl -fs -XPOST $URL/api/verify -H 'Content-Type: application/json' -d '{\"lhs\":\"x+1\",\"rhs\":\"1+x\"}'"

echo
echo "== v0.5 endpoints (DB required) =="
check "GET /api/srs/queue?user_id=1"  "curl -fs '$URL/api/srs/queue?user_id=1'"
check "GET /api/bank/next?user_id=1"  "curl -fs '$URL/api/bank/next?user_id=1'"

echo
echo "== v0.5 endpoints (LLM required) =="
check "POST /api/persona/wrap" \
  "curl -fs -XPOST $URL/api/persona/wrap -H 'Content-Type: application/json' -d '{\"text\":\"Nernst 식은 막전위를 결정하는 기본 식입니다.\",\"streak_days\":3}'"
check "POST /api/review/multi-lens" \
  "curl -fs -XPOST $URL/api/review/multi-lens -H 'Content-Type: application/json' -d '{\"text\":\"E_X = (RT/zF) ln([X]_o/[X]_i)\",\"declared_difficulty\":2,\"declared_bloom\":\"Remember\",\"citation\":{\"kind\":\"slide\",\"lecture\":\"L3\",\"page\":12}}'"

echo
echo "Summary: $(green "$ok pass") · $(red "$fail fail")"
echo
echo "If any fail: (1) check uvicorn is up on :$PORT, (2) DB endpoints need migrations applied + seed_bank_demo.py, (3) LLM endpoints need OPENROUTER_API_KEY."
