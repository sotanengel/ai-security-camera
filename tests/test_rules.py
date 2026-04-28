"""Tests for natural-language rules merged into prompts."""

from ai_security_camera.domain.rules import (
    UserRuleConfig,
    load_template_for_user_config,
    parse_user_rules_yaml,
    render_vlm_user_prompt,
)
from ai_security_camera.domain.templates import load_builtin_template


def test_parse_user_rules_example() -> None:
    yaml_text = """
template: uc_01
custom_rules:
  - "配達員が荷物を置いた場合は通知し、severityはmediumとする"
notification:
  channels: [ntfy]
"""
    cfg = parse_user_rules_yaml(yaml_text)
    assert cfg.template == "uc_01"
    assert len(cfg.custom_rules) == 1


def test_render_includes_custom_rules() -> None:
    t = load_builtin_template("uc_01")
    text = render_vlm_user_prompt(
        t,
        detector_summary="person 0.9",
        custom_rules_lines=["深夜は人物検知を必ず通知"],
    )
    assert "person 0.9" in text
    assert "深夜は人物検知を必ず通知" in text


def test_load_template_for_user_config() -> None:
    builtins = {
        "uc_01": load_builtin_template("uc_01"),
    }
    cfg = UserRuleConfig(template="uc_01", custom_rules=["ルール1"])
    resolved = load_template_for_user_config(cfg, builtins=builtins)
    assert resolved.id == "uc_01"
