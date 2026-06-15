#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier

python /tests/shared_grader.py \
  --submission /logs/artifacts/submission.tgz \
  --eval-inputs /tests/eval_inputs.jsonl \
  --query-log /var/log/oracle/queries.jsonl \
  --output /logs/verifier/reward.json
