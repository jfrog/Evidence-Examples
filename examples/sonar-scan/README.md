## Sonar evidence creation

This example shows how to create and attach Sonar analysis evidence using the JFrog CLI.

### Prerequisites
- SONAR_TOKEN: SonarCloud/SonarQube token.
- A completed Sonar scan that produced a `report-task.txt` file.

### Default report-task.txt discovery
When you run:
```bash
jf evd create --integration sonar
```
the tool auto-detects the Sonar task file using these paths (in order):
- target/sonar/report-task.txt (Maven)
- build/sonar/report-task.txt (Gradle)
- .scannerwork/report-task.txt (CLI scanner)
- .sonarqube/out/.sonar/report-task.txt (MSBuild)

If the file is not found, configure its location via YAML or env var (see below).

### Minimal workflow step (example)
```yaml
- name: Create evidence
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  run: |
    jf evd create \
      --build-name $GITHUB_WORKFLOW \
      --build-number "${{ github.run_number }}" \
      --key "${{ secrets.SIGNING_KEY }}" \
      --key-alias ${{ vars.SIGNING_KEY_ALIAS }} \
      --integration sonar
```

### Configuration
You can configure the integration via YAML or environment variables. YAML keys have 1:1 env equivalents.

1) YAML: ./jfrog/evidence/evidence.yml
```yaml
sonar:
  url: https://sonarcloud.io
  reportTaskFile: .scannerwork/report-task.txt
  pollingMaxRetries: 30
  pollingRetryIntervalMs: 5000
```

2) Environment variables
- SONAR_URL
- SONAR_REPORT_TASK_FILE
- SONAR_POLLING_MAX_RETRIES
- SONAR_POLLING_RETRY_INTERVAL_MS

### Parameters reference
Evidence creation:

- --integration sonar
  - Selects the Sonar integration.

Sonar resolution (via YAML/env):

- sonar.url / SONAR_URL
  - Sonar base URL. By default url is parsed from report-task.txt. If not found there, defaults to https://sonarcloud.io.

- sonar.reportTaskFile / SONAR_REPORT_TASK_FILE
  - Path to report-task.txt. If omitted, auto-detection (see order above) is used.

- sonar.pollingMaxRetries / SONAR_POLLING_MAX_RETRIES
  - Maximum polling attempts to wait for analysis results.

- sonar.pollingRetryIntervalMs / SONAR_POLLING_RETRY_INTERVAL_MS
  - Milliseconds to wait between polling attempts.

### Behavior
Evidence is created for both successful and failed Sonar analyses (including failed quality gates).
