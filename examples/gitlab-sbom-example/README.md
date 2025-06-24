# GitLab SBOM Evidence Example

This project demonstrates how to automate Docker image builds, generate SBOM (Software Bill of Materials) reports, convert them to Markdown, and attach the signed SBOM evidence to the Docker image in JFrog Artifactory using GitLab CI/CD and JFrog CLI.

## Overview

The pipeline builds a Docker image, generates a CycloneDX SBOM, converts the SBOM JSON to Markdown, pushes the image to Artifactory, and attaches the signed SBOM as evidence to the image package. This enables traceability and compliance for your container images in CI/CD.

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
  ```bash
  docker build -f ./examples/gitlab-sbom/Dockerfile -t $DOCKER_IMAGE_NAME_WITH_TAG ./examples/gitlab-sbom
  ```
- **Push Docker Image:**
  ```bash
  jf rt docker-push $DOCKER_IMAGE_NAME_WITH_TAG $REPO_NAME --build-name=$BUILD_NAME --build-number=$BUILD_NUMBER
  ```
- **Convert SBOM JSON to Markdown:**
  ```bash
  python3 json-to-md.py
  ```
- **Attach Evidence:**
  ```bash
  jf evd create --package-name="${PACKAGE_NAME}" --package-version="${PACKAGE_VERSION}" --package-repo-name="${REPO_NAME}" --key="${PRIVATE_KEY}" --key-alias="${PRIVATE_KEY_ALIAS}" --predicate="${PREDICATE_FILE}" --predicate-type="${PREDICATE_TYPE}" --markdown="${MARKDOWN_FILE}"
  ```

## References

- [Gitlab Container Scanning](https://docs.gitlab.com/user/application_security/container_scanning/)
- [CycloneDX SBOM Specification](https://cyclonedx.org/)
- [JFrog Evidence Management](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management)
- [JFrog CLI Documentation](https://jfrog.com/getcli/)