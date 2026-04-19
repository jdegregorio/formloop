"""Requirement traceability helpers."""

from __future__ import annotations

import re

from formloop.paths import repo_root

REQ_PATTERN = re.compile(r"FLH-[A-Z]+-\d{3}")


def build_traceability_report() -> dict[str, object]:
    requirements_text = (repo_root() / "REQUIREMENTS_HARNESS.md").read_text(encoding="utf-8")
    requirement_ids = sorted(set(REQ_PATTERN.findall(requirements_text)))

    referenced: dict[str, list[str]] = {}
    scan_paths = list((repo_root() / "src").rglob("*.py")) + list(
        (repo_root() / "tests").rglob("*.py")
    )
    for file_path in scan_paths:
        text = file_path.read_text(encoding="utf-8")
        for req_id in set(REQ_PATTERN.findall(text)):
            referenced.setdefault(req_id, []).append(str(file_path.relative_to(repo_root())))

    missing = [req_id for req_id in requirement_ids if req_id not in referenced]
    return {
        "total_requirements": len(requirement_ids),
        "referenced_requirements": len(referenced),
        "missing_requirements": missing,
        "references": referenced,
    }


def main() -> None:
    report = build_traceability_report()
    print(report)


if __name__ == "__main__":
    main()
