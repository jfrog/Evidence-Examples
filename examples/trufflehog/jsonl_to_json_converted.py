import json
import sys

from sanitize_trufflehog import sanitize_record

DEFAULT_INPUT_FILE = "trufflehog-results.jsonl"
DEFAULT_OUTPUT_FILE = "trufflehog.json"


def convert(input_file, output_file):
    """Write an evidence predicate that keeps only non-secret finding fields."""
    records = []
    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue
            records.append(sanitize_record(json.loads(stripped)))

    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump({"data": records}, outfile, indent=2)
        outfile.write("\n")

    print(f"Converted {input_file} to {output_file}")
    return records


def main(argv):
    input_file = argv[1] if len(argv) > 1 else DEFAULT_INPUT_FILE
    output_file = argv[2] if len(argv) > 2 else DEFAULT_OUTPUT_FILE
    convert(input_file, output_file)


if __name__ == "__main__":
    main(sys.argv)
