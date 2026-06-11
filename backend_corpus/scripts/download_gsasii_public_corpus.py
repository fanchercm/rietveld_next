#!/usr/bin/env python3
"""Download the public GSAS-II tutorial files used by the backend test corpus.

This script is intended for opt-in corpus refreshes, not normal CI.
"""
from __future__ import annotations
import argparse
import hashlib
import pathlib
import urllib.parse
import urllib.request

TARGETS = [
    ("https://raw.githubusercontent.com/AdvancedPhotonSource/GSAS-II-tutorials/main/Simulation/data/", "gsasii/simulation", ["CuO.cif", "CuCr2O4.cif", "BT1.prm"]),
    ("https://raw.githubusercontent.com/AdvancedPhotonSource/GSAS-II-tutorials/main/TOF-CW%20Joint%20Refinement/data/", "gsasii/tof_cw_joint", ["NAC.cif", "CaF2.cif", "11BM_NAC.fxye", "11bm_gsas.prm", "PG3_22048.gsa", "PG3_22049.gsa", "POWGEN_1066.instprm", "POWGEN_2665.instprm", "NAC-2015A.EXP"]),
]

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="rietveld_public_backend_corpus")
    args = parser.parse_args()
    root = pathlib.Path(args.out)
    for base, subdir, files in TARGETS:
        outdir = root / subdir
        outdir.mkdir(parents=True, exist_ok=True)
        for name in files:
            url = base + urllib.parse.quote(name)
            dest = outdir / name
            print(f"download {url} -> {dest}")
            urllib.request.urlretrieve(url, dest)
            print(f"  size={dest.stat().st_size} sha256={sha256(dest)}")

if __name__ == "__main__":
    main()
