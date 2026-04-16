from __future__ import annotations

from pathlib import Path


def load_builtin_skill_texts(skill_dir: Path) -> dict[str, str]:
    skills: dict[str, str] = {}
    if not skill_dir.exists():
        return skills
    for path in sorted(skill_dir.glob("*.md")):
        skills[path.stem] = path.read_text(encoding="utf-8")
    return skills

