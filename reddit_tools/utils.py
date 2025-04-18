from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def get_secrets(secrets_filepath: Path | str) -> dict:
    with open(secrets_filepath, mode="r") as f:
        key_values = (l.strip().split(":") for l in f.readlines())
    secrets = {k: v for k, v in key_values}
    return secrets
