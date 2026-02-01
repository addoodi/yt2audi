"""Main CLI application using Typer."""

from pathlib import Path
from typing import Any, Optional, Annotated

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

import click
# Monkeypatch to fix Typer/Click incompatibility
# Typer calls make_metavar() without ctx, but Click 8.x requires it
_original_make_metavar = click.Parameter.make_metavar

def _patched_make_metavar(self, ctx=None):
    # If ctx is missing, try to get current context or pass safe fallback
    if ctx is None:
        ctx = click.get_current_context(silent=True)
    return _original_make_metavar(self, ctx=ctx)

click.Parameter.make_metavar = _patched_make_metavar

# Helper for manual arg parsing
def _manual_parse_args(args: list[str], value_options: set[str]) -> tuple[list[str], dict[str, Any]]:
    positional = []
    options = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("-"):
            # Handle --opt=value format
            if "=" in arg:
                opt, val = arg.split("=", 1)
                options[opt] = val
                i += 1
                continue

            # Check if this option takes a value
            takes_value = False
            for opt in value_options:
                if arg == opt:
                    takes_value = True
                    break
            
            if takes_value:
                if i + 1 < len(args) and not args[i+1].startswith("-"):
                    options[arg] = args[i+1]
                    i += 2
                else:
                    options[arg] = True # Treat as flag if value missing nearby
                    i += 1
            else:
                options[arg] = True
                i += 1
        else:
            positional.append(arg)
            i += 1
    return positional, options

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


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def download(ctx: typer.Context) -> None:
    """Download and convert a single YouTube video.

    Arguments:
        url: YouTube video URL

    Options:
        --profile, -p: Profile name to use
        --output, -o: Output directory
        --skip-conversion: Download only
    """
    value_opts = {"--profile", "-p", "--output", "-o"}
    pos_args, opts = _manual_parse_args(ctx.args, value_opts)

    if not pos_args:
        console.print("[bold red]Error:[/bold red] Missing argument 'URL'")
        raise typer.Exit(code=1)

    url = pos_args[0]
    
    profile = opts.get("--profile") or opts.get("-p") or "audi_q5_mmi"
    if profile is True: profile = "audi_q5_mmi"
    
    output = opts.get("--output") or opts.get("-o")
    if output: output = Path(str(output))
    
    skip_conversion = opts.get("--skip-conversion") is True
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


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def batch(ctx: typer.Context):
    """Download and convert multiple videos from a file.
    
    Arguments:
        urls_file: Text file with YouTube URLs (one per line)
        
    Options:
        --profile, -p: Profile name to use
        --output, -o: Output directory
    """
    # Manual parsing: value options
    value_opts = {"--profile", "-p", "--output", "-o"}
    pos_args, opts = _manual_parse_args(ctx.args, value_opts)

    if not pos_args:
        console.print("[bold red]Error:[/bold red] Missing argument 'URLS_FILE'")
        raise typer.Exit(code=1)
        
    urls_file = Path(pos_args[0])
    
    profile = opts.get("--profile") or opts.get("-p") or "audi_q5_mmi"
    if profile is True: profile = "audi_q5_mmi" # Handle case where value missing
    
    output = opts.get("--output") or opts.get("-o")
    if output: output = Path(str(output))

    from yt2audi.cli.helpers import print_header, print_summary, process_single_video


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

        from yt2audi.cli.helpers import BatchProgressManager
        from yt2audi.core import ProcessingPipeline
        import asyncio

        downloader = Downloader(prof)
        converter = Converter(prof)
        output_dir = output or Path(prof.output.output_dir)

        # Initialize pipeline
        # Use concurrency settings from app config if available, else defaults
        try:
            from yt2audi.config import load_app_config
            app_cfg = load_app_config()
            max_dl = app_cfg.app.concurrent_downloads
            max_cv = app_cfg.app.concurrent_conversions
        except Exception:
            max_dl = 2
            max_cv = 1

        pipeline = ProcessingPipeline(
            prof, 
            max_concurrent_downloads=max_dl,
            max_concurrent_conversions=max_cv
        )

        progress_manager = BatchProgressManager(console)
        
        with progress_manager:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                pipeline.run_batch(
                    urls, 
                    output_dir, 
                    progress_callback=progress_manager.get_callback()
                )
            )

        succeeded = len(results)
        failed = len(urls) - succeeded
        print_summary(len(urls), succeeded, failed)

    except YT2AudiError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def playlist(ctx: typer.Context) -> None:
    """Download and convert an entire YouTube playlist.
    
    Arguments:
        url: YouTube playlist URL

    Options:
        --profile, -p: Profile name to use
        --output, -o: Output directory
        --start: Playlist start index
        --end: Playlist end index
    """
    value_opts = {"--profile", "-p", "--output", "-o", "--start", "--end"}
    pos_args, opts = _manual_parse_args(ctx.args, value_opts)
    
    if not pos_args:
        console.print("[bold red]Error:[/bold red] Missing argument 'URL'")
        raise typer.Exit(code=1)
        
    url = pos_args[0]
    
    profile = opts.get("--profile") or opts.get("-p") or "audi_q5_mmi"
    if profile is True: profile = "audi_q5_mmi"
    
    output = opts.get("--output") or opts.get("-o")
    if output: output = Path(str(output))
    
    start = int(opts.get("--start", 1))
    end = opts.get("--end")
    if end: end = int(end)
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
        
        # Update profile with CLI overrides
        prof.download.playlist_start = start
        prof.download.playlist_end = end

        from yt2audi.cli.helpers import BatchProgressManager, print_summary
        from yt2audi.core import ProcessingPipeline
        import asyncio

        downloader = Downloader(prof)
        output_dir = output or Path(prof.output.output_dir)

        # 1. Extract URLs from playlist
        console.print("[bold green]Extracting playlist information...[/bold green]")
        urls = downloader.get_playlist_urls(url)
        
        if not urls:
            console.print("[yellow]No videos found in playlist or failed to extract info.[/yellow]")
            return

        console.print(f"[green][OK][/green] Found {len(urls)} videos\n")

        # 2. Initialize pipeline
        try:
            from yt2audi.config import load_app_config
            app_cfg = load_app_config()
            max_dl = app_cfg.app.concurrent_downloads
            max_cv = app_cfg.app.concurrent_conversions
        except Exception:
            max_dl = 2
            max_cv = 1

        pipeline = ProcessingPipeline(prof, max_dl, max_cv)
        progress_manager = BatchProgressManager(console)
        
        # 3. Process concurrently
        with progress_manager:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                pipeline.run_batch(
                    urls, 
                    output_dir, 
                    progress_callback=progress_manager.get_callback()
                )
            )

        succeeded = len(results)
        failed = len(urls) - succeeded
        print_summary(len(urls), succeeded, failed)

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
