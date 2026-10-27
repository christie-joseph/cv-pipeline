# CV Resume Tailoring Pipeline

An **ephemeral, in-memory, deterministic resume generator** that automatically tailors your resume for any Job Description (JD).

---

## 📌 Quick Overview of the Solution

### What Is This Tool?
The **CV Resume Tailoring Pipeline** is an intelligent, automated tool that takes any job description (from a file or your clipboard) and compares it against your master career history. It automatically selects your most relevant job experiences, chooses your strongest bullet points using AI vector search, rewrites action verbs to match the target job, and generates a professional, tailored resume in seconds.

### Why Was It Built?
Instead of manually tweaking your resume for every single job application or cluttering your computer with dozens of slightly different `.pdf` files, this tool maintains a single **"Source of Truth"** for your career history (`data/experiences/`).

### Key Highlights
- **Zero Disk Clutter & Markdown Export**: Generated resumes exist strictly in computer memory by default. Optionally export clean, version-controllable Markdown (`--format markdown` or `--format all`) to `output/resume_tailored.md`.
- **100% Offline-First Architecture**: Run completely disconnected with `--offline`. Bypasses all cloud networks, uses deterministic rule rewriting, and safeguards local execution with zero latency or token usage.
- **Cliché & Buzzword Detection**: Built-in AST-style lexical analyzer detects weak responsibility preambles ("responsible for", "helped with"), empty corporate buzzwords ("rockstar", "synergy", "spearheaded"), and provides instant ATS score penalties and actionable Quick Wins.
- **Token-Dense Machine Rewriter Protocol**: Communicates with LLMs using a compact JSON format (`{"kw": [...], "b": [...]}` $\to$ `{"out": [...]}`), saving ~70% token overhead, combined with selective pre-filtering that skips bullets that already hit keyword and metric criteria.
- **Length-Calibrated RapidFuzz Matching**: Skill extraction utilizes length-calibrated Damerau-Levenshtein distance gating ($\le 1$ edit for terms $\le 6$ chars; $\le 2$ edits for terms $> 6$ chars) to prevent false positives without memory-heavy BK-trees.
- **Timeline Integrity**: Automatically keeps your job history in exact chronological order without creating artificial employment gaps.
- **Smart 3-Tier AI Stack with Priority Failover**: Uses a free multi-cloud AI pool (**1st OpenRouter $\rightarrow$ 2nd Gemini $\rightarrow$ 3rd Cerebras $\rightarrow$ 4th Groq**), with automated fallback to local Ollama AI or deterministic Python rules.
- **Custom API Key Support**: Add your own custom API key with top priority (`CUSTOM_API_KEY`).
- **Instant Audit Reports**: Displays your ATS match score, matched vs missing skills, cliché warnings, selected vs excluded bullet points, and a digital fingerprint receipt for 100% reproducibility.

---

## 🔒 Public vs Private Repository Architecture & Dual-Branch Sync

This solution supports a **clean separation between public source code and private career credentials**:

```text
CV pipeline/
├── data/
│   ├── contact.yaml               # Neutral public template (Alex Morgan)
│   ├── education.yaml             # Neutral public university history
│   ├── projects.yaml              # Neutral public engineering projects
│   ├── skills.yaml                # Standardized skills taxonomy
│   └── experiences/
│       ├── cloud_infrastructure.yaml # Public sample domain data
│       ├── fintech_backend.yaml
│       ├── web_platform.yaml
│       ├── data_engineering.yaml
│       ├── early_career.yaml
│       └── personal/              # [GIT-IGNORED] Put your real career YAMLs here!
│           ├── my_company_1.yaml
│           └── my_company_2.yaml
├── jobs/
│   └── benchmarks/                # 6 Calibrated multi-domain test benchmarks
│       ├── 01_backend_distributed.txt
│       ├── 02_fintech_payments.txt
│       ├── 03_data_streaming.txt
│       ├── 04_web_fullstack.txt
│       ├── 05_early_career_generalist.txt
│       └── 06_marketing_irrelevant.txt
├── .env.example                   # Public template environment file
├── .env                           # [GIT-IGNORED] Private API keys
└── .gitattributes                 # Protects private config during git merges
```

