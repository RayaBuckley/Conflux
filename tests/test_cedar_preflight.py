"""Offline Cedar differential protocol and unavailable-result classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from jsonschema import Draft202012Validator

from conflux.adapters.scenarios import load_schema
from conflux.experiments import (
    cedar_differential_preflight,
    load_cedar_bundle,
    load_cedar_corpus,
)

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "experiments" / "manifests" / "cedar-policy-bundle-v1.json"
CORPUS = ROOT / "experiments" / "suites" / "cedar-differential-v1.json"


def test_cedar_preflight_covers_required_corpus_without_invoking_binary() -> None:
    bundle = load_cedar_bundle(BUNDLE)
    corpus = load_cedar_corpus(CORPUS)
    result = cedar_differential_preflight(bundle, corpus)
    case_list = cast(list[dict[str, object]], result["cases"])
    cases = {str(item["case_id"]): item for item in case_list}

    assert set(cases) == {
        "allow",
        "deny",
        "mixed-context",
        "recipient",
        "destination",
        "resource-selector",
        "missing-entity",
        "explicit-forbid",
    }
    assert result["classification"] == "evaluation_ready"
    assert result["cedar_status"] == "unavailable"
    assert result["complete"] is False
    assert all(item["cedar_decision"] is None for item in cases.values())
    assert cases["allow"]["oracle_allowed"] is True
    assert cases["mixed-context"]["oracle_allowed"] is False
    assert len(cast(list[object], cases["mixed-context"]["translated_requests"])) == 2
    assert cases["missing-entity"]["translated_requests"] == []
    assert cases["missing-entity"]["translation_denials"] == ["missing_resource_entity"]
    Draft202012Validator(load_schema("cedar-differential-result.schema.json")).validate(result)


def test_cedar_preflight_is_byte_deterministic() -> None:
    bundle = load_cedar_bundle(BUNDLE)
    corpus = load_cedar_corpus(CORPUS)
    first = cedar_differential_preflight(bundle, corpus)
    second = cedar_differential_preflight(bundle, corpus)
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second,
        sort_keys=True,
        separators=(",", ":"),
    )


def test_corpus_rejects_unknown_principals_and_request_overflow(tmp_path: Path) -> None:
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    payload["cases"][0]["allowed_principal_ids"] = ["mallory"]
    invalid = tmp_path / "unknown.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown Principal"):
        load_cedar_corpus(invalid)

    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    payload["max_requests"] = 1
    overflow = tmp_path / "overflow.json"
    overflow.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="request bound"):
        load_cedar_corpus(overflow)


def test_unknown_bundle_version_and_feature_fail_closed(tmp_path: Path) -> None:
    version = json.loads(BUNDLE.read_text(encoding="utf-8"))
    version["binary"]["version"] = "4.12.0"
    invalid_version = tmp_path / "version.json"
    invalid_version.write_text(json.dumps(version), encoding="utf-8")
    with pytest.raises(ValueError):
        load_cedar_bundle(invalid_version)

    feature = json.loads(BUNDLE.read_text(encoding="utf-8"))
    feature["supported_features"].append("templates")
    invalid_feature = tmp_path / "feature.json"
    invalid_feature.write_text(json.dumps(feature), encoding="utf-8")
    with pytest.raises(ValueError):
        load_cedar_bundle(invalid_feature)
