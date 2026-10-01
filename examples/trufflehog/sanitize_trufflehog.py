"""Strip secret material from TruffleHog findings before they become evidence.

Evidence is readable by every principal who can read the subject package, and a
signed predicate cannot be edited in place. TruffleHog puts the matched secret
in Raw/RawV2 and often again in ExtraData, so the published record is an
allowlist of non-secret fields.
"""

# Fields safe to publish. Anything else (Raw, RawV2, ExtraData, StructuredData,
# VerificationError) is dropped, including fields added by newer TruffleHog versions.
SAFE_FIELDS = (
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
)

_SECRET_VALUE_KEYS = ("Raw", "RawV2")
# Replacing a very short secret as a substring would corrupt unrelated text.
_MIN_SUBSTRING_SECRET_LENGTH = 8
_REDACTION_PLACEHOLDER = "[redacted]"


def sanitize_record(record):
    """Return a copy of a TruffleHog finding with secret fields removed."""
    if not isinstance(record, dict):
        raise TypeError("TruffleHog finding must be a JSON object")

    secrets = _secret_values(record)
    sanitized = {}
    for field in SAFE_FIELDS:
        if field not in record:
            continue
        sanitized[field] = _scrub(record[field], secrets)
    return sanitized


def source_location(record):
    """Human-readable file:line (or equivalent) from SourceMetadata."""
    metadata = record.get("SourceMetadata") if isinstance(record, dict) else None
    data = metadata.get("Data") if isinstance(metadata, dict) else None
    if not isinstance(data, dict) or not data:
        return "N/A"

    locations = []
    for details in data.values():
        if not isinstance(details, dict):
            continue
        path = details.get("file") or details.get("path") or ""
        line = details.get("line")
        if path and line is not None:
            locations.append(f"{path}:{line}")
        elif path:
            locations.append(str(path))
        elif line is not None:
            locations.append(f"line {line}")
    return ", ".join(locations) if locations else "N/A"


def _secret_values(record):
    secrets = []
    seen = set()
    for key in _SECRET_VALUE_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            secrets.append(value)
    secrets.sort(key=len, reverse=True)
    return secrets


def _scrub(value, secrets):
    if isinstance(value, str):
        return _scrub_string(value, secrets)
    if isinstance(value, list):
        return [_scrub(item, secrets) for item in value]
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key in _SECRET_VALUE_KEYS:
                continue
            cleaned[key] = _scrub(item, secrets)
        return cleaned
    return value


def _scrub_string(value, secrets):
    redacted = value
    for secret in secrets:
        if redacted == secret or (
            len(secret) >= _MIN_SUBSTRING_SECRET_LENGTH and secret in redacted
        ):
            redacted = redacted.replace(secret, _REDACTION_PLACEHOLDER)
    return redacted