### 1. The Git-Ignored Personal Overlay (Single Repository Method)
If `data/experiences/personal/` (or `data/contact/personal/`, etc.) exists on your machine, the pipeline **automatically loads your real personal career data** instead of the public sample files. Because `personal/` subdirectories and `.env` are listed in `.gitignore`, your private career data and API keys will **never be committed to GitHub**.

### 2. Dual Branching Strategy (Public vs Private Branch Sync)
If you manage two Git branches (`public` for open-source sharing and `private` for your personal use):

#### Setting up the `private` branch:
```bash
# 1. Create a private branch from public
git checkout -b private

# 2. Add your personal experiences to data/experiences/personal/
# 3. Create your local .env file with your API keys
```

#### Syncing logic updates from `public` to `private`:
When algorithm or code logic updates are committed to the `public` branch, sync them to `private` without touching your personal data:

```bash
# 1. Switch to your private branch
git checkout private

# 2. Merge public code updates cleanly
git merge public
```

---

## 📁 Complete Personalization Map (Where to Update Your Information)

To personalize this solution completely for your own career applications, update the YAML files listed below. 

> [!TIP]
> **Privacy First**: Put your personal files inside `data/<category>/personal/` (e.g. `data/contact/personal/contact.yaml`). The system automatically prefers personal files when they exist and ignores them from Git!

| Category | Location | File Name | Description & Required Fields |
| :--- | :--- | :--- | :--- |
| **Contact Info** | `data/contact/personal/` | `contact.yaml` | Candidate `name` & `email` (required); `phone`, `linkedin`, `github`, `location` (optional). |
| **Education** | `data/education/personal/` | `education.yaml` | `institution`, `degree`, `location`, `dates` (graduation year extracted automatically). |
| **Work History** | `data/experiences/personal/` | `role1.yaml`, `role2.yaml` | Source of truth experiences: `company`, `start`, `end`, `importance`, `titles`, `bullets`, `tags`. |
| **Projects** | `data/projects/personal/` | `projects.yaml` | Personal projects: `id`, `title`, `tech_stack`, `bullets` (no dates required). |
| **Skills Taxonomy** | `data/` | `skills.yaml` | Taxonomy mapping skills into 5 categories: `Languages`, `Frameworks`, `Cloud`, `Databases`, `Technologies`. |
| **API Keys** | `./` (Root directory) | `.env` | Free LLM API keys (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `CEREBRAS_API_KEY`, `GROQ_API_KEY`, or `CUSTOM_API_KEY`). |

---

### Detailed File Templates for Personalization

#### 1. Contact Information (`data/contact/personal/contact.yaml` or `data/contact.yaml`)
```yaml
name: "Alex Morgan"
email: "alex.morgan@example.com"
linkedin: "linkedin.com/in/alexmorgan"      # Optional
github: "github.com/alexmorgan"            # Optional
phone: "+1 (555) 019-2834"                 # Optional
location: "San Francisco, CA"              # Optional
```

#### 2. Education History (`data/education/personal/education.yaml` or `data/education.yaml`)
```yaml
education:
  - institution: "Tech State University"
    location: "San Francisco, CA"
    degree: "B.S. in Computer Science"
    dates: "2018 - 2022"                    # Graduation year is extracted automatically
```

#### 3. Personal Work Experience (`data/experiences/personal/role.yaml`)
```yaml
id: "cloud_infrastructure"
company: "Apex Cloud Systems"
start: "2023"
end: "Present"                              # "Present" ensures this position sits at the top
importance: 10                             # Priority rating (1 to 10)
optional: false                            # Set true if this job can be omitted when space is tight

tags:
  - "distributed-systems"
  - "cloud"
  - "kubernetes"
  - "golang"
  - "python"

titles:
  default: "Senior Systems Engineer"
  variants:
    - "Cloud Platform Engineer"
    - "Infrastructure Engineer"

bullets:
  - id: "apex_infra_b1"
    text: "Architected a multi-region Kubernetes control plane managing 120+ microservices with 99.99% service availability."
    tags: ["kubernetes", "cloud", "distributed-systems"]
  - id: "apex_infra_b2"
    text: "Engineered distributed tracing infrastructure across Go and Python backend services, reducing p99 tail latency by 42%."
    tags: ["golang", "python", "observability"]
```

