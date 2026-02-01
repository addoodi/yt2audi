"""Helper functions for CLI to reduce code duplication."""

from pathlib import Path
from typing import Any, Callable, Optional
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from yt2audi.core import Converter, Downloader, ProcessingPipeline, Splitter, HistoryManager
from yt2audi.models.profile import Profile
from yt2audi.transfer import USBManager

console = Console()


class BatchProgressManager:
    """Manages multiple progress bars for concurrent batch tasks."""

    def __init__(self, console_obj: Console) -> None:
        """Initialize progress manager.

        Args:
            console_obj: Rich console instance
        """
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console_obj,
            refresh_per_second=10,
        )
        self.tasks: dict[str, TaskID] = {}

    def get_callback(self) -> Callable[[str, float, str], None]:
        """Get a callback function for the pipeline.

        Returns:
            Callback(url, percent, stage)
        """
        def callback(url: str, percent: float, stage: str) -> None:
            if url not in self.tasks:
                # Use video ID or last part of URL as label
                label = url.split("v=")[-1][:8] if "v=" in url else url[-8:]
                task_id = self.progress.add_task(
                    f"[cyan]{label}[/cyan] Queued",
                    total=100
                )
                self.tasks[url] = task_id
            
            label = url.split("v=")[-1][:8] if "v=" in url else url[-8:]
            self.progress.update(
                self.tasks[url],
                completed=percent,
                description=f"[cyan]{label}[/cyan] {stage}"
            )
        
        return callback

    def __enter__(self) -> Progress:
        return self.progress.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.progress.__exit__(exc_type, exc_val, exc_tb)


def create_download_progress() -> tuple[Progress, Callable]:
    """Create a progress bar for downloads.
    
    Returns:
        Tuple of (Progress object, progress_hook callable)
    """
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
    
    task_id = None
    
    def progress_hook(d: dict) -> None:
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task("Downloading...", total=100)
        
        if d.get("status") == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            if total > 0:
                percent = (downloaded / total) * 100
                progress.update(task_id, completed=percent)
    
    return progress, progress_hook


def create_convert_progress() -> tuple[Progress, Callable]:
    """Create a progress bar for conversion.
    
    Returns:
        Tuple of (Progress object, convert_progress callable)
    """
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    
    task_id = None
    
    def convert_progress(percent: float, stage: str) -> None:
        nonlocal task_id
        if task_id is None:
            task_id = progress.add_task("Converting...", total=100)
        progress.update(task_id, completed=percent, description=stage)
    
    return progress, convert_progress


