"""Unit tests for GPU detection logic."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt2audi.core.gpu_detector import (
    GPUInfo,
    GPUVendor,
    check_ffmpeg_encoder,
    detect_amd_gpu,
    detect_available_gpus,
    detect_intel_gpu,
    detect_nvidia_gpu,
    get_encoder_extra_args,
    get_encoder_preset,
    select_best_encoder,
)
from yt2audi.exceptions import GPUDetectionError
from yt2audi.models.profile import EncoderType


class TestGPUInfo:
    """Test suite for GPUInfo class."""

    def test_gpu_info_creation(self) -> None:
        """Test creating GPUInfo instance."""
        gpu = GPUInfo(
            vendor=GPUVendor.NVIDIA,
            name="NVIDIA RTX 4090",
            has_encoder=True,
        )
        assert gpu.vendor == GPUVendor.NVIDIA
        assert gpu.name == "NVIDIA RTX 4090"
        assert gpu.has_encoder is True

    def test_gpu_info_repr(self) -> None:
        """Test GPUInfo string representation."""
        gpu = GPUInfo(
            vendor=GPUVendor.AMD,
            name="AMD Radeon RX 7900 XTX",
            has_encoder=True,
        )
        repr_str = repr(gpu)
        assert "AMD" in repr_str
        assert "Radeon" in repr_str


class TestDetectNvidiaGPU:
    """Test suite for NVIDIA GPU detection."""

    @patch("yt2audi.core.gpu_detector.py3nvml")
    def test_detect_nvidia_gpu_found(self, mock_nvml: Mock) -> None:
        """Test NVIDIA GPU detection when GPU is found."""
        # Mock NVML functions
        mock_nvml.py3nvml.nvmlInit.return_value = None
        mock_nvml.py3nvml.nvmlDeviceGetCount.return_value = 1
        mock_nvml.py3nvml.nvmlDeviceGetHandleByIndex.return_value = MagicMock()
        mock_nvml.py3nvml.nvmlDeviceGetName.return_value = "NVIDIA RTX 4090"
        mock_nvml.py3nvml.nvmlShutdown.return_value = None

        result = detect_nvidia_gpu()

        assert result is not None
        assert result.vendor == GPUVendor.NVIDIA
        assert "RTX 4090" in result.name
        assert result.has_encoder is True

    @patch("yt2audi.core.gpu_detector.py3nvml")
    def test_detect_nvidia_gpu_bytes_name(self, mock_nvml: Mock) -> None:
        """Test NVIDIA GPU detection with bytes name."""
        # Mock NVML functions with bytes return
        mock_nvml.py3nvml.nvmlInit.return_value = None
        mock_nvml.py3nvml.nvmlDeviceGetCount.return_value = 1
        mock_nvml.py3nvml.nvmlDeviceGetHandleByIndex.return_value = MagicMock()
        mock_nvml.py3nvml.nvmlDeviceGetName.return_value = b"NVIDIA GTX 1080"
        mock_nvml.py3nvml.nvmlShutdown.return_value = None

        result = detect_nvidia_gpu()

        assert result is not None
        assert "GTX 1080" in result.name
        assert isinstance(result.name, str)

    @patch("yt2audi.core.gpu_detector.py3nvml")
    def test_detect_nvidia_gpu_not_found(self, mock_nvml: Mock) -> None:
        """Test NVIDIA GPU detection when no GPU found."""
        mock_nvml.py3nvml.nvmlInit.return_value = None
        mock_nvml.py3nvml.nvmlDeviceGetCount.return_value = 0
        mock_nvml.py3nvml.nvmlShutdown.return_value = None

        result = detect_nvidia_gpu()

        assert result is None

    def test_detect_nvidia_gpu_import_error(self) -> None:
        """Test NVIDIA GPU detection when py3nvml not available."""
        with patch.dict("sys.modules", {"py3nvml": None, "py3nvml.py3nvml": None}):
            result = detect_nvidia_gpu()
            # Should handle import error gracefully
            assert result is None


class TestDetectAMDGPU:
    """Test suite for AMD GPU detection."""

    @patch("yt2audi.core.gpu_detector.GPUtil")
    def test_detect_amd_gpu_via_gputil(self, mock_gputil: Mock) -> None:
        """Test AMD GPU detection via GPUtil."""
        # Mock GPU object
        mock_gpu = MagicMock()
        mock_gpu.name = "AMD Radeon RX 6800"
        mock_gputil.getGPUs.return_value = [mock_gpu]

        result = detect_amd_gpu()

        assert result is not None
        assert result.vendor == GPUVendor.AMD
        assert "6800" in result.name

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.GPUtil")
    def test_detect_amd_gpu_via_ffmpeg_fallback(
        self,
        mock_gputil: Mock,
        mock_check_encoder: Mock,
    ) -> None:
        """Test AMD GPU detection via FFmpeg fallback."""
        # GPUtil fails
        mock_gputil.getGPUs.side_effect = Exception("GPUtil not available")
        # FFmpeg encoder check succeeds
        mock_check_encoder.return_value = True

        result = detect_amd_gpu()

        assert result is not None
        assert result.vendor == GPUVendor.AMD
        assert "via FFmpeg" in result.name

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.GPUtil")
    def test_detect_amd_gpu_not_found(
        self,
        mock_gputil: Mock,
        mock_check_encoder: Mock,
    ) -> None:
        """Test AMD GPU detection when no GPU found."""
        mock_gputil.getGPUs.return_value = []
        mock_check_encoder.return_value = False

        result = detect_amd_gpu()

        assert result is None


class TestDetectIntelGPU:
    """Test suite for Intel GPU detection."""

    @patch("yt2audi.core.gpu_detector.GPUtil")
    def test_detect_intel_gpu_via_gputil(self, mock_gputil: Mock) -> None:
        """Test Intel GPU detection via GPUtil."""
        mock_gpu = MagicMock()
        mock_gpu.name = "Intel UHD Graphics 630"
        mock_gputil.getGPUs.return_value = [mock_gpu]

        result = detect_intel_gpu()

        assert result is not None
        assert result.vendor == GPUVendor.INTEL
        assert "Intel" in result.name

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.GPUtil")
    def test_detect_intel_gpu_via_ffmpeg_fallback(
        self,
        mock_gputil: Mock,
        mock_check_encoder: Mock,
    ) -> None:
        """Test Intel GPU detection via FFmpeg fallback."""
        mock_gputil.getGPUs.side_effect = Exception("GPUtil error")
        mock_check_encoder.return_value = True

        result = detect_intel_gpu()

        assert result is not None
        assert result.vendor == GPUVendor.INTEL


class TestCheckFFmpegEncoder:
    """Test suite for FFmpeg encoder checking."""

    @patch("subprocess.run")
    def test_check_ffmpeg_encoder_available(self, mock_run: Mock) -> None:
        """Test checking for available FFmpeg encoder."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" V..... h264_nvenc          NVIDIA NVENC H.264 encoder\n",
        )

        result = check_ffmpeg_encoder("h264_nvenc")

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_check_ffmpeg_encoder_not_available(self, mock_run: Mock) -> None:
        """Test checking for unavailable FFmpeg encoder."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" V..... libx264          libx264 H.264 / AVC\n",
        )

        result = check_ffmpeg_encoder("h264_nvenc")

        assert result is False

    @patch("subprocess.run")
    def test_check_ffmpeg_encoder_timeout(self, mock_run: Mock) -> None:
        """Test FFmpeg encoder check timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=10)

        result = check_ffmpeg_encoder("h264_nvenc")

        assert result is False

    @patch("subprocess.run")
    def test_check_ffmpeg_encoder_not_found(self, mock_run: Mock) -> None:
        """Test FFmpeg encoder check when ffmpeg not found."""
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")

        result = check_ffmpeg_encoder("h264_nvenc")

        assert result is False


