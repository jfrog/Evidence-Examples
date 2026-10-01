import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from jsonl_to_json_converted import convert
from process_trufflehog_results import generate_markdown_report
from sanitize_trufflehog import sanitize_record

FIXTURE_PATH = pathlib.Path(__file__).with_name("vulnerable_setting")
KNOWN_TOKEN = "super-secret-token-SHOULD-NOT-LEAK"
KNOWN_TOKEN_V2 = "super-secret-token-SHOULD-NOT-LEAK-v2-user:pass"


def _finding(**overrides):
    record = {
        "SourceMetadata": {
            "Data": {
                "Filesystem": {
                    "file": "/pwd/examples/trufflehog/vulnerable_setting",
                    "line": 2,
                }
            }
        },
        "SourceID": 1,
        "SourceType": 15,
        "SourceName": "trufflehog - filesystem",
        "DetectorType": 17,
        "DetectorName": "AWS",
        "DetectorDescription": "AWS key",
        "DecoderName": "PLAIN",
        "Verified": True,
        "VerificationError": f"upstream echoed {KNOWN_TOKEN}",
        "Raw": KNOWN_TOKEN,
        "RawV2": KNOWN_TOKEN_V2,
        "Redacted": "super-secret-token-****",
        "ExtraData": {
            "account": "123456789012",
            "message": KNOWN_TOKEN,
            "secret": KNOWN_TOKEN_V2,
        },
        "StructuredData": {"raw": KNOWN_TOKEN},
    }
    record.update(overrides)
    return record


def _assert_secret_absent(blob, secret):
    if secret and secret in blob:
        raise AssertionError("secret material leaked into evidence output")


class SanitizeTrufflehogTest(unittest.TestCase):
    def test_markdown_omits_raw_secrets_and_keeps_redacted_summary(self):
        markdown = generate_markdown_report(_finding())

        self.assertIn("**Detector Name:** `AWS`", markdown)
        self.assertIn("**Verified:** `True`", markdown)
        self.assertIn("**Redacted Data:** `super-secret-token-****`", markdown)
        self.assertIn("vulnerable_setting:2", markdown)
        self.assertNotIn("Raw Data", markdown)
        self.assertNotIn("Extra Data", markdown)
        _assert_secret_absent(markdown, KNOWN_TOKEN)
        _assert_secret_absent(markdown, KNOWN_TOKEN_V2)

    def test_predicate_is_an_allowlist(self):
        sanitized = sanitize_record(_finding())

        self.assertEqual(
            set(sanitized),
            {
                "DetectorName",
                "DetectorType",
                "DetectorDescription",
                "DecoderName",
                "Verified",
                "SourceName",
                "SourceType",
                "SourceID",
                "SourceMetadata",
                "Redacted",
            },
        )
        encoded = json.dumps(sanitized)
        _assert_secret_absent(encoded, KNOWN_TOKEN)
        _assert_secret_absent(encoded, KNOWN_TOKEN_V2)
        self.assertNotIn("ExtraData", encoded)
        self.assertNotIn("VerificationError", encoded)
        self.assertEqual(sanitized["Redacted"], "super-secret-token-****")
        self.assertTrue(sanitized["Verified"])

    def test_redacted_field_that_echoes_raw_is_replaced(self):
        sanitized = sanitize_record(_finding(Redacted=KNOWN_TOKEN))
        self.assertEqual(sanitized["Redacted"], "[redacted]")
        _assert_secret_absent(json.dumps(sanitized), KNOWN_TOKEN)

    def test_converter_output_excludes_seeded_fixture_credentials(self):
        wanted_keys = {"aws_access_key_id", "aws_secret_access_key"}
        fixture_secrets = []
        for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in wanted_keys and value:
                fixture_secrets.append(value)
        self.assertEqual(len(fixture_secrets), 2)

        record = _finding(
            Raw=fixture_secrets[0],
            RawV2=fixture_secrets[1],
            ExtraData={"message": fixture_secrets[0], "secret": fixture_secrets[1]},
            Redacted="AKIA****",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "results.jsonl"
            dest = root / "trufflehog.json"
            source.write_text(json.dumps(record) + "\n", encoding="utf-8")
            convert(str(source), str(dest))
            predicate = dest.read_text(encoding="utf-8")

        for secret in fixture_secrets:
            _assert_secret_absent(predicate, secret)
        self.assertNotIn('"Raw"', predicate)
        self.assertIn("AKIA****", predicate)


if __name__ == "__main__":
    unittest.main()
