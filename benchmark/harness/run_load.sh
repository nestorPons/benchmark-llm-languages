#!/usr/bin/env bash
# Load test runner (spec section 6.1): warm-up + sustained load at several
# concurrency levels, repeated measurements.
#
# Usage:
#   run_load.sh <task> <language> [base_url] [tool]
#
# tool: k6 (default, recommended) | oha | wrk
# Env overrides: VUS_LIST="1,10,50" REPS=5 PATH=/health METHOD=GET
#   WARMUP_S=30 HOLD_S=60
#
# Output: results/summary/load/<task>/<language>/<tool>/summary.json
# plus one raw JSON per (vus, rep).

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$HARNESS_DIR")"

TASK="${1:?usage: run_load.sh <task> <language> [base_url] [tool]}"
LANG="${2:?usage: run_load.sh <task> <language> [base_url] [tool]}"
BASE_URL="${3:-http://127.0.0.1:8005}"
TOOL="${4:-k6}"

VUS_LIST="${VUS_LIST:-1,10,50}"
REPS="${REPS:-5}"
PATH_="${PATH_:-/health}"
METHOD="${METHOD_:-GET}"
WARMUP_S="${WARMUP_S:-30}"
HOLD_S="${HOLD_S:-60}"

OUT_DIR="${ROOT_DIR}/results/summary/load/${TASK}/${LANG}/${TOOL}"
mkdir -p "$OUT_DIR"

command -v "$TOOL" >/dev/null 2>&1 || {
  echo "error: '$TOOL' not found in PATH" >&2
  exit 2
}

IFS=',' read -r -a VUS_ARRAY <<< "$VUS_LIST"

SUMMARY=()
SUMMARY_JSON="{\"task\":\"$TASK\",\"language\":\"$LANG\",\"tool\":\"$TOOL\",\"runs\":["

for VUS in "${VUS_ARRAY[@]}"; do
  for REP in $(seq 1 "$REPS"); do
    OUT="${OUT_DIR}/vus${VUS}_rep${REP}.json"
    case "$TOOL" in
      k6)
        K6_SUMMARY="$(mktemp)"
        BASE_URL="$BASE_URL" REQ_PATH="$PATH_" METHOD="$METHOD" \
        VUS="$VUS" WARMUP_S="${WARMUP_S}s" HOLD_S="${HOLD_S}s" \
        "$TOOL" run --quiet --summary-export="$K6_SUMMARY" "$HARNESS_DIR/load_scenario.js" >/dev/null 2>&1
        python3 -c 'import sys,json
d=json.load(open(sys.argv[1])); m=d.get("metrics",{})
def gv(metric,key):
    mm=m.get(metric,{})
    return mm.get(key, mm.get("values",{}).get(key))
print(json.dumps({"vus":int(sys.argv[2]),"rep":int(sys.argv[3]),"http_reqs":gv("http_reqs","rate"),"http_req_duration_p95":gv("http_req_duration","p(95)"),"http_req_duration_p99":gv("http_req_duration","p(99)"),"errors":gv("checks","fails")}))' "$K6_SUMMARY" "$VUS" "$REP" > "$OUT" 2>/dev/null \
          || echo "{\"vus\":$VUS,\"rep\":$REP,\"error\":\"k6 parse failed\"}" > "$OUT"
        rm -f "$K6_SUMMARY"
        ;;
      oha)
        "$TOOL" -z "${HOLD_S}s" -c "$VUS" "$BASE_URL$PATH_" --json > "$OUT" 2>/dev/null \
          || python3 -c 'import json,sys; print(json.dumps({"vus":'"$VUS"',"rep":'"$REP"',"error":"oha failed"}))' > "$OUT"
        ;;
      wrk)
        "$TOOL" -t "$VUS" -c "$VUS" -d "${HOLD_S}s" "$BASE_URL$PATH_" > /dev/null 2>&1 \
          && echo '{"vus":'"$VUS"',"rep":'"$REP"'}' > "$OUT" \
          || python3 -c 'import json; print(json.dumps({"vus":'"$VUS"',"rep":'"$REP"',"error":"wrk failed"}))' > "$OUT"
        ;;
      *)
        echo "error: unsupported tool '$TOOL' (use k6, oha or wrk)" >&2
        exit 2
        ;;
    esac
    SUMMARY+=("$(cat "$OUT")")
    echo "[$TOOL] vus=$VUS rep=$REP done"
  done
done

# Aggregate
IFS=',' SUMMARY_JSON+="${SUMMARY[*]}"
SUMMARY_JSON+=']}'
echo "$SUMMARY_JSON" | python3 -m json.tool > "${OUT_DIR}/summary.json"

echo "Load results written to ${OUT_DIR}/summary.json"
