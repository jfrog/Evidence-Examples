# Attach Evidence in Artifactory

Artifactory enables you to attach evidence (signed metadata) to a designated subject, such as an artifact, build, package, or Release Bundle v2. These evidence files provide a record of an external process performed on the subject, such as test results, vulnerability scans, or official approval.

This document describes how to use the JFrog CLI to create different types of evidence related to a Docker image deployed to Artifactory, including:

* Package evidence
* Generic evidence
* Build evidence
* Release Bundle evidence   

The following workflow is described:

1. [Bootstrapping](#bootstrapping)  
   1. [Install JFrog CLI](#install-jfrog-cli)  
   2. [Log In to the Artifactory Docker Registry](#log-in-to-the-artifactory-docker-registry)  
2. [Build the Docker Image](#build-the-docker-image)  
3. [Attach Package Evidence](#attach-package-evidence)  
4. [Upload README File and Associated Evidence](#upload-readme-file-and-associated-evidence)  
5. [Publish Build Info and Attach Build Evidence](#publish-build-info-and-attach-build-evidence)  
6. [Create a Release Bundle v2 from the Build](#create-a-release-bundle-v2-from-the-build)  
7. [Attach Release Bundle Evidence](#attach-release-bundle-evidence)
8. [Create an External Policy to Potentially Block Release Bundle Promotion](#create-external-policy-to-block-rb-promotion)

Refer to [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) for the complete script.

***

## Note

For more information about evidence on the JFrog platform, see Evidence Management.
***

## Prerequisites {#prerequisites}

* Make sure JFrog CLI 2.65.0 or above is installed and in your system PATH. For installation instructions, see [Install JFrog CLI](#bootstrapping).  
* Make sure Artifactory can be used as a Docker registry. Please refer to [Getting Started with Artifactory as a Docker Registry](https://www.jfrog.com/confluence/display/JFROG/Getting+Started+with+Artifactory+as+a+Docker+Registry) in the JFrog Artifactory User Guide. You should end up with a Docker registry URL, which is mapped to a local Docker repository (or a virtual Docker repository with a local deployment target) in Artifactory. You'll need to know the name of the Docker repository to later collect the published image build-info.  
* Make sure the following repository variables are configured in GitHub settings:  
  * ARTIFACTORY_URL (location of your Artifactory installation)  
  * BUILD_NAME (planned name for the build of the Docker image)  
  * BUNDLE_NAME (planned name for the Release Bundle created from the build)  
* Make sure the following repository secrets are configured in GitHub settings:  
  * ARTIFACTORY_ACCESS_TOKEN (access token used for authentication)  
  * JF_USER (your username in Artifactory)  
  * PRIVATE_KEY (the key used to sign evidence)



## Bootstrapping  {#bootstrapping}

### Install JFrog CLI {#install-jfrog-cli}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) installs the latest version of the JFrog CLI and performs checkout. Please note that a valid access token is required. 

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

### Log In to the Artifactory Docker Registry {#log-in-to-the-artifactory-docker-registry}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) logs into the Docker registry, as described in the [prerequisites](#prerequisites), and sets up QEMU and Docker Buildx in preparation for building the Docker image.

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

## Build the Docker Image {#build-the-docker-image}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) builds the Docker image and deploys it to Artifactory.

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

## Attach Package Evidence {#attach-package-evidence}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) creates evidence for the package containing the Docker image. The evidence is signed with your private key, as defined in the [Prerequisites](#prerequisites).

```yaml
- name: Evidence on docker  
  run: |  
     echo '{ "actor": "${{ github.actor }}", "date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'" }' > sign.json  
     jf evd create --package-name example-project-app --package-version 32 --package-repo-name example-project-docker-dev \  
       --key "${{ secrets.PRIVATE_KEY }}" \  
       --predicate ./sign.json --predicate-type https://jfrog.com/evidence/signature/v1   
     echo ' Evidence attached: `signature` ' 
```

## Upload README File and Associated Evidence {#upload-readme-file-and-associated-evidence}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) uploads the README file and creates signed evidence about this generic artifact. The purpose of this section is to demonstrate the ability to create evidence for any type of file uploaded to Artifactory, in addition to packages, builds, and Release Bundles.

```yaml
- name: Upload readme file  
  run: |  
    jf rt upload ./README.md example-project-generic-dev/readme/${{ github.run\_number }}/ --build-name ${{ vars.BUILD_NAME }} --build-number ${{ github.run_number }}  
    jf evd create --subject-repo-path example-project-generic-dev/readme/${{ github.run_number }}/README.md \  
      --key "${{ secrets.PRIVATE_KEY }}" \  
      --predicate ./sign.json --predicate-type https://jfrog.com/evidence/signature/v1
```

## Publish Build Info and Attach Build Evidence {#publish-build-info-and-attach-build-evidence}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) creates a build from the package containing the Docker image and then creates signed evidence attesting to its creation.

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

## Create a Release Bundle v2 from the Build {#create-a-release-bundle-v2-from-the-build}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) creates an immutable Release Bundle v2 from the build containing the Docker image. Having a Release Bundle prevents any changes to the Docker image as it progresses through the various stages of your SDLC towards eventual distribution to your end users.

```yaml
- name: Create release bundle  
  run: |  
    echo '{ "files": [ {"build": "'"${{ vars.BUILD_NAME }}/${{ github.run_number }}"'" } ] }' > bundle-spec.json  
    jf release-bundle-create ${{ vars.BUNDLE_NAME }} ${{ github.run_number }} --signing-key PGP-RSA-2048 --spec bundle-spec.json --sync=true  
    NAME_LINK=${{ vars.ARTIFACTORY_URL }}'/ui/artifactory/lifecycle/?bundleName='${{ vars.BUNDLE_NAME }}'&bundleToFlash='${{ vars.BUNDLE_NAME }}'&repositoryKey=example-project-release-bundles-v2&activeKanbanTab=promotion'  
    VER_LINK=${{ vars.ARTIFACTORY_URL }}'/ui/artifactory/lifecycle/?bundleName='${{ vars.BUNDLE_NAME }}'&bundleToFlash='${{ vars.BUNDLE_NAME }}'&releaseBundleVersion='${{ github.run_number }}'&repositoryKey=example-project-release-bundles-v2&activeVersionTab=Version%20Timeline&activeKanbanTab=promotion'  
    echo ' Release bundle ['${{ vars.BUNDLE_NAME }}']('${NAME_LINK}'):['${{ github.run_number }}']('${VER_LINK}') created' >> $GITHUB_STEP_SUMMARY
```

***

**Note**

For more information about using the JFrog CLI to create a Release Bundle, see [https://docs.jfrog-applications.jfrog.io/jfrog-applications/jfrog-cli/cli-for-jfrog-artifactory/release-lifecycle-management](https://docs.jfrog-applications.jfrog.io/jfrog-applications/jfrog-cli/cli-for-jfrog-artifactory/release-lifecycle-management).
***

## Attach Release Bundle Evidence {#attach-release-bundle-evidence}

This section of [build.yaml](https://github.com/jfrog/Evidence-Examples/tree/main/.github/workflows) creates signed evidence about the Release Bundle. 

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

## Create an External Policy to Potentially Block Release Bundle Promotion {#create-external-policy-to-block-rb-promotion}

When the Evidence service is used in conjunction with JFrog Xray, each Release Bundle promotion generates evidence in the form of a CycloneDX SBOM. You can create a policy in an external tool (for example, a rego policy) that reviews the contents of the CycloneDX evidence file and decides whether to block the promotion because the Release Bundle fails to meet all your organization's requirements for promotion to the next stage of your SDLC.

To see a sample rego policy, go [here](https://github.com/jfrog/Evidence-Examples/blob/main/policy/policy.rego).
For more information about integrating Release Lifecycle Management and Evidence with Xray, see [Scan Release Bundles (v2) with Xray](https://jfrog.com/help/r/jfrog-artifactory-documentation/scan-release-bundles-v2-with-xray).

