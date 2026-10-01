import json
import sys

from sanitize_trufflehog import sanitize_record, source_location


def generate_markdown_report(report):
    """Build a Markdown finding that contains no raw secret material."""
    sanitized = sanitize_record(report)
    detector_name = sanitized.get("DetectorName")
    if not detector_name:
        return None

    source_name = sanitized.get("SourceName", "N/A")
    detector_description = sanitized.get("DetectorDescription", "N/A")
    verified = sanitized.get("Verified", False)
    redacted = sanitized.get("Redacted", "N/A")
    location = source_location(sanitized)

    return f"""
## Report Overview: {source_name}

**Source Name:** `{source_name}`

**Detector Name:** `{detector_name}`

**Detector Description:** `{detector_description}`

**Source Location:** `{location}`

**Verified:** `{verified}`

**Redacted Data:** `{redacted}`

---
"""


def main(input_file):
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    markdown_reports = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        report = json.loads(stripped)
        markdown_report = generate_markdown_report(report)
        if markdown_report:
            markdown_reports.append(markdown_report)

    output_file = "report_readme.md"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n\n".join(markdown_reports))

    print(f"Markdown README generated successfully and saved to {output_file}!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_trufflehog_results.py <report_file>")
        sys.exit(1)

    main(sys.argv[1])