#### 4. Personal Projects (`data/projects/personal/projects.yaml` or `data/projects.yaml`)
```yaml
projects:
  - id: "distributed_kv_store"
    title: "Distributed KV Store"
    tech_stack: ["Go", "Raft", "gRPC", "Docker"]
    bullets:
      - "Implemented a Raft-based distributed key-value store with consensus replication and leader election."
      - "Benchmarked throughput achieving 15,000 write ops/sec across 5 replicated nodes with sub-10ms commit latency."
```

#### 5. Technical Skills Taxonomy (`data/skills.yaml`)
```yaml
skills:
  # Languages: Python, Go, C#, Java, TypeScript, SQL, Bash
  - id: python
    display: "Python"
    aliases: ["python", "py", "python3"]
    category: "Languages"

  # Frameworks: FastAPI, Django, React, ASP.NET Core
  - id: fastapi
    display: "FastAPI"
    aliases: ["fastapi", "fast-api"]
    category: "Frameworks"

  # Cloud: AWS, GCP, Azure, Kubernetes, Terraform
  - id: kubernetes
    display: "Kubernetes"
    aliases: ["kubernetes", "k8s"]
    category: "Cloud"

  # Databases: PostgreSQL, Redis, MongoDB, Cassandra
  - id: postgresql
    display: "PostgreSQL"
    aliases: ["postgresql", "postgres", "psql"]
    category: "Databases"

  # Technologies: Docker, CI/CD, Kafka, gRPC, Distributed Systems
  - id: kafka
    display: "Apache Kafka"
    aliases: ["kafka", "apache kafka"]
    category: "Technologies"
```

#### 6. API Environment File (`.env`)
```env
# Standard Cloud Provider Keys (Free tiers available):
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
CEREBRAS_API_KEY=your_cerebras_key
GROQ_API_KEY=your_groq_key

# Optional Custom API Key (Auto-registers as Priority 0 / Top Priority):
CUSTOM_API_KEY=your_custom_api_key
CUSTOM_API_URL=https://api.openai.com/v1
CUSTOM_API_MODEL=gpt-4o-mini
```

---

## 🚀 First-Time Setup Guide (Step-by-Step for Non-Tech Users)

Follow these simple steps to set up and run the pipeline on your computer in under 5 minutes. No prior programming experience required!

### Step 1: Install Python
1. Download Python **3.11**, **3.12**, or **3.13** from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer. 
3. **CRITICAL**: On the very first installer screen, check the box that says **"Add python.exe to PATH"** before clicking Install.

---

### Step 2: Open Terminal / Command Prompt in the Project Folder
1. Open the project folder (`CV pipeline`) on your computer.
2. **On Windows**: Click on the folder address bar at the top of File Explorer, type `cmd` or `powershell`, and press **Enter**.
3. **On macOS / Linux**: Open Terminal and `cd` into the project directory.

---

### Step 3: Install Required Packages (One-Time Setup)
Copy and paste these two commands into your terminal, pressing **Enter** after each:

```bash
# Command 1: Install required software packages
pip install -r requirements.txt

# Command 2: Download the English language parser
python -m spacy download en_core_web_sm
```

---

### Step 4: Add Free AI Keys & Custom Provider (Optional)
The pipeline automatically tries your API keys in order of priority:
**1st OpenRouter $\rightarrow$ 2nd Gemini $\rightarrow$ 3rd Cerebras $\rightarrow$ 4th Groq**

1. Create a simple text file named `.env` in the main project folder.
2. Open `.env` in Notepad or VS Code and add any free API keys you have:

```env
# Standard Cloud API Keys:
OPENROUTER_API_KEY=your_openrouter_key_here
GEMINI_API_KEY=your_free_gemini_key_here
CEREBRAS_API_KEY=your_cerebras_key_here
GROQ_API_KEY=your_free_groq_key_here

# Optional: Custom API Key (Takes top priority automatically!)
CUSTOM_API_KEY=your_custom_key_here
CUSTOM_API_URL=https://api.openai.com/v1
CUSTOM_API_MODEL=gpt-4o-mini
```

