#!/usr/bin/env python3

"""
CodeQL SARIF to Markdown Converter

This script converts CodeQL SARIF output files to readable Markdown format.
It includes severity ratings, CVSS scores, and detailed analysis information.
"""

import json
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import platform
import os

class SeverityFormatter:
    """Handles severity-related formatting and conversions."""

    EMOJI_MAP = {
        'error': '🔴',
        'warning': '🟡',
        'note': '🔵',
        'none': '⚪'
    }

    CVSS_RANGES = [
        (9.0, 'Critical'),
        (7.0, 'High'),
        (4.0, 'Medium'),
        (0.0, 'Low')
    ]

    @classmethod
    def get_emoji(cls, level: str) -> str:
        return cls.EMOJI_MAP.get(level.lower(), cls.EMOJI_MAP['none'])

    @classmethod
    def get_cvss_rating(cls, security_severity: Any) -> str:
        if not security_severity:
            return "N/A"
        try:
            score = float(security_severity)
            for threshold, rating in cls.CVSS_RANGES:
                if score >= threshold:
                    return f"{rating} ({score})"
            return f"Low ({score})"
        except (ValueError, TypeError):
            return str(security_severity)

class MarkdownBuilder:
    def __init__(self, sarif_data: Dict):
        self.data = sarif_data
        self.formatter = SeverityFormatter()
        self.sections: List[str] = []

    def add_header(self) -> None:
        codeql_version = "unknown"
        if self.data.get('runs'):
            tool_info = self.data['runs'][0].get('tool', {}).get('driver', {})
            codeql_version = tool_info.get('version', 'unknown')

        self.sections.extend([
            "# 🔍 CodeQL Security Analysis Report",
            "\n## Scan Details",
            f"**Scan Type**: CodeQL Static Analysis\n",
            f"**Scan Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
            f"**Operating System**: {platform.system()} {platform.release()}\n",
            f"**Analysis Tool**: CodeQL",
            "\n---\n"
        ])

    def add_tool_info(self) -> None:
        if not self.data.get('runs'):
            return
        tool = self.data['runs'][0].get('tool', {}).get('driver', {})
        self.sections.extend([
            "\n## 🛠️ Analysis Details",
            f"- **Tool**: {tool.get('name', 'CodeQL')}",
            f"- **Version**: {tool.get('semanticVersion', tool.get('version', 'N/A'))}",
        ])

        # Map artifact index to language
        artifact_lang = {}
        for notification in tool.get('notifications', []):
            lang = notification.get('properties', {}).get('languageDisplayName')
            locations = notification.get('locations', [])
            for loc in locations:
                idx = loc.get('physicalLocation', {}).get('artifactLocation', {}).get('index')
                if lang and idx is not None:
                    artifact_lang[idx] = lang



    def add_summary(self) -> None:
        severity_count = {
            'error': 0,
            'warning': 0,
            'note': 0,
            'none': 0
        }
        total_issues = 0

        for run in self.data.get('runs', []):
            # Collect rules from driver and all extensions
            rules = {rule['id']: rule for rule in run.get('tool', {}).get('driver', {}).get('rules', [])}
            for ext in run.get('tool', {}).get('extensions', []):
                for rule in ext.get('rules', []):
                    rules[rule['id']] = rule

            for result in run.get('results', []):
                rule_id = result.get('ruleId', 'unknown')
                rule = rules.get(rule_id, {})
                rule_severity = rule.get('properties', {}).get('problem.severity', 'none')
                level = result.get('level', rule_severity).lower()
                if level not in severity_count:
                    severity_count[level] = 0
                severity_count[level] += 1
                total_issues += 1

        self.sections.extend([
            "\n## 📊 Analysis Summary",
            f"\n**Total Issues Found**: {total_issues}",
            "\n### Severity Breakdown"
        ])

        for severity in ['error', 'warning', 'note', 'none']:
            count = severity_count.get(severity, 0)
            emoji = self.formatter.get_emoji(severity)
            self.sections.append(f"- {emoji} **{severity.title()}**: {count}")


    def add_query_info(self) -> None:
        self.sections.append("\n## 📝 Query Information")

        unique_queries = set()
        for run in self.data.get('runs', []):
            for rule in run.get('tool', {}).get('driver', {}).get('rules', []):
                if rule['id'] not in unique_queries:
                    unique_queries.add(rule['id'])
                    properties = rule.get('properties', {})

                    self.sections.extend([
                        f"\n### {rule.get('name', rule['id'])}",
                        f"- **ID**: `{rule['id']}`"
                    ])

                    if 'security-severity' in properties:
                        cvss = self.formatter.get_cvss_rating(properties['security-severity'])
                        self.sections.append(f"- **CVSS Score**: {cvss}")

                    severity = properties.get('problem.severity', 'none')
                    emoji = self.formatter.get_emoji(severity)
                    self.sections.append(f"- **Severity**: {emoji} {severity.title()}")

                    if 'tags' in properties:
                        tags = ', '.join(f'`{tag}`' for tag in properties['tags'])
                        self.sections.append(f"- **Tags**: {tags}")

                    description = rule.get('description', {}).get('text', 'No description available')
                    self.sections.extend(['', description, ''])

    def add_findings(self) -> None:
        self.sections.extend([
            "\n## 🔍 Detailed Findings",
            "\n| Severity | Query | Location | Description |",
            "|----------|--------|-----------|-------------|"
        ])

        for run in self.data.get('runs', []):
            # Collect rules from driver and all extensions
            rules = {rule['id']: rule for rule in run.get('tool', {}).get('driver', {}).get('rules', [])}
            for ext in run.get('tool', {}).get('extensions', []):
                for rule in ext.get('rules', []):
                    rules[rule['id']] = rule

            for result in run.get('results', []):
                rule_id = result.get('ruleId', 'unknown')
                rule = rules.get(rule_id, {})
                rule_name = rule.get('name', rule_id)

                # Fallback to rule severity if result.level is missing
                rule_severity = rule.get('properties', {}).get('problem.severity', 'none')
                severity = result.get('level', rule_severity)

                emoji = self.formatter.get_emoji(severity)
                location = self._format_location(result.get('locations', []))
                message = result.get('message', {}).get('text', 'No description available')

                self.sections.append(
                    f"| {emoji} {severity.title()} | {rule_name} | {location} | {message} |"
                )
    def _format_location(self, locations: List[Dict]) -> str:
        if not locations:
            return "N/A"
        loc = locations[0].get('physicalLocation', {})
        file_path = loc.get('artifactLocation', {}).get('uri', 'unknown')
        region = loc.get('region', {})
        start_line = region.get('startLine', '?')
        end_line = region.get('endLine', start_line)
        location = f"`{file_path}:{start_line}`"
        if start_line != end_line:
            location += f"-`{end_line}`"
        return location


    def build(self) -> str:
        self.add_header()
        self.add_tool_info()
        self.add_summary()
        self.add_query_info()
        self.add_findings()
        return '\n'.join(self.sections)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) != 3:
        logger.error("Incorrect number of arguments")
        print("Usage: python sarif_to_markdown.py <input_sarif_file> <output_markdown_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        logger.info(f"Reading SARIF file: {input_file}")
        with open(input_file, 'r') as f:
            sarif_data = json.load(f)

        logger.info("Converting SARIF to Markdown")
        builder = MarkdownBuilder(sarif_data)
        markdown_content = builder.build()

        logger.info(f"Writing Markdown file: {output_file}")
        with open(output_file, 'w') as f:
            f.write(markdown_content)

        logger.info("Conversion completed successfully")

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid SARIF JSON in file: {input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
