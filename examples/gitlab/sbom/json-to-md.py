import json

def json_to_md(json_path, md_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    name = data.get('metadata', {}).get('component', {}).get('name', 'N/A')
    timestamp = data.get('metadata', {}).get('timestamp', 'N/A')
    tools = data.get('metadata', {}).get('tools', {}).get('components', [])
    components = data.get('components', [])
    dependencies = data.get('dependencies', [])

    with open(md_path, 'w') as f:
        f.write(f"# SBOM Summary\n\n")
        f.write(f"**Component Name:** {name}\n\n")
        f.write(f"**Timestamp:** {timestamp}\n\n")
        f.write(f"## Tools Used\n")
        if tools:
            for tool in tools:
                tool_name = tool.get('name', 'Unknown Tool')
                tool_version = tool.get('version', 'Unknown Version')
                f.write(f"- {tool_name} (version: {tool_version})\n")
        else:
            f.write("No tool information found.\n")
        f.write(f"\n## Components\n")
        if components:
            f.write("| bom-ref | name | version |\n")
            f.write("|---|---|---|\n")
            for comp in components:
                bom_ref = comp.get('bom-ref', 'N/A').replace('|', '\\|')
                comp_name = comp.get('name', 'N/A').replace('|', '\\|')
                comp_version = comp.get('version', 'N/A').replace('|', '\\|')
                f.write(f"| {bom_ref} | {comp_name} | {comp_version} |\n")
        else:
            f.write("No components found.\n")

        f.write(f"\n## Dependencies\n")
        if dependencies:
            f.write("| Reference | DependsOn |\n")
            f.write("|---|---|\n")
            for dep in dependencies:
                ref = dep.get('ref', 'N/A').replace('|', '\\|')
                dependson = dep.get('dependsOn', [])
                dependson_str = ', '.join(d.replace('|', '\\|') for d in dependson) if dependson else ''
                f.write(f"| {ref} | {dependson_str} |\n")
        else:
            f.write("No dependencies found.\n")
        print(f"Markdown file generated at: {md_path}")


if __name__ == "__main__":
    json_to_md('./gl-sbom-report.cdx.json', 'GitLab_SBOM.md')