def process_single_video(
    url: str,
    prof: Profile,
    output_dir: Path,
    downloader: Downloader,
    converter: Converter,
    show_progress: bool = True,
    skip_conversion: bool = False,
) -> list[Path]:
    """Process a single video: download, convert, and handle size.
    
    Args:
        url: YouTube video URL
        prof: Profile configuration
        output_dir: Output directory for final files
        downloader: Downloader instance
        converter: Converter instance
        show_progress: Whether to show detailed progress bars
        skip_conversion: Skip conversion step (download only)
    
    Returns:
        List of final output file paths (may be multiple if split)
    
    Raises:
        DownloadError: If download fails
        ConversionError: If conversion fails
    """
    # Stage 0: Skip check
    history = HistoryManager()
    try:
        info_dict = downloader.extract_info(url)
        video_id = info_dict.get("id")
        
        # Check history
        if video_id and history.is_processed(video_id):
            console.print(f"[green][OK][/green] Skipping [bold]{info_dict.get('title', url)}[/bold] (Already in history)\n")
            return [converter.get_output_path(info_dict, output_dir)]

        # Check filesystem
        expected_path = converter.get_output_path(info_dict, output_dir)
        if expected_path.exists():
            console.print(f"[green][OK][/green] Skipping [bold]{expected_path.name}[/bold] (Already on disk)\n")
            if video_id:
                history.mark_completed(video_id)
            return [expected_path]
    except Exception:
        pass # If extraction fails, we'll try during download

    # Download
    if show_progress:
        console.print("[bold green]Downloading...[/bold green]")
        progress_obj, progress_hook = create_download_progress()
        with progress_obj:
            downloaded_path, info_dict = downloader.download_video(url, progress_callback=progress_hook)
        console.print(f"[green][OK][/green] Downloaded: {downloaded_path.name}\n")
    else:
        downloaded_path, info_dict = downloader.download_video(url)
    
    if skip_conversion:
        console.print("[yellow]Skipping conversion[/yellow]")
        return [downloaded_path]
    
    # Convert
    # Find thumbnail if downloaded
    thumbnail_path = None
    if downloaded_path:
        potential_thumbnail = downloaded_path.with_suffix(".jpg")
        if potential_thumbnail.exists():
            thumbnail_path = potential_thumbnail

    if show_progress:
        console.print("[bold green]Converting...[/bold green]")
        progress_obj, convert_hook = create_convert_progress()
        with progress_obj:
            converted_path = converter.convert_video(
                downloaded_path,
                output_dir=output_dir,
                progress_callback=convert_hook,
                info_dict=info_dict,
                thumbnail_path=thumbnail_path,
            )
        console.print(f"[green][OK][/green] Converted: {converted_path.name}\n")
    else:
        converted_path = converter.convert_video(
            downloaded_path, 
            output_dir=output_dir,
            info_dict=info_dict,
            thumbnail_path=thumbnail_path,
        )
    
    # Cleanup source video and thumbnail if exists
    if downloaded_path and downloaded_path.exists():
        try:
            downloaded_path.unlink()
        except Exception:
            pass

    if thumbnail_path and thumbnail_path.exists():
        try:
            thumbnail_path.unlink()
        except Exception:
            pass
    
    # Handle file size
    if show_progress:
        console.print("[bold green]Checking file size...[/bold green]")
    
    final_paths = Splitter.handle_size_exceed(
        converted_path,
        prof.output.max_file_size_gb,
        prof.output.on_size_exceed,
        output_dir,
    )
    
    # Report results
    if show_progress:
        if len(final_paths) > 1:
            console.print(f"[yellow][WARN][/yellow] File split into {len(final_paths)} parts:")
            for i, path in enumerate(final_paths, 1):
                size_mb = path.stat().st_size / 1024 / 1024
                console.print(f"  Part {i}: {path.name} ({size_mb:.1f} MB)")
        else:
            size_mb = final_paths[0].stat().st_size / 1024 / 1024
            console.print(f"[green][OK][/green] Final: {final_paths[0].name} ({size_mb:.1f} MB)")
    
    # USB Transfer
    if prof.transfer.usb_auto_copy:
        if show_progress:
            console.print("[bold green]Looking for USB drive...[/bold green]")
        
        usb_root = USBManager.find_best_drive(prof.transfer.usb_mount_path)
        if usb_root:
            if show_progress:
                console.print(f"[bold green]Copying to USB ({usb_root.drive})...[/bold green]")
            
            try:
                final_paths = USBManager.copy_to_usb(
                    final_paths,
                    usb_root,
                    prof.transfer.usb_subdir,
                    False
                )
                if show_progress:
                    console.print(f"[green][OK][/green] Copied to [bold]{usb_root}{prof.transfer.usb_subdir}[/bold]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] USB transfer failed: {e}")
        else:
            console.print("[yellow][WARN][/yellow] No USB drive found for auto-copy")

    # Record completion in history
    if info_dict and info_dict.get("id"):
        history.mark_completed(info_dict["id"])

    return final_paths


def print_header(title: str, version: str, profile_name: str, extra_info: Optional[str] = None) -> None:
    """Print standardized CLI header.
    
    Args:
        title: Title/mode name (e.g., "Batch Mode", "Playlist Mode")
        version: Application version
        profile_name: Active profile name
        extra_info: Optional additional information to display
    """
    console.print(f"[bold blue]YT2Audi v{version}{' - ' + title if title else ''}[/bold blue]")
    console.print(f"Profile: {profile_name}")
    if extra_info:
        console.print(extra_info)
    console.print()


def print_summary(total: int, succeeded: int, failed: int) -> None:
    """Print standardized batch processing summary.
    
    Args:
        total: Total number of items processed
        succeeded: Number of successful items
        failed: Number of failed items
    """
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total: {total}")
    console.print(f"  [green]Succeeded: {succeeded}[/green]")
    if failed > 0:
        console.print(f"  [red]Failed: {failed}[/red]")
