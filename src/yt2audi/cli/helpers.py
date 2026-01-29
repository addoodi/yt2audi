"""Helper functions for CLI to reduce code duplication."""

from pathlib import Path
from typing import Callable, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from yt2audi.core import Converter, Downloader, Splitter
from yt2audi.models.profile import Profile

console = Console()


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
    # Download
    if show_progress:
        console.print("[bold green]Downloading...[/bold green]")
        progress_obj, progress_hook = create_download_progress()
        with progress_obj:
            downloaded_path = downloader.download_video(url, progress_callback=progress_hook)
        console.print(f"[green]✓[/green] Downloaded: {downloaded_path.name}\n")
    else:
        downloaded_path = downloader.download_video(url)
    
    if skip_conversion:
        console.print("[yellow]Skipping conversion[/yellow]")
        return [downloaded_path]
    
    # Convert
    if show_progress:
        console.print("[bold green]Converting...[/bold green]")
        progress_obj, convert_hook = create_convert_progress()
        with progress_obj:
            converted_path = converter.convert_video(
                downloaded_path,
                output_dir=output_dir,
                progress_callback=convert_hook,
            )
        console.print(f"[green]✓[/green] Converted: {converted_path.name}\n")
    else:
        converted_path = converter.convert_video(downloaded_path, output_dir=output_dir)
    
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
            console.print(f"[yellow]⚠[/yellow] File split into {len(final_paths)} parts:")
            for i, path in enumerate(final_paths, 1):
                size_mb = path.stat().st_size / 1024 / 1024
                console.print(f"  Part {i}: {path.name} ({size_mb:.1f} MB)")
        else:
            size_mb = final_paths[0].stat().st_size / 1024 / 1024
            console.print(f"[green]✓[/green] Final: {final_paths[0].name} ({size_mb:.1f} MB)")
    
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
