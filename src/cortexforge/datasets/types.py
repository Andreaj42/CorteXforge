from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(slots=True)
class SplitManifest:
    recordings: List[str]


@dataclass(slots=True)
class GeneratorManifest:
    name: str
    version: str


@dataclass(slots=True)
class DatasetManifest:
    name: str
    version: str
    description: str
    format: str
    generator: GeneratorManifest
    splits: Dict[str, SplitManifest]


@dataclass(slots=True)
class LocalDataset:
    name: str
    version: str
    split: str
    root: Path
    recordings: List[Path]
