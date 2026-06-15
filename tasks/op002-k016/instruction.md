You need to infer and implement an unknown scalar operator.

The operator has arity 2. Each argument is an Excel-like scalar: finite number, string, boolean, blank-like `null`, or error object.

You may query the operator at most 16 times with:

```bash
oracle-query < inputs.jsonl
```

Each input line must be JSON:

```json
{"args":[3, "4"]}
```

Each oracle output line is JSON:

```json
{"value":11.5,"error":null}
{"value":null,"error":"#VALUE!"}
```

Protocol errors, such as exceeding the query budget, are not part of the operator behavior.
The oracle is backed by an Excel-compatible formula engine; match the observed oracle behavior exactly, including error codes and coercions.

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