class TestDetectAvailableGPUs:
    """Test suite for detecting all available GPUs."""

    @patch("yt2audi.core.gpu_detector.detect_intel_gpu")
    @patch("yt2audi.core.gpu_detector.detect_amd_gpu")
    @patch("yt2audi.core.gpu_detector.detect_nvidia_gpu")
    def test_detect_all_gpus(
        self,
        mock_nvidia: Mock,
        mock_amd: Mock,
        mock_intel: Mock,
    ) -> None:
        """Test detecting all GPU types."""
        mock_nvidia.return_value = GPUInfo(GPUVendor.NVIDIA, "RTX 4090", True)
        mock_amd.return_value = GPUInfo(GPUVendor.AMD, "RX 7900", True)
        mock_intel.return_value = GPUInfo(GPUVendor.INTEL, "UHD 630", True)

        result = detect_available_gpus()

        assert len(result) == 3
        assert result[0].vendor == GPUVendor.NVIDIA
        assert result[1].vendor == GPUVendor.AMD
        assert result[2].vendor == GPUVendor.INTEL

    @patch("yt2audi.core.gpu_detector.detect_intel_gpu")
    @patch("yt2audi.core.gpu_detector.detect_amd_gpu")
    @patch("yt2audi.core.gpu_detector.detect_nvidia_gpu")
    def test_detect_no_gpus(
        self,
        mock_nvidia: Mock,
        mock_amd: Mock,
        mock_intel: Mock,
    ) -> None:
        """Test when no GPUs are detected."""
        mock_nvidia.return_value = None
        mock_amd.return_value = None
        mock_intel.return_value = None

        result = detect_available_gpus()

        assert len(result) == 0


