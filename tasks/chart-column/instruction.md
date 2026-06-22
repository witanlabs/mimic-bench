You need to implement a renderer for a small Excel-compatible column chart subset.

Each input line is a JSON object with:

- `sheets`: workbook sheet data
- `chart`: a JSON chart specification

The oracle returns the reference PNG rendering for that chart and sheet data. All renders use PNG output at dpr 1 and zoom 1.

Query the oracle with:

```bash
oracle-query < inputs.jsonl
```

Each oracle output line is JSON:

```json
{"contentType":"image/png","pixelWidth":318,"pixelHeight":210,"data":"...base64 png bytes..."}
```

Protocol errors, such as exceeding the query budget, are not part of the chart behavior.

Create an executable at:

```bash
/app/solution/solve
```

It must read JSONL inputs from stdin and write one JSONL output per input to stdout using the same output format as the oracle. The output must always be PNG at dpr 1 and zoom 1.

You may implement the renderer in any language. Python, Node, npm, and uv are available. If your solution needs third-party dependencies at grading time, put a `package.json` or `pyproject.toml` inside `/app/solution`; the grader will install those dependencies before running `/app/solution/solve`.

When finished, package your solution for grading:

```bash
mkdir -p /logs/artifacts
tar -czf /logs/artifacts/submission.tgz -C /app solution
```

The grader will run your submitted CLI on fixed hidden evaluation inputs and compare the rendered PNGs against its own trusted oracle using full-image MS-SSIM. The rollout oracle service will not be reachable during grading.

Example input:

```json
{"sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Quarter"},{"address":"B1","value":"Sales"},{"address":"A2","value":"Q1"},{"address":"B2","value":12},{"address":"A3","value":"Q2"},{"address":"B3","value":19},{"address":"A4","value":"Q3"},{"address":"B4","value":7},{"address":"A5","value":"Q4"},{"address":"B5","value":15}]}],"chart":{"name":"SalesColumn","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"column","grouping":"standard","gapWidth":150,"series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","fillColor":"#4472C4"}]}],"title":{"text":"Quarterly Sales"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Quarter"},"reversed":false},"value":{"title":{"text":"Sales"},"min":null,"max":null,"majorUnit":null}}}}
```
