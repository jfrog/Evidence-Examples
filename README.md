
# **Attach Evidence in Artifactory**

This repository provides a comprehensive, hands-on example of how to create and attach signed evidence to your software assets at every stage of the development lifecycle using **JFrog Artifactory** and **JFrog CLI**.

By following this guide, you will learn how to build a verifiable, auditable trail for your software, from a single artifact to an immutable Release Bundle. This is a foundational practice for securing your software supply chain and enabling automated, policy-driven governance.

### **What You'll Accomplish**

* **Build and Publish** a multi-platform Docker image.
* **Attach Signed Evidence** to four distinct types of subjects:
    1. A **Generic Artifact** (a README.md file).
    2. A **Software Package** (eg: a Docker image, npm, go,…etc).
    3. A **Build Info** object (the CI build record).
    4. An immutable **Release Bundle v2**.
* **Understand the "Why"**: Learn how this chain of evidence enables secure, policy-based promotions.

### **The Evidence Journey:**

The GitHub Actions workflow (.github/workflows/build.yml) performs a sequence of operations to build a chain of trust. Evidence is attached at each critical step.

### **Note**

For more information about evidence on the JFrog platform, see [Evidence Management](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management).

```mermaid
graph TD
    subgraph "1. Build & Initial Evidence"
        A[Start] --> B(Build & Push Docker Image);
        B --> C{Attach Evidence to Package};
        D[Upload README.md] --> E{Attach Evidence to Generic File};
    end

    subgraph "2. Aggregate into a Build"
        C --> F(Publish Build Info);
        E --> F;
        F --> G{Attach Evidence to Build};
    end

    subgraph "3. Create Immutable Release"
        G --> H(Create Release Bundle v2 from Build);
        H --> I{Attach Evidence to Release Bundle};
    end

    subgraph "4. Enable Governance"
        I --> J[Ready for Secure Promotion with Policy Checks];
    end
```

## Getting Started: Prerequisites & Configuration

Before running the workflow, please ensure you have the following set up.

### Prerequisites

Make sure JFrog CLI 2.65.0 or above is installed and in your system PATH. For installation instructions, see Install JFrog CLI.

Make sure Artifactory can be used as a Docker registry. Please refer to Getting Started with Artifactory as a Docker Registry in the JFrog Artifactory User Guide. You should end up with a Docker registry URL, which is mapped to a local Docker repository (or a virtual Docker repository with a local deployment target) in Artifactory. You'll need to know the name of the Docker repository to later collect the published image build-info.

Make sure the following repository variables are configured in GitHub settings:

ARTIFACTORY_URL (location of your Artifactory installation)

BUILD_NAME (planned name for the build of the Docker image)

BUNDLE_NAME (planned name for the Release Bundle created from the build)

Make sure the following repository secrets are configured in GitHub settings:

ARTIFACTORY_ACCESS_TOKEN (access token used for authentication)

JF_USER (your username in Artifactory)

PRIVATE_KEY (the key used to sign evidence)

### GitHub Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| ARTIFACTORY_ACCESS_TOKEN | A valid JFrog Access Token with permissions to deploy and annotate. | |
| JF_USER | Your JFrog Platform username, used for the docker login action. | my-user |
| PRIVATE_KEY | The raw private key used to sign all evidence created in the workflow. | -----BEGIN PRIVATE KEY-----... |

### GitHub Variables

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| ARTIFACTORY_URL | The base URL of your JFrog Platform instance. | https://mycompany.jfrog.io |
| BUILD_NAME | A unique name for the build information in Artifactory. | evidence-example-build |
| BUNDLE_NAME | The name of the Release Bundle that will be created. | evidence-example-bundle |

## The Evidence Journey: Step-by-Step

This workflow demonstrates how evidence adds value at different levels of abstraction. For the complete implementation, please refer to the build.yml workflow file.

### Install JFrog CLI

This step uses the jfrog/setup-jfrog-cli action to install the JFrog CLI into the GitHub Actions runner and configures it with your Artifactory URL and access token.

```yaml
jobs:  
  Docker-build-with-evidence:  
    runs-on: ubuntu-latest  
    steps:  
      - name: Install jfrog cli  
        uses: jfrog/setup-jfrog-cli@v4  
        env:  
          JF_URL: ${{ vars.ARTIFACTORY_URL }}  
          JF_ACCESS_TOKEN: ${{ secrets.ARTIFACTORY_ACCESS_TOKEN }}

      - uses: actions/checkout@v4
```