class TestSelectBestEncoder:
    """Test suite for encoder selection logic."""

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.detect_available_gpus")
    def test_select_best_encoder_nvidia_preferred(
        self,
        mock_detect: Mock,
        mock_check: Mock,
    ) -> None:
        """Test encoder selection with NVIDIA GPU available."""
        mock_detect.return_value = [
            GPUInfo(GPUVendor.NVIDIA, "RTX 4090", True),
        ]
        mock_check.return_value = True

        priority = [
            EncoderType.NVENC_H264,
            EncoderType.AMF_H264,
            EncoderType.QSV_H264,
            EncoderType.LIBX264,
        ]

        result = select_best_encoder(priority)

        assert result == EncoderType.NVENC_H264

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.detect_available_gpus")
    def test_select_best_encoder_fallback_to_cpu(
        self,
        mock_detect: Mock,
        mock_check: Mock,
    ) -> None:
        """Test encoder selection fallback to CPU when no GPU."""
        mock_detect.return_value = []

        def check_encoder(encoder_name: str) -> bool:
            return encoder_name == "libx264"

        mock_check.side_effect = check_encoder

        priority = [
            EncoderType.NVENC_H264,
            EncoderType.LIBX264,
        ]

        result = select_best_encoder(priority)

        assert result == EncoderType.LIBX264

    @patch("yt2audi.core.gpu_detector.check_ffmpeg_encoder")
    @patch("yt2audi.core.gpu_detector.detect_available_gpus")
    def test_select_best_encoder_no_encoder_available(
        self,
        mock_detect: Mock,
        mock_check: Mock,
    ) -> None:
        """Test encoder selection when no encoder available."""
        mock_detect.return_value = []
        mock_check.return_value = False

        priority = [EncoderType.NVENC_H264, EncoderType.LIBX264]

        with pytest.raises(GPUDetectionError, match="No video encoder available"):
            select_best_encoder(priority)


class TestGetEncoderPreset:
    """Test suite for encoder preset mapping."""

    def test_get_nvenc_preset(self) -> None:
        """Test getting NVENC preset."""
        preset = get_encoder_preset(EncoderType.NVENC_H264)
        assert preset == "p4"

    def test_get_amf_preset(self) -> None:
        """Test getting AMF preset."""
        preset = get_encoder_preset(EncoderType.AMF_H264)
        assert preset == "balanced"

    def test_get_qsv_preset(self) -> None:
        """Test getting QuickSync preset."""
        preset = get_encoder_preset(EncoderType.QSV_H264)
        assert preset == "medium"

    def test_get_libx264_preset(self) -> None:
        """Test getting libx264 preset."""
        preset = get_encoder_preset(EncoderType.LIBX264)
        assert preset == "medium"


class TestGetEncoderExtraArgs:
    """Test suite for encoder extra arguments."""

    def test_get_nvenc_extra_args(self) -> None:
        """Test getting NVENC extra arguments."""
        args = get_encoder_extra_args(EncoderType.NVENC_H264, quality_cq=24)
        assert "-rc" in args
        assert "vbr" in args
        assert "-cq" in args
        assert "24" in args

    def test_get_amf_extra_args(self) -> None:
        """Test getting AMF extra arguments."""
        args = get_encoder_extra_args(EncoderType.AMF_H264, quality_cq=22)
        assert "-rc" in args
        assert "vbr_latency" in args
        assert "-qp_i" in args
        assert "22" in args

    def test_get_qsv_extra_args(self) -> None:
        """Test getting QuickSync extra arguments."""
        args = get_encoder_extra_args(EncoderType.QSV_H264, quality_cq=25)
        assert "-global_quality" in args
        assert "25" in args

    def test_get_libx264_extra_args(self) -> None:
        """Test getting libx264 extra arguments."""
        args = get_encoder_extra_args(EncoderType.LIBX264, quality_cq=23)
        assert "-crf" in args
        assert "23" in args
