"""`PromptReader` adapter that reads prompt templates from YAML files.

Each prompt lives in its own file `<prompts_dir>/<name>.yaml` with a `template` key.
Files are read on first use and cached, so editing a prompt requires a restart.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class PromptFile(BaseModel):
    """Schema of a prompt file; unknown keys are rejected to catch typos early."""

    model_config = ConfigDict(extra="forbid")

    template: str


class YamlPromptReader:
    def __init__(self, prompts_dir: Path) -> None:
        if not prompts_dir.is_dir():
            raise FileNotFoundError(f"Prompts directory not found: {prompts_dir.resolve()}")
        self._prompts_dir = prompts_dir
        self._templates: dict[str, str] = {}

    def system_prompt(self, owner_name: str) -> str:
        return self._template("system").format(owner_name=owner_name)

    def _template(self, name: str) -> str:
        if name not in self._templates:
            self._templates[name] = self._load(name)
        return self._templates[name]

    def _load(self, name: str) -> str:
        path = self._prompts_dir / f"{name}.yaml"
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
        return PromptFile.model_validate(data).template
