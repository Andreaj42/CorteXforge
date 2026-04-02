from json import dumps
from pathlib import Path

from cortexforge.forge.utils.sigmf.sigmf_annotations import make_sigmf_annotations
from cortexforge.forge.utils.sigmf.sigmf_captures import make_sigmf_captures
from cortexforge.forge.utils.sigmf.sigmf_global import make_sigmf_global


def write_sigmf(
    base_path: str,
    data_file: str,
    sample_rate: float,
    center_freq: float,
    gain: float,
    stat,
    annotations,
    hardware: str,
    description: str = "CorteXForge capture",
    author: str = "CorteXForge",
):
    """
    base_path: path without extension
    data_file: existing IQ file path (fc32 raw)
    Creates:
      - base_path.sigmf-data
      - base_path.sigmf-meta
    """
    base = Path(base_path)
    data_src = Path(data_file)

    meta_path = base.with_suffix(".sigmf-meta")
    data_path = base.with_suffix(".sigmf-data")

    # Move the data to .sigmf-data if needed
    if data_src.resolve() != data_path.resolve():
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_src.replace(data_path)


    meta = {
        "global": make_sigmf_global(
            author=author,
            sample_rate=sample_rate,
            data_path=data_path,
            description=description,
        ),
        "captures": make_sigmf_captures(
            center_freq=center_freq,
            gain=gain,
            hardware=hardware,
            stat=stat,
        ),
        "annotations": make_sigmf_annotations(annotations),
    }

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(dumps(meta, indent=2))
    return str(data_path), str(meta_path)
