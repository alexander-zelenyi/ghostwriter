from pathlib import Path

import pytest
from pydantic import ValidationError

from ghostwriter_agent.adapters import YamlPromptReader
from ghostwriter_agent.ports import PromptReader
from tests.conftest import PROMPTS_DIR


def write_prompt(directory: Path, name: str, content: str) -> None:
    (directory / f"{name}.yaml").write_text(content, encoding="utf-8")


def test_reader_implements_the_port() -> None:
    assert isinstance(YamlPromptReader(PROMPTS_DIR), PromptReader)


def test_real_system_prompt_mentions_the_owner() -> None:
    prompt = YamlPromptReader(PROMPTS_DIR).system_prompt(owner_name="Alex")

    assert "Alex" in prompt
    assert "{owner_name}" not in prompt


def test_system_prompt_is_rendered_from_the_yaml_template(tmp_path: Path) -> None:
    write_prompt(tmp_path, "system", "template: |\n  Speak for {owner_name}. Use {{braces}}.\n")

    prompt = YamlPromptReader(tmp_path).system_prompt(owner_name="Alex")

    assert prompt == "Speak for Alex. Use {braces}.\n"


def test_prompt_file_is_read_once(tmp_path: Path) -> None:
    write_prompt(tmp_path, "system", "template: first {owner_name}")
    reader = YamlPromptReader(tmp_path)
    reader.system_prompt(owner_name="A")

    write_prompt(tmp_path, "system", "template: second {owner_name}")

    assert reader.system_prompt(owner_name="A") == "first A"


def test_missing_prompts_directory_fails_at_construction(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        YamlPromptReader(tmp_path / "missing")


def test_missing_prompt_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        YamlPromptReader(tmp_path).system_prompt(owner_name="Alex")


def test_prompt_file_with_unknown_keys_is_rejected(tmp_path: Path) -> None:
    write_prompt(tmp_path, "system", "template: hi\ntemplte: typo\n")

    with pytest.raises(ValidationError):
        YamlPromptReader(tmp_path).system_prompt(owner_name="Alex")
