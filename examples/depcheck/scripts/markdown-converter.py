#!/usr/bin/env python3
"""
Dependency Check Markdown Converter
Inspired by JFrog Evidence Examples

This script converts OWASP Dependency Check JSON reports to readable markdown format
for better integration with documentation and reporting systems.
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class DependencyCheckMarkdownConverter:
    """Converts Dependency Check JSON reports to markdown format."""
    
    def __init__(self, json_file_path: str):
        """Initialize the converter with a JSON report file."""
        self.json_file_path = json_file_path
        self.report_data = self._load_json_report()
    
    def _load_json_report(self) -> Dict[str, Any]:
        """Load and parse the JSON report file."""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: Report file '{self.json_file_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in report file: {e}")
            sys.exit(1)
    
    def _format_cvss_score(self, score: Optional[float]) -> str:
        """Format CVSS score with color coding."""
        if score is None:
            return "N/A"
        
        if score >= 9.0:
            return f"**{score:.1f} (Critical)**"
        elif score >= 7.0:
            return f"**{score:.1f} (High)**"
        elif score >= 4.0:
            return f"**{score:.1f} (Medium)**"
        elif score >= 0.1:
            return f"**{score:.1f} (Low)**"
        else:
            return f"**{score:.1f} (None)**"
    
    def _format_cve_references(self, references: List[Dict[str, str]]) -> str:
        """Format CVE references as markdown links."""
        if not references:
            return "No references available"
        
        formatted_refs = []
        for ref in references:
            name = ref.get('name', 'Unknown')
            url = ref.get('url', '')
            if url:
                formatted_refs.append(f"[{name}]({url})")
            else:
                formatted_refs.append(name)
        
        return ", ".join(formatted_refs)
    
    def _format_vulnerability_table(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """Create a markdown table for vulnerabilities."""
        if not vulnerabilities:
            return "No vulnerabilities found."
        
        table = "| CVE ID | Severity | CVSS Score | Description | References |\n"
        table += "|--------|----------|------------|-------------|------------|\n"
        
        for vuln in vulnerabilities:
            cve_id = vuln.get('name', 'N/A')
            severity = vuln.get('severity', 'Unknown')
            cvss_score = self._format_cvss_score(vuln.get('cvssv3', {}).get('baseScore'))
            description = vuln.get('description', 'No description available')
            # Truncate description if too long
            if len(description) > 100:
                description = description[:97] + "..."
            
            references = self._format_cve_references(vuln.get('references', []))
            if len(references) > 50:
                references = references[:47] + "..."
            
            table += f"| {cve_id} | {severity} | {cvss_score} | {description} | {references} |\n"
        
        return table
    
    def _format_dependency_details(self, dependencies: List[Dict[str, Any]]) -> str:
        """Format dependency details with vulnerabilities."""
        if not dependencies:
            return "No dependencies analyzed."
        
        markdown = ""
        
        for dep in dependencies:
            file_path = dep.get('filePath', 'Unknown')
            file_name = dep.get('fileName', 'Unknown')
            is_virtual = dep.get('isVirtual', False)
            
            markdown += f"### {file_name}\n\n"
            markdown += f"- **File Path:** `{file_path}`\n"
            markdown += f"- **Is Virtual:** {is_virtual}\n"
            
            # Add SHA information
            md5 = dep.get('md5', 'N/A')
            sha1 = dep.get('sha1', 'N/A')
            sha256 = dep.get('sha256', 'N/A')
            
            markdown += f"- **MD5:** `{md5}`\n"
            markdown += f"- **SHA1:** `{sha1}`\n"
            markdown += f"- **SHA256:** `{sha256}`\n"
            
            # Add all packages
            packages = dep.get('packages', [])
            if packages:
                markdown += "\n#### Packages\n\n"
                for i, pkg in enumerate(packages, 1):
                    pkg_id = pkg.get('id', 'Unknown')
                    confidence = pkg.get('confidence', 'N/A')
                    markdown += f"**Package {i}:**\n"
                    markdown += f"- **ID:** `{pkg_id}`\n"
                    markdown += f"- **Confidence:** {confidence}\n"
                    markdown += "\n"
            
            # Add evidence collected
            evidence = dep.get('evidenceCollected', {})
            if evidence:
                markdown += "#### Evidence Collected\n\n"
                
                # Product evidence
                product_evidence = evidence.get('productEvidence', [])
                if product_evidence:
                    markdown += "**Product Evidence:**\n"
                    for ev in product_evidence:
                        name = ev.get('name', 'N/A')
                        value = ev.get('value', 'N/A')
                        confidence = ev.get('confidence', 'N/A')
                        source = ev.get('source', 'N/A')
                        markdown += f"- **{name}:** {value} (Confidence: {confidence}, Source: {source})\n"
                    markdown += "\n"
                
                # Vendor evidence
                vendor_evidence = evidence.get('vendorEvidence', [])
                if vendor_evidence:
                    markdown += "**Vendor Evidence:**\n"
                    for ev in vendor_evidence:
                        name = ev.get('name', 'N/A')
                        value = ev.get('value', 'N/A')
                        confidence = ev.get('confidence', 'N/A')
                        source = ev.get('source', 'N/A')
                        markdown += f"- **{name}:** {value} (Confidence: {confidence}, Source: {source})\n"
                    markdown += "\n"
                
                # Version evidence
                version_evidence = evidence.get('versionEvidence', [])
                if version_evidence:
                    markdown += "**Version Evidence:**\n"
                    for ev in version_evidence:
                        name = ev.get('name', 'N/A')
                        value = ev.get('value', 'N/A')
                        confidence = ev.get('confidence', 'N/A')
                        source = ev.get('source', 'N/A')
                        markdown += f"- **{name}:** {value} (Confidence: {confidence}, Source: {source})\n"
                    markdown += "\n"
            
            vulnerabilities = dep.get('vulnerabilities', [])
            if vulnerabilities:
                markdown += f"#### Vulnerabilities Found: {len(vulnerabilities)}\n\n"
                markdown += self._format_vulnerability_table(vulnerabilities)
            else:
                markdown += "#### Vulnerabilities Found: 0\n\n"
            
            markdown += "\n---\n\n"
        
        return markdown
    
    def generate_summary(self) -> str:
        """Generate a summary section of the report."""
        summary = self.report_data.get('summary', {})
        
        total_deps = summary.get('totalDependencies', 0)
        vulnerable_deps = summary.get('vulnerableDependencies', 0)
        total_vulns = summary.get('totalVulnerabilities', 0)
        
        markdown = "## Security Summary\n\n"
        markdown += f"- **Total Dependencies Analyzed:** {total_deps}\n"
        markdown += f"- **Vulnerable Dependencies:** {vulnerable_deps}\n"
        markdown += f"- **Total Vulnerabilities Found:** {total_vulns}\n"
        
        if total_deps > 0:
            vuln_percentage = (vulnerable_deps / total_deps) * 100
            markdown += f"- **Vulnerability Rate:** {vuln_percentage:.1f}%\n"
        
        # Add severity breakdown
        severity_counts = summary.get('severityCounts', {})
        if severity_counts:
            markdown += "\n### Severity Breakdown\n\n"
            for severity, count in severity_counts.items():
                if count > 0:
                    markdown += f"- **{severity.title()}:** {count}\n"
        
        return markdown
    
    def generate_report(self) -> str:
        """Generate the complete markdown report."""
        scan_info = self.report_data.get('scanInfo', {})
        
        markdown = "# OWASP Dependency Check Security Report\n\n"
        markdown += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        
        # Add report schema version
        report_schema = self.report_data.get('reportSchema', 'N/A')
        markdown += f"**Report Schema Version:** {report_schema}\n\n"
        
        # Report metadata
        project_info = self.report_data.get('projectInfo', {})
        if project_info:
            markdown += "## Report Information\n\n"
            markdown += f"- **Project Name:** {project_info.get('name', 'N/A')}\n"
            markdown += f"- **Report Date:** {project_info.get('reportDate', 'N/A')}\n"
            
            # Add credits if available
            credits = project_info.get('credits', {})
            if credits:
                markdown += "\n### Data Sources and Credits\n\n"
                for source, description in credits.items():
                    markdown += f"- **{source}:** {description}\n"
            
            markdown += "\n"
        
        # Scan information
        if scan_info:
            markdown += "## Scan Information\n\n"
            markdown += f"- **Scan Engine Version:** {scan_info.get('engineVersion', 'N/A')}\n"
            
            # Data Source table
            data_sources = scan_info.get('dataSource', [])
            if data_sources:
                markdown += "\n### Data Sources\n\n"
                markdown += "| Data Source | Last Checked | Last Modified |\n"
                markdown += "|-------------|--------------|---------------|\n"
                
                for source in data_sources:
                    name = source.get('name', 'N/A')
                    timestamp = source.get('timestamp', 'N/A')
                    # Format timestamp for better readability
                    if timestamp != 'N/A':
                        try:
                            # Parse ISO timestamp and format it
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                        except:
                            formatted_timestamp = timestamp
                    else:
                        formatted_timestamp = 'N/A'
                    
                    markdown += f"| {name} | {formatted_timestamp} | {formatted_timestamp} |\n"
                markdown += "\n"
            
            # Only add scan duration if it's not N/A
            scan_duration = scan_info.get('scanDuration', 'N/A')
            if scan_duration != 'N/A':
                markdown += f"- **Scan Duration:** {scan_duration}\n"
            markdown += "\n"
        
        # Summary
        markdown += self.generate_summary()
        
        # Dependencies and vulnerabilities
        dependencies = self.report_data.get('dependencies', [])
        if dependencies:
            markdown += "\n## Dependencies Analysis\n\n"
            markdown += self._format_dependency_details(dependencies)
        
        # Footer
        markdown += "\n---\n\n"
        
        return markdown
    
    def save_markdown(self, output_file: str = None) -> str:
        """Save the markdown report to a file."""
        if output_file is None:
            base_name = os.path.splitext(self.json_file_path)[0]
            # Remove any existing "-report" suffix to avoid duplication
            if base_name.endswith('-report'):
                base_name = base_name[:-7]  # Remove "-report"
            output_file = f"{base_name}-report.md"
        
        markdown_content = self.generate_report()
        
        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            print(f"Markdown report saved to: {output_file}")
            return output_file
        except PermissionError as e:
            print(f"Permission denied: {e}")
            print(f"Trying to save to current directory instead...")
            # Try saving to current directory as fallback
            fallback_file = os.path.basename(output_file)
            try:
                with open(fallback_file, 'w', encoding='utf-8') as file:
                    file.write(markdown_content)
                print(f"Markdown report saved to: {fallback_file}")
                return fallback_file
            except Exception as fallback_e:
                print(f"Error saving to fallback location: {fallback_e}")
                return None
        except Exception as e:
            print(f"Error saving markdown file: {e}")
            return None


def main():
    """Main function to run the converter."""
    if len(sys.argv) < 2:
        print("Usage: python markdown-converter.py <json-report-file> [output-markdown-file]")
        print("Example: python markdown-converter.py dependency-check-report.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        converter = DependencyCheckMarkdownConverter(json_file)
        output_path = converter.save_markdown(output_file)
        
        if output_path:
            print(f"\nConversion completed successfully!")
            print(f"Input: {json_file}")
            print(f"Output: {output_path}")
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 