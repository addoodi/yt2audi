"""Main CLI application using Typer."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

import yt2audi
from yt2audi.config import list_available_profiles, load_profile
from yt2audi.core import Converter, Downloader, Splitter
from yt2audi.exceptions import ConversionError, DownloadError, YT2AudiError
from yt2audi.utils import configure_logging

app = typer.Typer(
    name="yt2audi",
    help="YouTube downloader and converter for Audi Q5 MMI/MIB2/3 systems",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"YT2Audi version {yt2audi.__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """YT2Audi - YouTube to Audi MMI video converter."""
    pass


@app.command()
def download(
    url: str = typer.Argument(..., help="YouTube video URL"),
    profile: str = typer.Option(
        "audi_q5_mmi",
        "--profile",
        "-p",
        help="Profile name to use",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory",
    ),
    skip_conversion: bool = typer.Option(
        False,
        "--skip-conversion",
        help="Download only, skip conversion",
    ),
) -> None:
    """Download and convert a single YouTube video.

    Example:
        yt2audi download "https://youtube.com/watch?v=..."
    """
    from yt2audi.cli.helpers import print_header, process_single_video
    
    try:
        # Load profile
        prof = load_profile(profile)
        configure_logging(prof.logging)

        print_header("", yt2audi.__version__, prof.profile.name, f"URL: {url}")

        # Initialize components
        downloader = Downloader(prof)
        converter = Converter(prof)
        output_dir = output or Path(prof.output.output_dir)

        # Process video
        final_paths = process_single_video(
            url, prof, output_dir, downloader, converter,
            show_progress=True, skip_conversion=skip_conversion
        )

        console.print("\n[bold green]Complete![/bold green]")

    except YT2AudiError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    urls_file: Path = typer.Argument(..., help="Text file with YouTube URLs (one per line)"),
    profile: str = typer.Option(
        "audi_q5_mmi",
        "--profile",
        "-p",
        help="Profile name to use",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory",
    ),
) -> None:
    """Download and convert multiple videos from a file.

    Example:
        yt2audi batch urls.txt
    """
    from yt2audi.cli.helpers import print_header, print_summary, process_single_video
    
    try:
        if not urls_file.exists():
            console.print(f"[bold red]Error:[/bold red] File not found: {urls_file}")
            raise typer.Exit(code=1)

        # Read URLs
        urls = []
        with open(urls_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

        if not urls:
            console.print("[bold red]Error:[/bold red] No URLs found in file")
            raise typer.Exit(code=1)

        # Load profile
        prof = load_profile(profile)
        configure_logging(prof.logging)

        print_header("Batch Mode", yt2audi.__version__, prof.profile.name, 
                    f"Videos to process: {len(urls)}")

        downloader = Downloader(prof)
        converter = Converter(prof)
        output_dir = output or Path(prof.output.output_dir)

        succeeded = 0
        failed = 0

        for i, url in enumerate(urls, 1):
            console.print(f"\n[bold cyan]Processing {i}/{len(urls)}:[/bold cyan] {url}")

            try:
                process_single_video(
                    url, prof, output_dir, downloader, converter, 
                    show_progress=False
                )
                console.print(f"  [green]✓[/green] Success")
                succeeded += 1

            except Exception as e:
                console.print(f"  [red]✗[/red] Failed: {e}")
                failed += 1

        print_summary(len(urls), succeeded, failed)

    except YT2AudiError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def playlist(
    url: str = typer.Argument(..., help="YouTube playlist URL"),
    profile: str = typer.Option(
        "audi_q5_mmi",
        "--profile",
        "-p",
        help="Profile name to use",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory",
    ),
) -> None:
    """Download and convert an entire YouTube playlist.

    Example:
        yt2audi playlist "https://youtube.com/playlist?list=..."
    """
    try:
        # Load profile
        prof = load_profile(profile)
        configure_logging(prof.logging)

        console.print(f"[bold blue]YT2Audi v{yt2audi.__version__} - Playlist Mode[/bold blue]")
        console.print(f"Profile: {prof.profile.name}")
        console.print(f"Playlist URL: {url}\n")

        downloader = Downloader(prof)
        converter = Converter(prof)
        output_dir = output or Path(prof.output.output_dir)

        # Download playlist
        console.print("[bold green]Downloading playlist...[/bold green]")
        downloaded_videos = downloader.download_playlist(url, output_dir=output_dir)

        console.print(f"[green][OK][/green] Downloaded {len(downloaded_videos)} videos\n")

        # Convert each video
        console.print("[bold green]Converting videos...[/bold green]")
        for i, video_path in enumerate(downloaded_videos, 1):
            console.print(f"  [{i}/{len(downloaded_videos)}] {video_path.name}")

            try:
                converted = converter.convert_video(video_path, output_dir=output_dir)
                Splitter.handle_size_exceed(
                    converted,
                    prof.output.max_file_size_gb,
                    prof.output.on_size_exceed,
                    output_dir,
                )
                console.print(f"    [green][OK][/green] Complete")
            except Exception as e:
                console.print(f"    [red][FAIL][/red] Failed: {e}")

        console.print("\n[bold green]Playlist complete![/bold green]")

    except YT2AudiError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def profiles() -> None:
    """List available profiles."""
    available = list_available_profiles()

    if not available:
        console.print("[yellow]No profiles found[/yellow]")
        return

    console.print("[bold]Available profiles:[/bold]\n")
    for name in available:
        try:
            prof = load_profile(name)
            console.print(f"  [cyan]{name}[/cyan]")
            console.print(f"    {prof.profile.description}")
        except Exception:
            console.print(f"  [cyan]{name}[/cyan]")
            console.print("    (Unable to load profile)")


if __name__ == "__main__":
    app()
