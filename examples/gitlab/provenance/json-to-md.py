import json

def format_digests(digests):
    if not isinstance(digests, dict):
        return ""
    sha1 = digests.get("sha1")
    sha256 = digests.get("sha256")
    if sha1 and sha256:
        return f"sha1: {sha1}, sha256: {sha256}"
    elif sha1:
        return f"sha1: {sha1}"
    elif sha256:
        return f"sha256: {sha256}"
    return ""

def main():
    with open('./predicate.json', 'r') as f:
        pred = json.load(f)

    lines = []
    lines.append("# SLSA Provenance Predicate")
    lines.append("")
    lines.append("## Predicate\n")
    
    # Build Definition
    build_def = pred.get("buildDefinition", {})
    lines.append("### Build Definition")
    lines.append(f"- **Build Type**: `{build_def.get('buildType', '')}`\n")

    # External Parameters
    ext_params = build_def.get("externalParameters", {})
    lines.append("#### External Parameters")
    lines.append(f"- **Entry Point**: `{ext_params.get('entryPoint', '')}`")
    lines.append(f"- **Source**: `{ext_params.get('source', '')}`")
    lines.append("")

    # Internal Parameters
    int_params = build_def.get("internalParameters", {})
    lines.append("#### Internal Parameters")
    for k, v in int_params.items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")

    # Resolved Dependencies
    lines.append("#### Resolved Dependencies")
    for dep in build_def.get("resolvedDependencies", []):
        lines.append(f"- **URI**: `{dep.get('uri', '')}`")
        digest = format_digests(dep.get("digest", {}))
        if digest:
            lines.append(f"- **Digest**: `{digest}`")
    lines.append("")

    # Run Details
    run_details = pred.get("runDetails", {})
    lines.append("### Run Details")
    
    # Builder
    builder = run_details.get("builder", {})
    lines.append(f"- **Builder ID**: `{builder.get('id', '')}`")
    version = builder.get("version", {})
    for k, v in version.items():
        lines.append(f"- **{k}**: `{v}`")
    lines.append("")

    # Metadata
    metadata = run_details.get("metadata", {})
    lines.append("#### Metadata")
    lines.append(f"- **Invocation ID**: `{metadata.get('invocationID', '')}`")
    lines.append(f"- **Started On**: `{metadata.get('startedOn', '')}`")
    lines.append(f"- **Finished On**: `{metadata.get('finishedOn', '')}`")
    lines.append("")

    with open('GitLabSLSA.md', 'w') as f:
        f.write('\n'.join(lines))

if __name__ == "__main__":
    main()
