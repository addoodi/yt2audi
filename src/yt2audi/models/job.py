"""Job/task models for tracking download and conversion progress."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status states."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    CONVERTING = "converting"
    CONVERTED = "converted"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job types."""

    SINGLE_VIDEO = "single_video"
    BATCH = "batch"
    PLAYLIST = "playlist"


class Job(BaseModel):
    """Represents a download/conversion job."""

    id: UUID = Field(default_factory=uuid4)
    job_type: JobType
    url: str
    status: JobStatus = Field(default=JobStatus.PENDING)
    profile_name: str

    # Progress tracking
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    current_stage: str = Field(default="Queued")
    eta_seconds: int | None = Field(default=None)

    # File paths
    downloaded_path: Path | None = Field(default=None)
    converted_path: Path | None = Field(default=None)
    final_paths: list[Path] = Field(default_factory=list)

    # Metadata
    video_title: str | None = Field(default=None)
    video_id: str | None = Field(default=None)
    duration_seconds: int | None = Field(default=None)
    file_size_mb: float | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)

    # Error tracking
    error_message: str | None = Field(default=None)
    retry_count: int = Field(default=0)

    # Additional data
    extra_data: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def mark_downloading(self) -> None:
        """Mark job as downloading."""
        self.status = JobStatus.DOWNLOADING
        self.current_stage = "Downloading"
        if not self.started_at:
            self.started_at = datetime.now()

    def mark_downloaded(self, path: Path) -> None:
        """Mark job as downloaded."""
        self.status = JobStatus.DOWNLOADED
        self.current_stage = "Downloaded"
        self.downloaded_path = path

    def mark_converting(self) -> None:
        """Mark job as converting."""
        self.status = JobStatus.CONVERTING
        self.current_stage = "Converting"

    def mark_converted(self, path: Path) -> None:
        """Mark job as converted."""
        self.status = JobStatus.CONVERTED
        self.current_stage = "Converted"
        self.converted_path = path

    def mark_transferring(self) -> None:
        """Mark job as transferring."""
        self.status = JobStatus.TRANSFERRING
        self.current_stage = "Transferring"

    def mark_completed(self, final_paths: list[Path]) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.current_stage = "Completed"
        self.final_paths = final_paths
        self.completed_at = datetime.now()
        self.progress_percent = 100.0

    def mark_failed(self, error: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.current_stage = "Failed"
        self.error_message = error
        self.completed_at = datetime.now()

    def mark_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.current_stage = "Cancelled"
        self.completed_at = datetime.now()

    def update_progress(self, percent: float, stage: str, eta: int | None = None) -> None:
        """Update job progress.

        Args:
            percent: Progress percentage (0-100)
            stage: Current stage description
            eta: Estimated time remaining in seconds
        """
        self.progress_percent = max(0.0, min(100.0, percent))
        self.current_stage = stage
        self.eta_seconds = eta

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
