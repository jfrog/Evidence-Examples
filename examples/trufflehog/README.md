# **Trufflehog Secret Scan Evidence Example**

This repository provides a working example of a GitHub Actions workflow that automatically scans a repository for exposed secrets using Trufflehog. It then attaches the resulting scan report as signed, verifiable evidence to a Docker image in JFrog Artifactory.

This workflow is an essential DevSecOps practice, helping to prevent accidental secret leakage by creating a traceable and auditable record of what was found in your codebase at a specific point in time.

### **Do not publish secret material as evidence**

Evidence created with `jf evd create` is stored on the package. Anyone who can read that package or repository can read the evidence, including other teams, service accounts, and anonymous readers when the repository allows it. That audience is wider than the people who can read the source repository. Signed evidence also cannot be quietly edited later, so a secret written into it stays there.

TruffleHog's JSON output includes the matched secret in `Raw` and `RawV2`, and sometimes again in `ExtraData`. This example strips those fields before anything is attached. The predicate and the optional Markdown report keep only non-secret metadata: detector name, source location, the `Redacted` value, and verification status.

### **Key Features**

* **Automated Secret Scanning**: Uses Trufflehog to scan the repository for potential secrets and sensitive information.
* **Comprehensive Detection**: Scans for various types of secrets including API keys, passwords, tokens, and other sensitive data.
* **Evidence Generation**: Creates a structured predicate file from Trufflehog scan results.
* **Optional Markdown Report**: Includes a helper script to generate a human-readable Markdown summary from the Trufflehog JSON results.
* **Signed Evidence Attachment**: Attaches the scan results to the corresponding package version in Artifactory using jf evd create, cryptographically signing it for integrity.
* **Trufflehog**: [what Trufflehog can detect](https://github.com/trufflesecurity/trufflehog)

### **Workflow**

The following diagram illustrates the sequence of operations performed by the GitHub Actions workflow.

```mermaid
graph TD
    A[Workflow Dispatch Trigger] --> B[Setup JFrog CLI]
    B --> C[Checkout Repository with Sparse Checkout]
    C --> D[Build and Publish Docker Image to Artifactory]
    D --> E[Run Trufflehog Secret Scan]
    E --> F{ATTACH_OPTIONAL_CUSTOM_MARKDOWN_TO_EVIDENCE?}
    F -->|true| G[Generate Custom Markdown Report]
    F -->|false| H[Skip Markdown Report Generation]
    G --> I[Attach Evidence to Package with jf evd create]
    H --> I[Attach Evidence to Package with jf evd create]
    I --> J[Evidence Signed and Stored in JFrog Platform]
```

---

### **1\. Prerequisites**

Before running this workflow, you must have:

* JFrog CLI 2.65.0 or above (installed automatically in the workflow)  
* An Artifactory repository configured for your project.
* A private key and a corresponding key alias configured in your JFrog Platform for signing evidence.  
* The following GitHub repository variables:  
  * `JF_URL` (JFrog Platform base URL, e.g. `https://mycompany.jfrog.io`)  
  * `JF_SIGNING_KEY_ALIAS` (Key alias for signing evidence)
* The following GitHub repository secrets:  
  * `JF_ACCESS_TOKEN` (JFrog access token with evidence upload permissions)  
  * `JF_PRIVATE_KEY` (Private key for signing evidence)

### Environment Variables Used

* `ATTACH_OPTIONAL_CUSTOM_MARKDOWN_TO_EVIDENCE` - Controls whether to generate and attach a Markdown report

### **2\. Configuration**

To use this workflow, you must configure the following GitHub Repository Secrets and Variables.

#### **GitHub Secrets**

Navigate to Settings \> Secrets and variables \> Actions and create the following secrets:

| Secret Name | Description |
| :---- | :---- | 
| JF_ACCESS_TOKEN | A valid JFrog Access Token with permissions to read, write, and annotate in your target repository. | 
| JF_PRIVATE_KEY | The private key used to sign the evidence. This key corresponds to the alias configured in JFrog Platform. |

#### **GitHub Variables**

Navigate to Settings \> Secrets and variables \> Actions and create the following variables:

| Variable Name | Description | Example Value |
| :---- | :---- | :---- |
| JF_URL | The base URL of your JFrog Platform instance. | https://mycompany.jfrog.io |
| JF_SIGNING_KEY_ALIAS | The alias for the public key in JFrog Platform used to verify the evidence signature. | my-signing-key-alias |

#### **Workflow Environment Variables**

You can also customize the workflow's behavior by modifying the env block in the .github/workflows/trufflehog-evidence-example.yml file:

| Variable Name | Description | Default Value |
| :---- | :---- | :---- |
| ATTACH_OPTIONAL_CUSTOM_MARKDOWN_TO_EVIDENCE | Set to true to generate and attach a Markdown report alongside the JSON evidence. Set to false to skip this step. | true |

---

### **3\. Usage**

This workflow is triggered manually.

1. Navigate to the **Actions** tab of your forked repository.  
2. In the left sidebar, click on the **Trufflehog Scan and JFrog Evidence** workflow.  
3. Click the **Run workflow** dropdown button. You can leave the default branch selected.  
4. Click the green **Run workflow** button.

Once the workflow completes successfully, you can navigate to your repository in Artifactory and view the evidence. Under the **Evidence** tab for the latest version, you will find the signed Trufflehog scan results.

### **How It Works: A Step-by-Step Breakdown**

1. **Setup and Checkout**: The workflow begins by setting up the JFrog CLI and checking out the repository code using sparse checkout to focus on the trufflehog example directory.
2. **Run Trufflehog Secret Scan**: Uses Docker to run Trufflehog against the repository, scanning for potential secrets and sensitive information. The scan outputs results in JSON format.
3. **Build the evidence predicate**: `jsonl_to_json_converted.py` turns the JSONL scan into `trufflehog.json` and drops secret fields (`Raw`, `RawV2`, `ExtraData`, and anything outside the allowlist) before the file is attached.
4. **Generate Optional Markdown Report**: If ATTACH_OPTIONAL_CUSTOM_MARKDOWN_TO_EVIDENCE is true, `process_trufflehog_results.py` writes a human-readable summary that includes the redacted value and location, and does not include the raw secret.
5. **Attach Signed Evidence**: The final step uses the jf evd create command to attach the scan results as evidence to the specific package version in Artifactory. The evidence is signed using the provided private key, ensuring its authenticity and integrity.

### **Key Commands Used**

* **Run Trufflehog Scan:**
  This step runs the `trufflesecurity/trufflehog` container to scan the entire checked-out repository. The results are output in a `.jsonl` (JSON Lines) format. The `|| true` ensures the workflow continues even if secrets are found, allowing the findings to be reported as evidence.

```bash
docker run --rm -v "$PWD:/pwd" trufflesecurity/trufflehog:latest filesystem /pwd --json > trufflehog-results.jsonl
```

* **Process Results:**
  The raw `.jsonl` output from Trufflehog is processed in two steps. Both scripts remove secret fields before writing files that `jf evd create` will publish.

1. `jsonl_to_json_converted.py` converts the JSON Lines file into `trufflehog.json`, the evidence predicate. Each finding keeps only the allowlisted non-secret fields.
2. If `ATTACH_OPTIONAL_CUSTOM_MARKDOWN_TO_EVIDENCE` is `true`, `process_trufflehog_results.py` generates a human-readable Markdown summary without `Raw` or `RawV2`.

```bash
python jsonl_to_json_converted.py trufflehog-results.jsonl trufflehog.json
python process_trufflehog_results.py trufflehog-results.jsonl
```

* **Attach Evidence:**
  This final step uses jf evd create to attach the processed trufflehog.json report to the Docker image. This creates a permanent, tamper-proof record of the secret scan for the associated build.

```bash
jf evd create \
  --package-name your-package-name \
  --package-version your-version \
  --package-repo-name your-repo-name \
  --key "${{ secrets.JF_PRIVATE_KEY }}" \
  --key-alias ${{ vars.JF_SIGNING_KEY_ALIAS }} \
  --predicate ./trufflehog.json \
  --predicate-type https://trufflesecurity.com/TruffleHog \
  --markdown report_readme.md
```

### **References**

* [Trufflehog Documentation](https://github.com/trufflesecurity/trufflehog)  
* [JFrog Evidence Management](https://jfrog.com/help/r/jfrog-artifactory-documentation/evidence-management)  
* [JFrog CLI Documentation](https://jfrog.com/getcli/)
