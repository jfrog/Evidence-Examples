# Create Sonar Scan Evidence predicate from the build CI and attach it to the build info
Sonar is a code scanning tool that helps to identify bugs, vulnerabilities, and code smells in your code. 
It is important to track the code quality and security of the code changes done and released. 
To allow automation of proper code quality and security checks, we create an evidence of the Sonar scan results
during the build with confirmation that the code quality and security checks passed before the code was committed.
using the `FailOnAnalysisFailure` argument the customer can decide if to create the sonar scan evidence if the scan did not pass 
sonar quality gates, or fail the predicate creation with exist status 1.
If the Analysis status is not 'OK', but `FailOnAnalysisFailure` was not set, then the predicate is created with analysis.status = 'ERROR' which 
should be checked using a policy.

## Environment variables
- `SONAR_TOKEN` - The sonar server token.
- `SONAR_TYPE` - Should be Either SAAS or SELFHOSTED, defaulting to SAAS.
- `SONAR_HOST_URL` - The sonar server host name, for example https://mysonar.mycorp.com, for example sonar.myconpany.org. required for SELFHOSTED type, if not provided for SAAS type sonarcloud.io is used as default.
- `SONAR_PROXY_URL` - The proxy server URL, in the format of http://your-proxy-server:port. or https://username:password@your-proxy-server:port

## Arguments
`--reportTaskFile=<path>` - The path to the sonar report task file.
`--FailOnAnalysisFailure` - Fail with exit code 1 if the sonar analysis failed in sonar quality gate.
`--WaitTime=<seconds>` - between sonar analysis results checks>
`--MaxRetries=<number>` - The maximum number of retries to check the sonar analysis results.
`--UseProxy` - Use a proxy server URL, requires PROXY_URL environment variable to be set.
 
## The example is based on the following steps:
1. set sonar token as an environment variable
2. call sonar scan
for example:
``
$PWD/sonar-scanner-6.2.1.4610/bin/sonar-scanner \
            -Dsonar.projectKey=my-sonar-project-key \
            -Dsonar.organization=my-sonar-org \
            -Dsonar.host.url=https://sonarcloud.io \
            -Dsonar.java.jdkHome=$JAVA_HOME \
            -Dsonar.verbose=true \
            -Dsonar.token=$SONAR_TOKEN
``
3. call the jira-transition-checker utility (use the binary for your build platform) with these arguments: "transition name" JIRA-ID [,JIRA-ID]
for example:
 ``./examples/sonar-scan/bin/sonar-scan-extractor-linux-amd64  --reportTaskFile=$PWD/.scannerwork/report-task.txt --FailOnAnalysisFailure > predicate.json
``               
4. call the evidence create cli with the predicate.json file
for example:
``
jf evd create \
            --build-name $GITHUB_WORKFLOW \
            --build-number "${{ github.run_number }}" \
            --predicate ./predicate.json \
            --predicate-type https://jfrog.com/evidence/sonar-scan/v1 \
            --provider-id "sonar" \
            --key "${{ secrets.JIRA_TEST_PKEY }}" \
            --key-alias ${{ vars.JIRA_TEST_KEY }}
``

## Additional considerations
```plaintext
It is advised to decide if to create an evidence with sonar analysis failure scan or refrain from creating the evidence.
to create the evidence with an analysis gateway failure content, do **not** add the `--FailOnAnalysisFailure` argument.

to refrain from creating the evidence with an analysis gateway failure content, add the `--FailOnAnalysisFailure` argument.
then check the exit code of the script and decide if to create the evidence or not.
```