import sys
import argparse
import logging
from .models.config import PipelineConfig
from .pipeline import Pipeline
from .renderer.pdf_compiler import open_pdf_in_viewer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    parser = argparse.ArgumentParser(description="CV Pipeline: In-Memory LaTeX Resume Tailoring Engine")
    parser.add_argument("jd_file", nargs="?", help="Path to job description text file")
    parser.add_argument("--clipboard", action="store_true", help="Read Job Description from system clipboard")
    parser.add_argument("--company", help="Target company profile name (e.g. google, amazon)")
    parser.add_argument("--no-rewrite", action="store_true", help="Disable LLM rewriting (pure ranking pass)")
    parser.add_argument("--no-pdf", action="store_true", help="Disable PDF compilation (output LaTeX only)")
    parser.add_argument("--ats", action="store_true", help="Display ATS match report")
    parser.add_argument("--diff", action="store_true", help="Display resume diff report")
    parser.add_argument("--manifest", action="store_true", help="Display reproducibility manifest")
    parser.add_argument("--copy", action="store_true", help="Copy generated LaTeX code to system clipboard")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug trace logging")

    args = parser.parse_args()

    # Get Job Description text
    jd_text = ""
    if args.clipboard:
        try:
            import pyperclip
            jd_text = pyperclip.paste()
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            sys.exit(1)
    elif args.jd_file:
        try:
            with open(args.jd_file, "r", encoding="utf-8") as f:
                jd_text = f.read()
        except Exception as e:
            print(f"Error reading JD file '{args.jd_file}': {e}")
            sys.exit(1)
    else:
        print("Please provide a job description file path or use --clipboard.")
        parser.print_help()
        sys.exit(1)

    # Load configuration & apply CLI overrides
    config = PipelineConfig.load_from_yaml()
    if args.no_rewrite:
        config.rewriter.enabled = False
    if args.no_pdf:
        config.output.compile_pdf = False
    if args.debug:
        config.debug = True
        config.output.debug = True

    # Configure logging based on debug flag
    is_debug = config.debug or config.output.debug
    if not is_debug:
        logging.getLogger().setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # Execute pipeline
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.style import Style

    console = Console()
    console.print("\n[bold cyan][*] CV Pipeline:[/] [dim]In-Memory LaTeX Resume Tailoring Engine[/dim]\n")

    result = None
    with Progress(
        SpinnerColumn("dots", style="bold magenta"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(bar_width=30, complete_style="cyan", finished_style="green"),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Parsing Job Description & Matching Skills...", total=100)
        
        pipeline = Pipeline(config=config)
        progress.update(task, advance=30, description="Ranking Experiences & Filtering Keywords...")
        
        result = pipeline.run(jd_text=jd_text, company_profile_name=args.company)
        progress.update(task, advance=70, description="Generating Resume & Formatting LaTeX...")

    console.print(Panel("[bold green][+] Resume Tailoring Complete![/bold green]", border_style="green"))

    # Output Reports if requested or configured
    if args.ats or config.output.show_ats_report:
        console.print("\n" + result.ats_report + "\n")

    if args.diff or config.output.show_diff:
        console.print("\n" + result.diff_report + "\n")

    if args.manifest or config.output.show_manifest:
        console.print("\n" + result.manifest + "\n")

    # Copy to clipboard if explicitly requested via flag or config
    should_copy_clipboard = args.copy or config.output.copy_to_clipboard
    if should_copy_clipboard:
        try:
            import pyperclip
            pyperclip.copy(result.latex_string)
            console.print("\n[bold green][+] LaTeX code copied to clipboard![/bold green]")
        except Exception:
            pass

    # Print raw LaTeX only if debug mode is active or explicitly requested via --copy
    if is_debug or args.copy:
        console.print("\n[bold yellow][+] GENERATED LATEX CODE:[bold yellow]")
        print("=" * 60)
        print(result.latex_string)
        print("=" * 60)

    # Open PDF in default viewer if compiled
    if result.pdf_bytes and config.output.open_pdf:
        console.print("[bold cyan][+] Ephemeral PDF compiled! Opening in system PDF viewer...[/bold cyan]")
        open_pdf_in_viewer(result.pdf_bytes)


if __name__ == "__main__":
    main()
