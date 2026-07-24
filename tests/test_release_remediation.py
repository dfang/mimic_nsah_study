from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def test_bundle_members_and_stage_indexes_use_current_hashes() -> None:
    manifest = load_yaml("study-manifest.yaml")

    for stage in manifest["stages"].values():
        artifact = stage.get("artifact")
        expected_hash = stage.get("sha256")
        if artifact and expected_hash:
            assert sha256(ROOT / artifact) == expected_hash, artifact

    for bundle_path in sorted((ROOT / "reproducibility" / "bundles").glob("*.yaml")):
        bundle = load_yaml(str(bundle_path.relative_to(ROOT)))
        for artifact in bundle.get("artifacts", []):
            path = artifact["path"]
            assert sha256(ROOT / path) == artifact["sha256"], (
                f"{bundle_path.relative_to(ROOT)} -> {path}"
            )


def test_analysis_bundle_contains_canonical_results_and_transcript_boundary() -> None:
    bundle = load_yaml("reproducibility/bundles/analysis.yaml")
    roles = {artifact["role"] for artifact in bundle["artifacts"]}

    assert "canonical_frozen_results" in roles
    assert "superseded_execution_transcript" in roles


def test_manuscript_review_bundle_is_pending_independent_rereview() -> None:
    bundle = load_yaml("reproducibility/bundles/manuscript-review.yaml")
    roles = {artifact["role"] for artifact in bundle["artifacts"]}

    assert bundle["gate_status"] == "pending_independent_rereview"
    assert "review_input" in roles
    assert "current_issue_register" in roles


def test_issue_register_uses_canonical_finding_fields() -> None:
    register = load_yaml("reproducibility/issue-register.yaml")
    required = {
        "id",
        "severity",
        "gate_effect",
        "confidence",
        "stage",
        "domain",
        "artifact",
        "location",
        "evidence",
        "risk",
        "recommended_action",
        "owner",
        "verification",
        "status",
        "closure_evidence",
        "closed_by",
        "closed_at",
    }
    valid_statuses = {"open", "resolved", "accepted-risk", "not-assessed"}
    valid_domains = {
        "governance",
        "design",
        "data",
        "clinical",
        "statistics",
        "reporting",
        "reproducibility",
    }

    for finding in register["issues"]:
        assert required <= finding.keys(), finding["id"]
        assert finding["status"] in valid_statuses, finding["id"]
        assert finding["domain"] in valid_domains, finding["id"]


def test_public_release_approval_is_explicitly_blocked() -> None:
    governance = load_yaml("reproducibility/governance-status.yaml")

    assert governance["public_aggregate_release_status"] == (
        "BLOCKED_PENDING_AUTHOR_INSTITUTION_APPROVAL"
    )
    assert governance["approval_recorded"] is False


def test_pdf_generation_manifest_binds_outputs_to_current_sources() -> None:
    generation = load_yaml("dist/pdf/generation-manifest.yaml")

    for artifact in generation["outputs"]:
        assert sha256(ROOT / artifact["path"]) == artifact["sha256"], artifact["path"]

    source_matches = [
        sha256(ROOT / artifact["path"]) == artifact["sha256"]
        for artifact in generation["sources"]
    ]
    if generation["status"] == "STALE_AFTER_AUTHORIZED_EICU_RERUN":
        assert not all(source_matches)
        assert generation["stale_against_current_sources"] is True
    else:
        assert all(source_matches)


def test_manuscript_scopes_available_validation_evidence() -> None:
    english = (ROOT / "dist/manuscript_non_traumatic_sah_phenotypes_cited.md").read_text(
        encoding="utf-8"
    )

    assert "Frozen MIMIC transforms and centroids assigned eICU phenotypes." in english
    assert "without fitting, tuning, or recalibration on eICU data" in english
    assert "stable phenotypes" not in english
    assert "overall partition stability" in english
