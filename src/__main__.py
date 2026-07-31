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

    # Execute pipeline
    print("\n[+] Executing CV Resume Tailoring Pipeline...\n")
    pipeline = Pipeline(config=config)
    result = pipeline.run(jd_text=jd_text, company_profile_name=args.company)

    # Output Reports if requested or configured
    if args.ats or config.output.show_ats_report:
        print("\n" + result.ats_report + "\n")

    if args.diff or config.output.show_diff:
        print("\n" + result.diff_report + "\n")

    if args.manifest or config.output.show_manifest:
        print("\n" + result.manifest + "\n")

    # Output LaTeX string
    print("=" * 60)
    print("GENERATED LATEX CODE (Raw String Output):")
    print("=" * 60)
    print(result.latex_string)
    print("=" * 60)

    # Copy to clipboard if requested
    if args.copy or config.output.copy_to_clipboard:
        try:
            import pyperclip
            pyperclip.copy(result.latex_string)
            print("[+] LaTeX code copied to clipboard!")
        except Exception:
            pass

    # Open PDF in default viewer if compiled
    if result.pdf_bytes and config.output.open_pdf:
        print("[+] Ephemeral PDF compiled! Opening in system PDF viewer...")
        open_pdf_in_viewer(result.pdf_bytes)


if __name__ == "__main__":
    main()