> [!NOTE]
> **No API key? Working offline?** No problem! With `--offline` (or an empty `.env`), the system automatically executes Tier C (built-in Python rules) to tailor your resume without needing any internet connection or cloud API keys.

---

### Step 5: Run Your Very First Resume Tailoring Command!

Run this command in your terminal using the built-in benchmark:

```bash
python -m src jobs/benchmarks/01_backend_distributed.txt --ats
```

**What will happen**:
1. The tool reads the benchmark job description.
2. It analyzes the work history in `data/experiences/`.
3. It prints a detailed **ATS Match Score Report** directly on your terminal screen, including cliché warnings and quick wins.
4. It outputs your tailored resume code.
5. If a PDF compiler (`pdflatex` / `tectonic`) is installed, it opens a PDF preview automatically!

---

## ⚡ Daily Usage Guide & Shortcut Flags

Once setup is complete, here is how you can use the tool for your job applications:

### 1. Tailor from a Job Description File
Save a job description into a text file and run:
```bash
python -m src jobs/benchmarks/01_backend_distributed.txt
```

### 2. Read Directly from Clipboard (Ctrl+C / Cmd+C)
Copy any job posting text from LinkedIn or Indeed and run:
```bash
python -m src --clipboard
```

### 3. Run in 100% Offline Mode
Run with zero network calls, instantly falling back to local deterministic rule rewriting:
```bash
python -m src jobs/benchmarks/01_backend_distributed.txt --offline
```

### 4. Export Clean Markdown
Generate clean Markdown to `output/resume_tailored.md` alongside or instead of PDF:
```bash
# Export Markdown only
python -m src jobs/benchmarks/01_backend_distributed.txt --format markdown

# Export both PDF and Markdown
python -m src jobs/benchmarks/01_backend_distributed.txt --format all
```

### 5. Display Audit Reports
Add flags to view audit reports on screen:
```bash
# Show ATS Match Score & Cliché / Buzzword Warnings
python -m src jobs/benchmarks/01_backend_distributed.txt --ats

# Show Resume Diff (Selected vs Excluded jobs and bullets)
python -m src jobs/benchmarks/01_backend_distributed.txt --diff

# Show Reproducibility Manifest (Digital Fingerprint)
python -m src jobs/benchmarks/01_backend_distributed.txt --manifest

# Show ALL 3 Reports at once:
python -m src jobs/benchmarks/01_backend_distributed.txt --ats --diff --manifest
```

