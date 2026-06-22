You need to implement a renderer for a small Excel-compatible waterfall chart subset.

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
{"sheets":[{"name":"Sheet1","cells":[{"address":"A1","value":"Step"},{"address":"B1","value":"Amount"},{"address":"A2","value":"Start"},{"address":"B2","value":100},{"address":"A3","value":"Cost"},{"address":"B3","value":-30},{"address":"A4","value":"Growth"},{"address":"B4","value":50},{"address":"A5","value":"End"},{"address":"B5","value":120}]}],"chart":{"name":"BasicWaterfall","position":{"from":{"cell":"D2","xOffsetPts":0,"yOffsetPts":0},"to":{"cell":"J16","xOffsetPts":0,"yOffsetPts":0}},"groups":[{"type":"waterfall","series":[{"name":{"ref":"Sheet1!B1"},"categories":"Sheet1!A2:A5","values":"Sheet1!B2:B5","totalIndexes":[0,3],"showConnectorLines":true,"fillColor":null}]}],"title":{"text":"Basic Waterfall"},"legend":{"position":"right"},"axes":{"category":{"title":{"text":"Category"}},"value":{"title":{"text":"Value"}}}}}
```