### Log In to the Artifactory Docker Registry

Here, we securely log in to the Artifactory Docker registry. This step also sets up QEMU and Docker Buildx, which are required to build multi-platform Docker images (e.g., for linux/amd64 and linux/arm64).

```yaml
 - name: Log in to Artifactory Docker Registry  
   uses: docker/login-action@v3  
   with:  
     registry: ${{ vars.ARTIFACTORY_URL }}  
     username: ${{ secrets.JF_USER }}  
     password: ${{ secrets.ARTIFACTORY_ACCESS_TOKEN }}

 - name: Set up QEMU  
   uses: docker/setup-qemu-action@v3

 - name: Set up Docker Buildx  
   uses: docker/setup-buildx-action@v3  
   with:  
     platforms: linux/amd64,linux/arm64  
     install: true
```

### Build the Docker Image

This step builds a multi-platform Docker image using the provided Dockerfile and pushes it to your Artifactory repository. The jfrog rt build-docker-create command captures the image details and temporarily associates them with a build name and number in the local JFrog CLI cache, laying the groundwork for creating the final Build Info object.

```yaml
 - name: Build Docker image  
   run: |
     URL=$(echo ${{ vars.ARTIFACTORY_URL }} | sed 's|^https://||')
     REPO_URL=${URL}'/example-project-docker-dev-virtual'
     docker build --build-arg REPO_URL=${REPO_URL} -f Dockerfile . \
     --tag ${REPO_URL}/example-project-app:${{ github.run_number }} \
     --output=type=image --platform linux/amd64 --metadata-file=build-metadata --push
     jfrog rt build-docker-create example-project-docker-dev --image-file build-metadata --build-name ${{ vars.BUILD_NAME }} --build-number ${{ github.run_number }}
```

### Attach Package Evidence

Now we attach the first piece of evidence directly to the Docker image package. This signed evidence acts as a verifiable record, attesting that a specific action (like a signature from a CI process) was performed on this package version.

```yaml
- name: Evidence on docker  
  run: |
    echo '{ "actor": "${{ github.actor }}", "date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'" }' > sign.json
    jf evd create --package-name example-project-app --package-version 32 --package-repo-name example-project-docker-dev \
      --key "${{ secrets.PRIVATE_KEY }}" \
      --predicate ./sign.json --predicate-type https://jfrog.com/evidence/signature/v1
    echo ' Evidence attached: `signature` '
```

### Upload README File and Associated Evidence

To demonstrate that evidence can be attached to any artifact, not just packages, this step uploads the README.md file to a generic repository and attaches similar signed evidence to it.

```yaml
- name: Upload readme file  
  run: |
    jf rt upload ./README.md example-project-generic-dev/readme/${{ github.run_number }}/ --build-name ${{ vars.BUILD_NAME }} --build-number ${{ github.run_number }}
    jf evd create --subject-repo-path example-project-generic-dev/readme/${{ github.run_number }}/README.md \
      --key "${{ secrets.PRIVATE_KEY }}" \
      --predicate ./sign.json --predicate-type https://jfrog.com/evidence/signature/v1
```

The crucial flags --build-name and --build-number in the jf rt upload command ensure this uploaded artifact is also added to the local build info record created in the previous step.

### Publish Build Info and Attach Build Evidence

This step performs the final action: it aggregates all previously linked artifacts (the Docker image from build-docker-create and the README from jf rt upload) and their metadata, which are stored locally in the CLI's temporary cache, and publishes this comprehensive Build Info object to Artifactory. Immediately after, it attaches signed evidence to this entire build, attesting to the integrity of the build process itself.

```yaml
  - name: Publish build info  
    run: jfrog rt build-publish ${{ vars.BUILD_NAME }} ${{ github.run_number }}

  - name: Sign build evidence  
    run: |
      echo '{ "actor": "${{ github.actor }}", "date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'" }' > sign.json
      jf evd create --build-name ${{ vars.BUILD_NAME }} --build-number ${{ github.run_number }} \
        --predicate ./sign.json --predicate-type https://jfrog.com/evidence/build-signature/v1 \
        --key "${{ secrets.PRIVATE_KEY }}"
      echo ' Evidence attached: `build-signature` ' >> $GITHUB_STEP_SUMMARY
```

