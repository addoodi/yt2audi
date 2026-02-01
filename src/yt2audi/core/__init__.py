"""Core functionality for YT2Audi."""

from yt2audi.core.converter import Converter, VideoMetadata
from yt2audi.core.downloader import Downloader
from yt2audi.core.history import HistoryManager
from yt2audi.core.gpu_detector import GPUInfo, GPUVendor, select_best_encoder
from yt2audi.core.pipeline import ProcessingPipeline
from yt2audi.core.splitter import Splitter

__all__ = [
    "Converter",
    "VideoMetadata",
    "Downloader",
    "HistoryManager",
    "GPUInfo",
    "GPUVendor",
    "select_best_encoder",
    "ProcessingPipeline",
    "Splitter",
]
