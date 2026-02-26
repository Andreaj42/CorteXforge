from cortexforge.forge.utils.sigmf.hash import _sha512_hex


def make_sigmf_global(author: str, sample_rate, data_path: str):
    return {
            "core:author": author,
            "core:description": "CorteXForge recording",
            "core:recorder": "CorteXForge",
            "core:datatype": "cf32_le",
            "core:sample_rate": float(sample_rate),
            "core:data_file": data_path.name,
            "core:sha512": _sha512_hex(data_path),
        },
