"""Tests for use-case template loading."""

from ai_security_camera.domain.templates import (
    UseCaseTemplate,
    list_builtin_template_ids,
    load_builtin_template,
)


def test_list_builtin_includes_three_templates() -> None:
    ids = list_builtin_template_ids()
    assert "uc_01" in ids
    assert "uc_02" in ids
    assert "uc_03" in ids
    assert len(ids) >= 3


def test_load_each_builtin() -> None:
    for tid in ("uc_01", "uc_02", "uc_03"):
        t = load_builtin_template(tid)
        assert isinstance(t, UseCaseTemplate)
        assert t.id == tid
        assert t.detector_classes
        assert t.vlm_system_prompt