### Create a Release Bundle v2 from the Build

The workflow now creates an immutable Release Bundle from the build we just published. This bundle is a tamper-proof, versioned collection that is ideal for promoting through your SDLC stages.

```yaml
- name: Create release bundle  
  run: |
    echo '{ "files": [ {"build": "'"${{ vars.BUILD_NAME }}/${{ github.run_number }}"'" } ] }' > bundle-spec.json
    jf release-bundle-create ${{ vars.BUNDLE_NAME }} ${{ github.run_number }} --signing-key PGP-RSA-2048 --spec bundle-spec.json --sync=true
    NAME_LINK=${{ vars.ARTIFACTORY_URL }}'/ui/artifactory/lifecycle/?bundleName='${{ vars.BUNDLE_NAME }}'&bundleToFlash='${{ vars.BUNDLE_NAME }}'&repositoryKey=example-project-release-bundles-v2&activeKanbanTab=promotion'
    VER_LINK=${{ vars.ARTIFACTORY_URL }}'/ui/artifactory/lifecycle/?bundleName='${{ vars.BUNDLE_NAME }}'&bundleToFlash='${{ vars.BUNDLE_NAME }}'&releaseBundleVersion='${{ github.run_number }}'&repositoryKey=example-project-release-bundles-v2&activeVersionTab=Version%20Timeline&activeKanbanTab=promotion'
    echo ' Release bundle ['${{ vars.BUNDLE_NAME }}']('${NAME_LINK}'):['${{ github.run_number }}']('${VER_LINK}') created' >> $GITHUB_STEP_SUMMARY
```

### Attach Release Bundle Evidence

Finally, we attach signed evidence to the immutable Release Bundle itself. This could represent a successful integration test or final approval, providing a verifiable gate for promotion to production environments.

```yaml
 - name: Evidence on release-bundle v2  
   run: |
     echo '{ "actor": "${{ github.actor }}", "date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'" }' > rbv2_evidence.json
     JF_LINK=${{ vars.ARTIFACTORY_URL }}'/ui/artifactory/lifecycle/?bundleName='${{ vars.BUNDLE_NAME }}'&bundleToFlash='${{ vars.BUNDLE_NAME }}'&releaseBundleVersion='${{ github.run_number }}'&repositoryKey=release-bundles-v2&activeVersionTab=Version%20Timeline&activeKanbanTab=promotion'
     echo 'Test on Release bundle ['${{ vars.BUNDLE_NAME }}':'${{ github.run_number }}']('${JF_LINK}') success' >> $GITHUB_STEP_SUMMARY
     jf evd create --release-bundle ${{ vars.BUNDLE_NAME }} --release-bundle-version ${{ github.run_number }} \
       --predicate ./rbv2_evidence.json --predicate-type https://jfrog.com/evidence/rbv2-signature/v1 \
       --key "${{ secrets.PRIVATE_KEY }}"
     echo ' Evidence attached: integration-test ' >> $GITHUB_STEP_SUMMARY
```

### Create an External Policy to Potentially Block Release Bundle Promotion

When the Evidence service is used in conjunction with JFrog Xray, each Release Bundle promotion generates evidence in the form of a CycloneDX SBOM. You can create a policy in an external tool (for example, a rego policy) that reviews the contents of the CycloneDX evidence file and decides whether to block the promotion (because the Release Bundle fails to meet all your organization's requirements for promotion to the next stage of your SDLC).

To see a sample rego policy, go here. For more information about integrating Release Lifecycle Management and Evidence with Xray, see Scan Release Bundles (v2) with Xray.

## References

### Product Documentation:

- [Evidence Management Overview](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management)
- [Getting Started with Artifactory as a Docker Registry](https://jfrog.com/help/r/jfrog-artifactory-documentation/getting-started-with-artifactory-as-a-docker-registry)
- [Xray](https://jfrog.com/help/r/xray-release-information/xray-release-notes)

### JFrog CLI Documentation:

- [JFrog CLI Command Reference](https://jfrog.com/help/r/jfrog-applications-and-cli-documentation/jfrog-cli)
- [Release Lifecycle Management with CLI](https://jfrog.com/help/r/jfrog-applications-and-cli-documentation/release-lifecycle-management)