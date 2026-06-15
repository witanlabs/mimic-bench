You need to infer and implement the Excel-compatible behavior of `DURATION`.

The oracle evaluates `=DURATION(...)` with the arguments you provide.

Accepted arities: 5, 6, 7.

Each argument is an Excel formula literal encoded as a JSON string. Examples include `"1"`, `"\"text\""`, `"DATE(2020,1,1)"`, and `"{1;2;3}"`.

The oracle query budget is configured by the benchmark runner and exposed as `QUERY_BUDGET`; when unset, it defaults to 256.

Query the operator with:

```bash
oracle-query < inputs.jsonl
```

Each input line must be JSON:

```json
{"args":["1","\"kg\"","\"lbm\""]}
```

Each oracle output line is JSON:

```json
{"value":0.45359237,"error":null}
{"value":null,"error":"#VALUE!"}
```

Protocol errors, such as exceeding the query budget, are not part of the operator behavior.
The oracle is backed by an Excel-compatible formula engine; match the observed oracle behavior exactly, including error codes, coercions, and array-shaped values.

Create an executable at:

```bash
/app/solution/solve
```

It must read JSONL inputs from stdin and write one JSONL output per input to stdout using the same output format as the oracle.

When finished, package your solution for grading:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The grader will run your submitted CLI on fixed hidden evaluation inputs and compute expected outputs with its own trusted oracle. The rollout oracle service will not be reachable during grading.
