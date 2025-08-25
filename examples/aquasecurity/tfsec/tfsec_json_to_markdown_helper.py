import json
import os
import sys

def generate_readme(json_file_path, output_file_path):
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)

        # Extract results
        results = data.get("results", [])
        # Generate markdown content
        markdown_content = f"""
# Detected Vulnerabilities by tfsec

"""
        for result in results:
            markdown_content += f"## Issue: {result.get('description', 'No description')}\n\n"
            markdown_content += f"### Impact\n{result.get('impact', 'No impact information')}\n\n"
            markdown_content += "### Links\n"
            for link in result.get('links', []):
                markdown_content += f"- [{link}]({link})\n"
            markdown_content += "\n"
            markdown_content += "### Location\n"
            location = result.get('location', {})
            markdown_content += f"- **File:** {location.get('filename', 'Unknown file')}\n"
            markdown_content += f"- **Start Line:** {location.get('start_line', 'Unknown start line')}\n"
            markdown_content += f"- **End Line:** {location.get('end_line', 'Unknown end line')}\n\n"
            markdown_content += "### Details\n"
            markdown_content += f"- **Long ID:** `{result.get('long_id', 'Unknown long ID')}`\n"
            markdown_content += f"- **Resolution:** {result.get('resolution', 'No resolution provided')}\n"
            markdown_content += f"- **Resource:** `{result.get('resource', 'Unknown resource')}`\n"
            markdown_content += f"- **Rule Description:** {result.get('rule_description', 'No rule description')}\n"
            markdown_content += f"- **Rule ID:** `{result.get('rule_id', 'Unknown rule ID')}`\n"
            markdown_content += f"- **Rule Provider:** `{result.get('rule_provider', 'Unknown rule provider')}`\n"
            markdown_content += f"- **Rule Service:** `{result.get('rule_service', 'Unknown rule service')}`\n"
            markdown_content += f"- **Severity:** `{result.get('severity', 'Unknown severity')}`\n"
            markdown_content += f"- **Status:** `{result.get('status', 'Unknown status')}`\n"
            markdown_content += f"- **Warning:** `{result.get('warning', 'Unknown warning')}`\n\n"

        # Write to the README file
        with open(output_file_path, 'w') as output_file:
            output_file.write(markdown_content)

        print(f"README file generated successfully at {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tfsec_json_to_markdown_helper.py <input_file>")
        sys.exit(1)
    # Define paths
    json_file_path = sys.argv[1]
    output_file_path = "tfsec.md"  # Adjust path as needed

    # Generate README
    generate_readme(json_file_path, output_file_path)
