"""
SeasonAlpha - Data Layer
=========================
Dünner Wrapper um yahoo_downloader.
Cache liegt in yahoo_downloader.py (ttl=3600).
"""

import pandas as pd
import numpy as np

from shared.yahoo_downloader import (
    download_data,
    preprocess,
)

# download_data und preprocess direkt re-exportiert
# KEIN zusätzlicher Cache hier — yahoo_downloader cached bereits!