### 6. Copy LaTeX Code directly to Clipboard
Copy the raw LaTeX code to paste into [Overleaf](https://www.overleaf.com):
```bash
python -m src jobs/benchmarks/01_backend_distributed.txt --copy --no-pdf
```

---

## 📊 Benchmark Suite (`jobs/benchmarks/`)

The repository includes 6 calibrated benchmark job descriptions to validate accuracy across different engineering verticals and test negative control rejection:

| Benchmark File | Target Vertical | Target Skills / Focus | Expected Score Range |
| :--- | :--- | :--- | :--- |
| `01_backend_distributed.txt` | Distributed Systems / Backend | Go, Kubernetes, gRPC, Distributed Systems | 75% – 95% |
| `02_fintech_payments.txt` | FinTech Backend / Payments | Java, Spring Boot, PostgreSQL, Kafka | 70% – 90% |
| `03_data_streaming.txt` | Data Engineering / ETL | Python, Spark, Kafka, Airflow | 70% – 90% |
| `04_web_fullstack.txt` | Web Platform / Fullstack | TypeScript, React, Node.js, GraphQL | 70% – 90% |
| `05_early_career_generalist.txt`| Junior / Early Career SWE | Python, SQL, Git, REST APIs | 60% – 80% |
| `06_marketing_irrelevant.txt` | Marketing (Negative Control) | SEO, Google Ads, Copywriting, Social Media | **< 15%** (Rejection) |

---

## 🔬 Core Functionalities & Technical Architecture

### 1. Source of Truth Work History (`data/experiences/*.yaml`)
Your work history is stored in readable YAML text files under `data/experiences/`. Each job includes:
- `company`, `start`, `end`: Chronological employment metadata.
- `importance`: Priority rating (1 to 10).
- `optional`: Boolean flag (`true` / `false`) allowing older tail jobs to be omitted if space is constrained while preserving timeline continuity.

### 2. Smart Hybrid Job Description Parser (`src/parser/jd_parser.py`)
Combines 3 text analysis techniques:
1. **YAKE Statistical Keyphrase Extraction**: Identifies key industry terms.
2. **spaCy Grammar & Entity Recognition**: Extracts company names, product terms, and precisely classifies job seniority (e.g., `Principal`, `Senior`, `Mid-Level/SWE`, `Junior`).
3. **FastEmbed Semantic Vector Search**: Computes vector embeddings to discover conceptual job requirements. In `--offline` mode, safely bypasses external model calls.

### 3. Length-Calibrated Fuzzy Skill Matcher (`src/ranker/skill_matcher.py`)
Matches candidate skills against JD requirements across 4 progressive passes:
1. Exact lowercase matching.
2. Alias & synonym normalization.
3. Substring & word boundary matching.
4. **Length-Calibrated Levenshtein distance**: Gated strictly to $\le 1$ edit for short terms ($\le 6$ characters) and $\le 2$ edits for longer terms ($> 6$ characters), eliminating false positives without the runtime memory overhead of BK-trees.

### 4. Cliché & Overused Phrase Detector (`src/ranker/cliche_detector.py`)
Scans resume bullets against 3 categories of weak phrasing:
- **Weak Responsibility Preambles**: *"Responsible for"*, *"Duties included"*, *"Helped with"*.
- **Empty Corporate Buzzwords**: *"Rockstar"*, *"Ninja"*, *"Synergy"*, *"Spearheaded"*, *"Thought leadership"*.
- **Vague / Passive Action Verbs**: *"Handled"*, *"Worked on"*, *"Assisted"*.
Flags occurrences in the ATS report, applies a quality penalty to the ATS score, and suggests strong active replacements.

### 5. Maximal Marginal Relevance (MMR) Bullet Selection (`src/ranker/bullet_ranker.py`)
Balances **Relevance** (how well a bullet matches the job description) against **Diversity** (preventing multiple bullet points from repeating the exact same topic).

### 6. Token-Dense 3-Tier Multi-Provider Rewriter Stack (`src/rewriter/`)
- **Selective Pre-filter**: Before invoking an LLM, the system checks whether the existing bullet already contains JD keywords and quantified metrics. High-scoring bullets bypass rewriting entirely, eliminating unnecessary API cost and latency.
- **Machine-Optimized Payload**: Rewriter requests and responses use a dense, compact JSON protocol (`{"kw": [...], "b": [...]}` $\to$ `{"out": [...]}`), cutting prompt token overhead by ~70%.
- **Tier A (Cloud LLM Pool)**: Tries providers by priority: **1st OpenRouter $\rightarrow$ 2nd Gemini $\rightarrow$ 3rd Cerebras $\rightarrow$ 4th Groq** (or top-priority `CUSTOM_API_KEY`). If one provider hits a rate limit or connection error, it automatically fails over to the next.
- **Tier B (Local Ollama GPU/CPU)**: Runs local model (`qwen2.5:1.5b`) if cloud APIs are unavailable.
- **Tier C (Python Rule Engine)**: Zero-latency deterministic rule engine that strengthens action verbs offline.
- **Strict Anti-Hallucination Guardrails**: Before any AI rewritten bullet is accepted, it must pass a strict Python validation layer that guarantees **100% Metric Retention** (no dropped/altered numbers or percentages) and **Length Bounding** (blocks overly verbose hallucinated paragraphs).

---

## 🧪 Running Automated Unit Tests (`pytest`)

To verify that all system components, vector calculations, cliché detectors, token efficiency filters, and timeline rules are working correctly, run:

```bash
# Run full automated test suite (62 tests)
python -m pytest tests/ -v
```

**Expected Result**: All 62 unit & integration tests pass cleanly:
- `test_jd_parser.py`: Multi-keyword extraction, seniority classification, and deduplication.
- `test_matcher.py`: 4-pass skill matching and length-calibrated fuzzy distance.
- `test_cliche_detector.py`: Weak preamble detection, buzzword warnings, and penalty scoring.
- `test_timeline.py`: Chronological integrity and gap detection.
- `test_bullet_ranker.py`: MMR relevance vs diversity scoring.
- `test_rewriter.py`: Multi-provider failover, metric retention, and guardrails.
- `test_token_efficiency.py`: Compact JSON protocol and selective rewrite skipping.
- `test_offline_mode.py`: 100% offline flag and deterministic rule fallback.
- `test_dummy_data.py`: Integrity and neutrality of sample YAMLs.
- `test_benchmark_matrix.py`: Evaluation across the 6 benchmark JDs and negative control rejection.

---

## 🛠️ Troubleshooting & Frequently Asked Questions

### 1. `ModuleNotFoundError: No module named 'src'`
- **Fix**: Make sure your terminal is opened in the main project directory (`CV pipeline`), and use `python -m src ...` instead of `python src/__main__.py`.

### 2. `Can't find model 'en_core_web_sm'`
- **Fix**: Run `python -m spacy download en_core_web_sm` in your terminal.

### 3. `No local LaTeX compiler found`
- **Fix**: You have two easy options:
  - Export Markdown directly: `python -m src jobs/benchmarks/01_backend_distributed.txt --format markdown` (saved to `output/resume_tailored.md`).
  - Or copy raw LaTeX to clipboard: `python -m src jobs/benchmarks/01_backend_distributed.txt --copy --no-pdf` and paste into [Overleaf.com](https://www.overleaf.com).

### 4. Running completely offline / on airplane mode
- **Fix**: Simply pass the `--offline` flag: `python -m src jobs/benchmarks/01_backend_distributed.txt --offline`. The pipeline executes entirely on your local machine with zero external network dependencies.

---

## ⚙️ Configuration Reference (`config.yaml`)

Edit `config.yaml` to adjust pipeline settings or customize provider priorities:

```yaml
max_experiences: 3              # Maximum number of job experiences to include
max_bullets_per_experience: 3   # Maximum bullets per job experience
minimum_similarity: 0.25        # Similarity score floor for experience selection
mmr_lambda: 0.7                 # MMR balance (1.0 = pure relevance, 0.0 = pure diversity)

weights:
  tfidf: 0.35
  embedding: 0.30
  skill_overlap: 0.20
  importance: 0.10
  company_boost: 0.05

rewriter:
  enabled: true
  ollama_model: "qwen2.5:1.5b"
  ollama_timeout: 30

  # Priority stack: lower priority number = higher priority
  providers:
    - name: "openrouter"
      api_url: "https://openrouter.ai/api/v1"
      api_model: "meta-llama/llama-3.3-70b-instruct:free"
      api_key_env: "OPENROUTER_API_KEY"
      priority: 1

    - name: "gemini"
      api_url: "https://generativelanguage.googleapis.com/v1beta/openai"
      api_model: "gemini-2.5-flash"
      api_key_env: "GEMINI_API_KEY"
      priority: 2

    - name: "cerebras"
      api_url: "https://api.cerebras.ai/v1"
      api_model: "llama3.1-8b"
      api_key_env: "CEREBRAS_API_KEY"
      priority: 3

    - name: "groq"
      api_url: "https://api.groq.com/openai/v1"
      api_model: "llama-3.3-70b-versatile"
      api_key_env: "GROQ_API_KEY"
      priority: 4

output:
  compile_pdf: true
  open_pdf: true
  show_ats_report: true
  show_diff: true
  show_manifest: true
  copy_to_clipboard: false
```

---

## 📖 Additional Developer Documentation
For in-depth educational breakdowns of Python code logic, Pydantic schemas, and package details, see [WIKI_README.md](file:///d:/PROJECTS/CV%20pipeline/WIKI_README.md).
