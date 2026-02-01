"""GPU detection and encoder selection."""

import subprocess
from enum import Enum

import structlog
try:
    import py3nvml.py3nvml as nvml
except ImportError:
    nvml = None

try:
    import GPUtil
except ImportError:
    GPUtil = None

from yt2audi.exceptions import GPUDetectionError
from yt2audi.models.profile import EncoderType

logger = structlog.get_logger(__name__)


class GPUVendor(str, Enum):
    """GPU vendor types."""

    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    UNKNOWN = "unknown"


class GPUInfo:
    """GPU information."""

    def __init__(self, vendor: GPUVendor, name: str, has_encoder: bool) -> None:
        """Initialize GPU info.

        Args:
            vendor: GPU vendor
            name: GPU model name
            has_encoder: Whether GPU has hardware encoder
        """
        self.vendor = vendor
        self.name = name
        self.has_encoder = has_encoder

    def __repr__(self) -> str:
        """String representation."""
        return f"GPUInfo(vendor={self.vendor}, name={self.name}, has_encoder={self.has_encoder})"


def detect_nvidia_gpu() -> GPUInfo | None:
    """Detect NVIDIA GPU using py3nvml.

    Returns:
        GPUInfo if NVIDIA GPU found, None otherwise
    """
    if nvml is None:
        return None

    try:
        nvml.nvmlInit()
        device_count = nvml.nvmlDeviceGetCount()

        if device_count > 0:
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            name = nvml.nvmlDeviceGetName(handle)

            # Decode bytes to string if needed
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            logger.info("nvidia_gpu_detected", name=name, device_count=device_count)
            nvml.nvmlShutdown()

            return GPUInfo(vendor=GPUVendor.NVIDIA, name=name, has_encoder=True)

        nvml.nvmlShutdown()
    except Exception as e:
        logger.debug("nvidia_detection_failed", error=str(e))

    return None


def detect_amd_gpu() -> GPUInfo | None:
    """Detect AMD GPU using GPUtil or system commands.

    Returns:
        GPUInfo if AMD GPU found, None otherwise
    """
    if GPUtil is None:
        return None

    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            if "amd" in gpu.name.lower() or "radeon" in gpu.name.lower():
                logger.info("amd_gpu_detected", name=gpu.name)
                return GPUInfo(vendor=GPUVendor.AMD, name=gpu.name, has_encoder=True)
    except Exception as e:
        logger.debug("amd_detection_gputil_failed", error=str(e))

    # Fallback: Try to detect via FFmpeg encoders
    if check_ffmpeg_encoder("h264_amf"):
        logger.info("amd_gpu_detected_via_ffmpeg")
        return GPUInfo(vendor=GPUVendor.AMD, name="AMD GPU (via FFmpeg)", has_encoder=True)

    return None


def detect_intel_gpu() -> GPUInfo | None:
    """Detect Intel GPU with QuickSync support.

    Returns:
        GPUInfo if Intel GPU found, None otherwise
    """
    if GPUtil is None:
        return None

    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            if "intel" in gpu.name.lower():
                logger.info("intel_gpu_detected", name=gpu.name)
                return GPUInfo(vendor=GPUVendor.INTEL, name=gpu.name, has_encoder=True)
    except Exception as e:
        logger.debug("intel_detection_gputil_failed", error=str(e))

    # Fallback: Try to detect via FFmpeg encoders
    if check_ffmpeg_encoder("h264_qsv"):
        logger.info("intel_gpu_detected_via_ffmpeg")
        return GPUInfo(vendor=GPUVendor.INTEL, name="Intel GPU (via FFmpeg)", has_encoder=True)

    return None


