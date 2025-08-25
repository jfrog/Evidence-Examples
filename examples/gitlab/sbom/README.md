# GitLab SBOM Evidence Example

This repository provides a working example of a GitLab CI/CD pipeline that builds a Docker image, generates a Software Bill of Materials (SBOM) using GitLab's native Container Scanning, and attaches the SBOM as signed, verifiable evidence to the image in JFrog Artifactory.

This workflow is a key DevSecOps practice, creating a transparent and auditable inventory of all components within your container images, directly from your CI/CD process.

## Overview

The pipeline builds a Docker image, generates a CycloneDX SBOM, converts the SBOM JSON to Markdown, pushes the image to Artifactory, and attaches the signed SBOM as evidence to the image package. This enables traceability and compliance for your container images in CI/CD.

### Key Features

* **Automated Docker Build**: Builds a Docker image and pushes it to Artifactory.  
* **Native SBOM Generation**: Leverages GitLab's built-in Container Scanning feature to automatically generate a CycloneDX SBOM.  
* **Optional Markdown Summary**: Includes a helper script to generate a human-readable Markdown report from the SBOM data.  
* **Signed Evidence Attachment**: Attaches the JSON SBOM as a predicate to the corresponding Docker image in Artifactory, cryptographically signing it for integrity.

## Prerequisites

- JFrog CLI 2.65.0 or above (installed automatically in the pipeline)
- Artifactory configured as a Docker registry
- The following GitLab CI/CD variables:
    - `REGISTRY_URL` (Artifactory Docker registry domain, e.g. `mycompany.jfrog.io`)
    - `ARTIFACTORY_URL` (Artifactory base URL)
    - `ARTIFACTORY_ACCESS_TOKEN` (Artifactory access token)
    - `REGISTRY_USER` (Docker registry user)
    - `REGISTRY_PASSWORD` (Docker registry password)
    - `PRIVATE_KEY` (Private key for signing evidence)
    - `PRIVATE_KEY_ALIAS` (Key alias for signing evidence)

## Environment Variables Used

- `REPO_NAME` - Docker repository name
- `BUILD_NAME` - Build name for Artifactory
- `BUILD_NUMBER` - Build number (uses GitLab pipeline ID)
- `PACKAGE_NAME` - Docker image name
- `PACKAGE_VERSION` - Docker image tag (uses Git commit short SHA)
- `PREDICATE_FILE` - Path to SBOM JSON file
- `PREDICATE_TYPE` - Predicate type URL for SBOM
- `DOCKER_IMAGE_NAME_WITH_TAG` - Full Docker image name with tag
- `MARKDOWN_FILE` - Path to the generated Markdown file from SBOM

## Pipeline Stages

1. **Build and Push Docker Image**
    - Builds the Docker image using the provided Dockerfile and pushes it to Artifactory.
2. **Container Scanning**
    - Scans the pushed Docker image for vulnerabilities.
3. **Generate Markdown from SBOM and Attach Evidence**
    - Converts the CycloneDX SBOM JSON to Markdown.
    - Attaches the SBOM (JSON and Markdown) as signed evidence to the Docker image package in Artifactory.
    - 
## Example Usage

Trigger the pipeline in GitLab CI/CD. The pipeline will:

- Build and push the Docker image
- Generate and convert the SBOM
- Push the image to Artifactory
- Attach the SBOM as evidence

## Key Commands Used

- **Build Docker Image:**
  The pipeline first builds a Docker image from the specified Dockerfile and then pushes it to your Artifactory instance using the JFrog CLI.
  ```bash
  docker build -f ./examples/gitlab/sbom/Dockerfile -t $DOCKER_IMAGE_NAME_WITH_TAG ./examples/gitlab/sbom
  ```
- **Push Docker Image:**
  ```bash
  jf rt docker-push $DOCKER_IMAGE_NAME_WITH_TAG $REPO_NAME --build-name=$BUILD_NAME --build-number=$BUILD_NUMBER
  ```
- **Convert SBOM JSON to Markdown:**
  This stage leverages GitLab's native security capabilities. By including the `Container-Scanning.gitlab-ci.yml` template in your main pipeline configuration, GitLab automatically runs a scanner against the image built in the previous stage. A key output of this scan is a `gl-container-scanning-report.json` artifact, which contains a detailed SBOM in CycloneDX format.
  ```bash
  python3 json-to-md.py
  ```
- **Attach Evidence:**
  The jf evd create command attaches the original SBOM report to the Docker image package in Artifactory. This creates a permanent, tamper-proof link between your image and its complete list of software components.
  ```bash
  jf evd create --package-name="${PACKAGE_NAME}" --package-version="${PACKAGE_VERSION}" --package-repo-name="${REPO_NAME}" --key="${PRIVATE_KEY}" --key-alias="${PRIVATE_KEY_ALIAS}" --predicate="${PREDICATE_FILE}" --predicate-type="${PREDICATE_TYPE}" --provider-id="gitlab" --markdown="${MARKDOWN_FILE}"
  ```

## References

- [Gitlab Container Scanning](https://docs.gitlab.com/user/application_security/container_scanning/)
- [CycloneDX SBOM Specification](https://cyclonedx.org/)
- [JFrog Evidence Management](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management)
- [JFrog CLI Documentation](https://jfrog.com/getcli/)
