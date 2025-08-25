import json
import sys


def count_severity(vulnerabilities):
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}
    for vuln in vulnerabilities:
        severity = vuln['Severity'].upper()
        if severity in severity_counts:
            severity_counts[severity] += 1
        else:
            severity_counts['UNKNOWN'] += 1
    return severity_counts


def generate_markdown_report(trivy_output):
    artifact = trivy_output['ArtifactName']
    artifact_type = trivy_output['ArtifactType']
    created_at = trivy_output['CreatedAt']
    image_id = trivy_output.get('Metadata', {}).get('ImageID', 'N/A')
    image_size = trivy_output.get('Metadata', {}).get('Size', 'N/A')

    if 'Results' in trivy_output and len(trivy_output['Results']) > 0:
        os_info = trivy_output['Results'][0].get('Target', 'N/A').split()
        os_name = os_info[-2]  # Expected format "OS version"
        os_version = os_info[-1]
    else:
        os_name = 'N/A'
        os_version = 'N/A'

    all_vulnerabilities = []
    for result in trivy_output['Results']:
        all_vulnerabilities.extend(result.get('Vulnerabilities', []))

    severity_counts = count_severity(all_vulnerabilities)

    markdown_report = f"""
## Trivy Scan Report: {artifact}

**Artifact Name:** `{artifact}`

**Artifact Type:** `{artifact_type}`

**Scan Date:** `{created_at}`

**Operating System:** `{os_name} {os_version}`

**Image ID:** `{image_id}`

**Image Size:** `{image_size}`

---
### Overview of Vulnerabilities
| Severity   | Count |
| :--------- | :---- |
| CRITICAL   | {severity_counts.get('CRITICAL', 0)} |
| HIGH       | {severity_counts.get('HIGH', 0)} |
| MEDIUM     | {severity_counts.get('MEDIUM', 0)} |
| LOW        | {severity_counts.get('LOW', 0)} |
| UNKNOWN    | {severity_counts.get('UNKNOWN', 0)} |
---
### Detected Vulnerabilities by Package
This section lists all detected vulnerabilities, categorized by the type of package (OS or language-specific) and then by individual packages.
"""

    for result in trivy_output['Results']:
        # Skip if Results key does not have a "Vulnerabilities" key or if Vulnerabilities is empty
        if 'Vulnerabilities' not in result or not result['Vulnerabilities']:
            continue
            
        package_class = result['Class']
        target = result['Target']

        if package_class == 'os-pkgs':
            markdown_report += f"""
#### OS Packages (`os-pkgs`)
**Target:** `{target}`
| Vulnerability ID | Package    | Installed Version | Severity | Description                                   | Status      |
| :--------------- | :--------- | :---------------- | :------- | :-------------------------------------------- | :---------- |
"""
            for vuln in result['Vulnerabilities']:
                markdown_report += f"| {vuln['VulnerabilityID']} | {vuln['PkgName']} | {vuln['InstalledVersion']} | {vuln['Severity']} | {vuln['Description']} | {vuln['Status']} |\n"

        elif package_class == 'lang-pkgs':
            markdown_report += f"""
#### Language-specific Packages (`lang-pkgs`)
**Target:** `{target}`
| Vulnerability ID | Package    | Installed Version | Fixed Version | Severity | Description                                   | Status      |
| :--------------- | :--------- | :---------------- | :------------ | :------- | :-------------------------------------------- | :---------- |
"""
            for vuln in result['Vulnerabilities']:
                fixed_version = vuln.get('FixedVersion', 'N/A')
                markdown_report += f"| {vuln['VulnerabilityID']} | {vuln['PkgName']} | {vuln['InstalledVersion']} | {fixed_version} | {vuln['Severity']} | {vuln['Description']} | {vuln['Status']} |\n"

    markdown_report += "\n---"
    return markdown_report


def main(input_file):
    # Read JSON input from a file
    with open(input_file, 'r') as file:
        trivy_output = json.load(file)

    # Generate the Markdown report
    markdown_report = generate_markdown_report(trivy_output)

    # Define the output file path
    output_file = 'trivy-results.md'

    # Write the Markdown report to a file
    with open(output_file, 'w') as file:
        file.write(markdown_report)

    print(f"Markdown report generated successfully and saved to {output_file}!")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python trivy_json_to_markdown_helper.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    main(input_file)