def check_ffmpeg_encoder(encoder_name: str) -> bool:
    """Check if FFmpeg supports a specific encoder.

    Args:
        encoder_name: FFmpeg encoder name (e.g., "h264_nvenc")

    Returns:
        True if encoder is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode == 0:
            return encoder_name in result.stdout

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("ffmpeg_encoder_check_failed", encoder=encoder_name, error=str(e))

    return False


def detect_available_gpus() -> list[GPUInfo]:
    """Detect all available GPUs.

    Returns:
        List of GPUInfo objects for detected GPUs
    """
    gpus: list[GPUInfo] = []

    # Try NVIDIA
    nvidia = detect_nvidia_gpu()
    if nvidia:
        gpus.append(nvidia)

    # Try AMD
    amd = detect_amd_gpu()
    if amd:
        gpus.append(amd)

    # Try Intel
    intel = detect_intel_gpu()
    if intel:
        gpus.append(intel)

    return gpus


def select_best_encoder(encoder_priority: list[EncoderType]) -> EncoderType:
    """Select the best available encoder based on priority list.

    Args:
        encoder_priority: Ordered list of preferred encoders

    Returns:
        Best available encoder

    Raises:
        GPUDetectionError: If no encoder is available

    The function checks each encoder in priority order and returns
    the first one that is available. If no hardware encoder is found,
    it falls back to libx264 (CPU encoding).
    """
    logger.info("selecting_encoder", priority=encoder_priority)

    # Detect available GPUs
    gpus = detect_available_gpus()
    logger.info("gpus_detected", count=len(gpus), gpus=[str(gpu) for gpu in gpus])

    # Map GPU vendors to encoder types
    vendor_encoder_map = {
        GPUVendor.NVIDIA: EncoderType.NVENC_H264,
        GPUVendor.AMD: EncoderType.AMF_H264,
        GPUVendor.INTEL: EncoderType.QSV_H264,
    }

    # Build set of available encoders
    available_encoders = set()
    for gpu in gpus:
        if gpu.has_encoder and gpu.vendor in vendor_encoder_map:
            encoder = vendor_encoder_map[gpu.vendor]
            # Verify encoder is actually available in FFmpeg
            if check_ffmpeg_encoder(encoder.value):
                available_encoders.add(encoder)

    # Always add libx264 as CPU fallback
    if check_ffmpeg_encoder(EncoderType.LIBX264.value):
        available_encoders.add(EncoderType.LIBX264)

    logger.info("available_encoders", encoders=[e.value for e in available_encoders])

    # Select first available encoder from priority list
    for encoder in encoder_priority:
        if encoder in available_encoders:
            logger.info("encoder_selected", encoder=encoder.value)
            return encoder

    # If nothing from priority list is available, use libx264
    if EncoderType.LIBX264 in available_encoders:
        logger.warning("no_priority_encoder_available_using_fallback", encoder="libx264")
        return EncoderType.LIBX264

    raise GPUDetectionError("No video encoder available (FFmpeg not found or misconfigured)")


def get_encoder_preset(encoder: EncoderType) -> str:
    """Get the appropriate preset for an encoder.

    Args:
        encoder: Encoder type

    Returns:
        Preset string for FFmpeg

    Different encoders use different preset names:
    - NVENC: p1-p7 (p4 = balanced)
    - AMF: speed/balanced/quality
    - QuickSync: veryfast/faster/fast/medium/slow
    - libx264: ultrafast/superfast/veryfast/faster/fast/medium/slow/slower/veryslow
    """
    preset_map = {
        EncoderType.NVENC_H264: "p4",  # Balanced performance/quality
        EncoderType.AMF_H264: "balanced",
        EncoderType.QSV_H264: "medium",
        EncoderType.LIBX264: "medium",
    }

    return preset_map.get(encoder, "medium")


def get_encoder_extra_args(encoder: EncoderType, quality_cq: int) -> list[str]:
    """Get encoder-specific extra arguments.

    Args:
        encoder: Encoder type
        quality_cq: Quality CQ value (0-51, lower = better)

    Returns:
        List of FFmpeg arguments
    """
    args: list[str] = []

    if encoder == EncoderType.NVENC_H264:
        args.extend(["-rc:v:0", "vbr", "-cq:v:0", str(quality_cq)])
    elif encoder == EncoderType.AMF_H264:
        args.extend(["-rc:v:0", "vbr_latency", "-qp_i:v:0", str(quality_cq)])
    elif encoder == EncoderType.QSV_H264:
        args.extend(["-global_quality:v:0", str(quality_cq)])
    elif encoder == EncoderType.LIBX264:
        args.extend(["-crf:v:0", str(quality_cq)])

    return args
