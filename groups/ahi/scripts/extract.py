"""Cut the fire area out of every Himawari-9 B07/B14 full-disk frame in data/ahi/raw/.

Rows 530:640, cols 1920:2120 of the 2 km full disk (segment 2 of 10), all 10-min frames
in one file: data/ahi/ahi_b07_b14_crop.npz (tags, b07, b14 in K; lon, lat).
"""

import glob
import os
import warnings
from multiprocessing import Pool

import numpy as np

from common import CROP, RAW

warnings.filterwarnings("ignore")
R0, R1, C0, C1 = 530, 640, 1920, 2120


def files(tag):
    return sorted(
        glob.glob(f"{RAW}/HS_H09_{tag}_B07_FLDK_R20_S0210.DAT.bz2")
        + glob.glob(f"{RAW}/HS_H09_{tag}_B14_FLDK_R20_S0210.DAT.bz2")
    )


def one(tag):
    from satpy import Scene

    fs = files(tag)
    if len(fs) < 2:
        return tag, None, None
    try:
        s = Scene(reader="ahi_hsd", filenames=fs)
        s.load(["B07", "B14"])
        return tag, s["B07"].values[R0:R1, C0:C1].astype("f4"), s["B14"].values[R0:R1, C0:C1].astype("f4")
    except Exception as e:
        print("ERR", tag, e, flush=True)
        return tag, None, None


if __name__ == "__main__":
    from satpy import Scene

    tags = sorted({os.path.basename(f)[7:20] for f in glob.glob(f"{RAW}/*_B07_*R20*")})
    s = Scene(reader="ahi_hsd", filenames=[files(tags[0])[0]])
    s.load(["B07"])
    lon, lat = s["B07"].attrs["area"].get_lonlats()
    with Pool(8) as p:
        res = p.map(one, tags, chunksize=4)
    res = [r for r in res if r[1] is not None]
    np.savez_compressed(
        CROP,
        tags=np.array([r[0] for r in res]),
        b07=np.stack([r[1] for r in res]),
        b14=np.stack([r[2] for r in res]),
        lon=lon[R0:R1, C0:C1].astype("f4"),
        lat=lat[R0:R1, C0:C1].astype("f4"),
    )
    print(len(res), "frames", res[0][0], res[-1][0])
