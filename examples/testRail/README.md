# TestRail Evidence Integration Example

This repository provides a working example of a GitHub Actions workflow that orchestrates a complete testing lifecycle. It builds a Docker image, runs automated E2E tests, uploads the results to a TestRail test run, and simultaneously attaches the same results as signed, verifiable evidence to the image in JFrog Artifactory.

This workflow bridges the gap between your Test Case Management (TCM) system and your artifact repository, providing comprehensive traceability for quality assurance.

## Overview

The workflow builds a Docker image, runs automated tests, uploads test results to TestRail, generates test result evidence (JSON and Markdown), pushes the image to Artifactory, and attaches the signed TestRail test results as evidence to the image package. This enables traceability and compliance for testing in your CI/CD pipeline with TestRail integration.

### **Key Features**

* **Automated E2E Testing**: Uses **Cypress** to run a full suite of end-to-end tests against a live application.  
* **Dual-Format Reporting**: Generates test reports in two formats: **JUnit XML** for TestRail compatibility and **JSON** for rich data evidence.  
* **TestRail Integration**: Leverages the `gurock/trcli-action` to automatically upload test results to a specified project in TestRail, creating or updating test runs.  
* **Optional Markdown Summary**: Includes a script to generate a human-readable Markdown report from the JSON test results.  
* **Signed Evidence Attachment**: Attaches the JSON test report as a predicate to the corresponding Docker image in Artifactory, cryptographically signing the evidence for integrity.

## Prerequisites

- JFrog CLI 2.65.0 or above (installed automatically in the workflow)
- Artifactory configured as a Docker registry
- TestRail instance with API access
- The following GitHub repository variables:
    - `JF_URL` (Artifactory Docker registry domain, e.g. `mycompany.jfrog.io`)
    - `ARTIFACTORY_URL` (Artifactory base URL)
- The following GitHub repository secrets:
    - `JF_ACCESS_TOKEN` (Artifactory access token)
    - `PRIVATE_KEY` (Private key for signing evidence)
    - `PRIVATE_KEY_ALIAS` (Key alias for signing evidence)
    - `TESTRAIL_HOST` (TestRail instance URL)
    - `TESTRAIL_USERNAME` (TestRail username)
    - `TESTRAIL_API_KEY` (TestRail API key)

## Environment Variables Used

- `REGISTRY_URL` - Docker registry domain (from `JF_URL`)
- `REPO_NAME` - Docker repository name
- `IMAGE_NAME` - Docker image name
- `TAG_NAME` - Docker image tag (uses GitHub run number)
- `BUILD_NAME` - Build name for Artifactory
- `BUILD_NUMBER` - Build number (uses GitHub run number)
- `ATTACH_OPTIONAL_MARKDOWN_TO_EVIDENCE` - Set to `true` to attach a Markdown report as evidence

## Workflow

```mermaid
graph TD
    A[Workflow Dispatch Trigger] --> B[Setup JFrog CLI]
    B --> C[Checkout Repository]
    C --> D[Build and Publish Docker Image]
    D --> E[Run Automated Tests]
    E --> F[Merge Test Run Results]
    F --> G[Upload Results to TestRail]
    G --> H{Attach Optional Markdown Report?}
    H -->|Yes| I[Generate Markdown Report]
    H -->|No| J[Skip Markdown Report]
    I --> K[Attach Evidence to Package]
    J --> K[Attach Evidence to Package]
```

## Example Usage

You can trigger the workflow manually from the GitHub Actions tab. The workflow will:

- Build and test the Docker image
- Run Automated Tests
- Merge test results (JSON and JUnit XML)
- Upload test results to TestRail
- Push the image to Artifactory
- Attach the TestRail test results as evidence

## Key Commands Used

- **Build and Push Docker Image:**
  The workflow first builds a Docker image and pushes it to Artifactory. This image serves as the "subject" for the test results. The associated build information is also published.
  
  ```bash
  docker build . --file ./examples/testRail/Dockerfile --tag $REGISTRY_URL/$REPO_NAME/$IMAGE_NAME:$TAG_NAME
  jf rt docker-push $REGISTRY_URL/$REPO_NAME/$IMAGE_NAME:$TAG_NAME $REPO_NAME --build-name=$BUILD_NAME --build-number=$BUILD_NUMBER
  jf rt build-publish $BUILD_NAME $BUILD_NUMBER
  ```

- **Run Automated Tests:**
  This step uses the `cypress-io/github-action` to run the end-to-end tests. Note that `continue-on-error: true` is used, ensuring that even failed test results are reported and attached as evidence.
  
  ```yaml
  uses: cypress-io/github-action@v6
  with:
    install: true
    install-command: npm install
    start: npm run start
    quiet: true
    wait-on: 'http://localhost:3000/app.html'
    wait-on-timeout: 120
    working-directory: examples/testRail
  continue-on-error: true

- **Upload Results to TestRail:**
  The raw test results are merged into two distinct formats for different purposes: a `junit-report.xml` file for TestRail and an `overall-report.json` file for the Artifactory evidence.
  Using the `gurock/trcli-action`, the workflow uploads the `junit-report.xml` to your TestRail project, automatically creating a new test run and populating it with the results.
  
  ```yaml
  uses: gurock/trcli-action@main
  with:
    host: ${{ secrets.TESTRAIL_HOST }}
    username: ${{ secrets.TESTRAIL_USERNAME }}
    password: ${{ secrets.TESTRAIL_API_KEY }}
    project: 'TestRail Project'
    report_file_path: './examples/testRail/reports/junit-report.xml'
    title: 'Automated Test Run Results'
    run_description: 'GitHub Workflow Run Id: $BUILD_NUMBER'
    auto_create_cases_yes: 'true'
    close_run: 'true'
  ```

- **Attach Evidence:**
  Finally, the workflow attaches the `overall-report.json` to the Docker image in Artifactory using `jf evd create`. This creates a permanent, tamper-proof link between the artifact and its detailed test results.
  
  ```bash
  jf evd create \
  --package-name $IMAGE_NAME \
  --package-version $TAG_NAME \
  --package-repo-name $REPO_NAME \
  --key "${{ secrets.PRIVATE_KEY }}" \
  --key-alias "${{ secrets.PRIVATE_KEY_ALIAS }}" \
  --predicate "reports/overall-report.json" \
  --predicate-type "http://testrail.com/test-results" \
  --provider-id "testrail" \
  [--markdown "reports/results.md"]
  ```
    The --markdown flag is included only if ATTACH_OPTIONAL_MARKDOWN_TO_EVIDENCE is set to true.

## References
- [TestRail API Documentation](https://support.testrail.com/hc/en-ust)
- [JFrog Evidence Management](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management)
- [JFrog CLI Documentation](https://jfrog.com/getcli/)
