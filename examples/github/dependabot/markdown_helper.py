import json
import sys

def generate_dependabot_markdown_report(json_file_path, artifact_name, scan_date, image_id, image_size):
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Error: The file '{json_file_path}' was not found. Please ensure it exists."
    except json.JSONDecodeError:
        return f"Error: Could not decode JSON from '{json_file_path}'. Please verify the file's content."

    markdown_output = f"# Dependabot Vulnerability Report\n\n"

    markdown_output += f"""
**Artifact Name:** `{artifact_name}`

**Scan Date:** `{scan_date}`

**Image ID:** `{image_id}`

**Image Size:** `{image_size}`


"""

    alerts_data = data.get("data", [])
    alerts_found = bool(alerts_data)

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}

    for alert in alerts_data:
        severity = alert.get("severity", "unknown").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
        else:
            severity_counts["unknown"] += 1

    markdown_output += "---\n\n"
    markdown_output += "## Overview of Vulnerabilities\n\n"
    markdown_output += "| Severity | Count |\n"
    markdown_output += "| ------ | ------ |\n"
    markdown_output += f"| CRITICAL | {severity_counts['critical']} |\n"
    markdown_output += f"| HIGH     | {severity_counts['high']} |\n"
    markdown_output += f"| MEDIUM   | {severity_counts['medium']} |\n"
    markdown_output += f"| LOW      | {severity_counts['low']} |\n"
    markdown_output += f"| UNKNOWN  | {severity_counts['unknown']} |\n\n"

    markdown_output += "---\n\n"

    markdown_output += "## Detected Vulnerabilities by Package\n\n"

    if not alerts_found:
        markdown_output += "No Dependabot alerts were found in the provided JSON.\n"
    else:
        for alert in alerts_data:
            package_name = alert.get("packageName", "N/A")
            summary = alert.get("summary", "No summary provided.")
            ecosystem = alert.get("ecosystem", "N/A")
            cve_id = alert.get("cveId", "N/A")
            ghsa_id = alert.get("ghsaId", "N/A")
            severity = alert.get("severity", "N/A").capitalize()
            vulnerable_range = alert.get("vulnerableVersionRange", "N/A")
            patched_version = alert.get("patchedVersion", "N/A")
            advisory_url = alert.get("advisoryUrl", "N/A")
            detected_at = alert.get("detectedAt", "N/A")

            markdown_output += f"### Vulnerability: **{summary}**\n"
            markdown_output += f"- **Package**: `{package_name}` (Ecosystem: `{ecosystem}`)\n"
            markdown_output += f"- **Severity**: **{severity}**\n"

            if cve_id and cve_id != "N/A":
                markdown_output += f"- **CVE ID**: `{cve_id}`\n"
            if ghsa_id and ghsa_id != "N/A":
                markdown_output += f"- **GHSA ID**: `{ghsa_id}`\n"

            markdown_output += f"- **Vulnerable Version Range**: `{vulnerable_range}`\n"
            markdown_output += f"- **First Patched Version**: `{patched_version}`\n"
            markdown_output += f"- **Detected At**: `{detected_at}`\n"

            if advisory_url and advisory_url != "N/A":
                markdown_output += f"- **Advisory URL**: <{advisory_url}>\n"
            markdown_output += "\n---\n\n"

    return markdown_output

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python markdown_helper.py <path_to_dependabot.json> <output_report.md> <artifact_name> <scan_date> <image_id> <image_size>")
        sys.exit(1)

    json_file_path = sys.argv[1]
    output_markdown_path = sys.argv[2]
    artifact_name = sys.argv[3]
    scan_date = sys.argv[4]
    image_id = sys.argv[5]
    image_size = sys.argv[6]
    
    markdown_report = generate_dependabot_markdown_report(
        json_file_path, 
        artifact_name, 
        scan_date,  
        image_id, 
        image_size
    )
    
    try:
        with open(output_markdown_path, 'w') as outfile:
            outfile.write(markdown_report)
        print(f"Dependabot vulnerability report successfully generated and saved to '{output_markdown_path}'")
    except IOError as e:
        print(f"Error: Could not write the report to '{output_markdown_path}'. Reason: {e}")
        sys.exit(1)