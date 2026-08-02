# CV Resume Tailoring Pipeline

An **ephemeral, in-memory, deterministic resume generator** that automatically tailors your resume for any Job Description (JD).

---

## 📌 Quick Overview of the Solution

### What Is This Tool?
The **CV Resume Tailoring Pipeline** is a smart, automated tool that takes a job description (from a text file or your clipboard) and compares it against your master work history. It automatically selects your most relevant job experiences, chooses your strongest bullet points using AI vector search, rewrites action verbs to match the target job, and generates a professional, tailored resume in seconds.

### Why Was It Built?
Instead of manually tweaking your resume for every single job application or cluttering your computer with dozens of slightly different `.pdf` files, this tool maintains a single **"Source of Truth"** for your career history (`data/experiences/`). 

### Key Highlights
- **Zero Disk Clutter**: Generated resumes exist only in computer memory. Custom files are **never saved to disk**.
- **Timeline Integrity**: Automatically keeps your job history in exact chronological order without creating artificial employment gaps.
- **Smart 3-Tier AI Stack with Priority Failover**: Uses a free multi-cloud AI pool (**1st OpenRouter $\rightarrow$ 2nd Gemini $\rightarrow$ 3rd Cerebras $\rightarrow$ 4th Groq**), with automated fallback to local Ollama AI or deterministic Python rules.
- **Custom API Key Support**: Add your own custom API key with top priority (`CUSTOM_API_KEY`).
- **Instant Audit Reports**: Displays your ATS match score, matched vs missing skills, selected vs excluded bullet points, and a digital fingerprint receipt for 100% reproducibility.

---

## 🔒 Public vs Private Repository Architecture & Dual-Branch Sync

This solution supports a **clean separation between public source code and private career credentials**:

```text
CV pipeline/
├── data/
│   └── experiences/
│       ├── amazon.yaml            # Public sample data for demo
│       ├── research.yaml
│       └── personal/              # [GIT-IGNORED] Put your real YAMLs here!
│           ├── my_company_1.yaml
│           └── my_company_2.yaml
├── .env.example                   # Public template environment file
├── .env                           # [GIT-IGNORED] Private API keys
└── .gitattributes                 # Protects private config during git merges
```

### 1. The Git-Ignored Personal Overlay (Single Repository Method)
If `data/experiences/personal/` exists on your machine, the pipeline **automatically loads your real personal career data** from `personal/` instead of the public sample files. Because `data/experiences/personal/` and `.env` are listed in `.gitignore`, your private career data and API keys will **never be committed to GitHub**.

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

#### 1. Contact Information (`data/contact/personal/contact.yaml`)
```yaml
name: "Candidate Full Name"
email: "your.email@example.com"
linkedin: "linkedin.com/in/yourprofile"    # Optional
github: "github.com/yourusername"          # Optional
phone: "+44 7000 000000"                  # Optional
location: "City, Country"                 # Optional
```

#### 2. Education History (`data/education/personal/education.yaml`)
```yaml
education:
  - institution: "University of Birmingham"
    location: "Birmingham, UK"
    degree: "MSc Advanced Computer Science"
    dates: "Sept 2022"                      # Graduation year (e.g., 2022) is extracted automatically

  - institution: "Mar Athanasius College of Engineering"
    location: "Kerala, India"
    degree: "BTech Computer Science and Engineering"
    dates: "Aug 2020"                       # Graduation year (e.g., 2020) is extracted automatically
```

#### 3. Personal Work Experience (`data/experiences/personal/fsp_cloud_backend.yaml`)
```yaml
id: "fsp_cloud_backend"
company: "FSP"
start: "2026"
end: "Present"                              # "Present" ensures this position sits at the top
importance: 10                             # Priority rating (1 to 10)
optional: false                            # Set true if this job can be omitted when space is tight

tags:
  - "csharp"
  - "dotnet"
  - "azure"
  - "distributed-systems"

titles:
  default: "Associate Developer - Cloud & Backend"
  variants:
    - "Cloud & Backend Engineer"
    - "Senior Backend Engineer"

bullets:
  - id: "fsp_cb_b1"
    text: "Engineered a fault-tolerant asynchronous integration layer by migrating synchronous endpoints to serverless computing and distributed message queues."
    tags: ["azure", "serverless", "distributed-systems"]
```

#### 4. Personal Projects (`data/projects/personal/projects.yaml`)
```yaml
projects:
  - id: "gitlytics"
    title: "Gitlytics"
    tech_stack: ["Python", "Flask", "React", "PostgreSQL", "Docker"]
    bullets:
      - "Developed a full-stack web application using Flask serving a REST API with React as frontend."
      - "Implemented GitHub OAuth to retrieve data from user repositories."

  - id: "simple_paintball"
    title: "Simple Paintball"
    tech_stack: ["Spigot API", "Java", "Maven", "Git"]
    bullets:
      - "Developed a Minecraft server plugin published to websites gaining 2K+ downloads."
```

#### 5. Technical Skills Taxonomy (`data/skills.yaml`)
```yaml
skills:
  # Languages: C#, Java, Python, TypeScript, JavaScript, C++, SQL, Bash, HTML/CSS
  - id: csharp
    display: "C#"
    aliases: ["c#", "csharp", ".net", "dotnet"]
    category: "Languages"

  # Frameworks: .NET / ASP.NET Core, React, Blazor, Entity Framework
  - id: dotnet_aspnet
    display: ".NET / ASP.NET Core"
    aliases: [".net", "asp.net core", ".net core"]
    category: "Frameworks"

  # Cloud: Azure, AWS, DigitalOcean
  - id: azure
    display: "Azure"
    aliases: ["azure", "microsoft azure"]
    category: "Cloud"

  # Databases: SQL Server, PostgreSQL, MongoDB, Redis, BigQuery, Firestore / Firebase
  - id: sql_server
    display: "SQL Server"
    aliases: ["sql server", "ms sql", "mssql"]
    category: "Databases"

  # Technologies: Docker, Kubernetes, Azure DevOps, GitHub Actions, Git, Bicep, ARM Templates, REST APIs, Microservices, Event-Driven Architecture
  - id: docker
    display: "Docker"
    aliases: ["docker", "containerization"]
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
1. Download Python **3.11** or **3.12** from [python.org/downloads](https://www.python.org/downloads/).
2. Run the installer. 
3. **CRITICAL**: On the very first installer screen, check the box that says **"Add python.exe to PATH"** before clicking Install.

---

### Step 2: Open Terminal / Command Prompt in the Project Folder
1. Open the project folder (`CV pipeline`) on your computer.
2. **On Windows**: Click on the folder address bar at the top of File Explorer, type `cmd`, and press **Enter**.
3. **On macOS**: Right-click inside the project folder and select **Open in Terminal**.

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
2. Open `.env` in Notepad or TextEdit and add any free API keys you have:

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
> **Don't have an API key?** No problem! If you leave `.env` empty, the system automatically uses Tier C (built-in Python rules) to tailor your resume without needing any internet connection or API keys.

---

### Step 5: Run Your Very First Resume Tailoring Command!

Run this command in your terminal:

```bash
python -m src jobs/google_backend.txt --ats
```

**What will happen**:
1. The tool reads the sample job description (`jobs/google_backend.txt`).
2. It analyzes your work history in `data/experiences/`.
3. It prints an **ATS Match Score Report** directly on your terminal screen.
4. It outputs your tailored raw LaTeX resume code.
5. If a PDF compiler (`pdflatex` / `tectonic`) is installed, it opens a PDF preview automatically!

---

## ⚡ Daily Usage Guide & Shortcut Flags

Once setup is complete, here is how you can use the tool for your job applications:

### 1. Tailor from a Job Description File
Save a job description into a text file and run:
```bash
python -m src jobs/google_backend.txt
```

### 2. Read Directly from Clipboard (Ctrl+C / Cmd+C)
Copy any job posting text from LinkedIn or Indeed and run:
```bash
python -m src --clipboard
```

### 3. Display Audit Reports
Add flags to view audit reports on screen:
```bash
# Show ATS Match Score
python -m src jobs/google_backend.txt --ats

# Show Resume Diff (Selected vs Excluded jobs and bullets)
python -m src jobs/google_backend.txt --diff

# Show Reproducibility Manifest (Digital Fingerprint)
python -m src jobs/google_backend.txt --manifest

# Show ALL 3 Reports at once:
python -m src jobs/google_backend.txt --ats --diff --manifest
```

### 4. Copy LaTeX Code directly to Clipboard
Copy the raw LaTeX code to paste into [Overleaf](https://www.overleaf.com):
```bash
python -m src jobs/google_backend.txt --copy --no-pdf
```

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
3. **FastEmbed Semantic Vector Search**: Computes vector embeddings to discover conceptual job requirements.

### 3. Maximal Marginal Relevance (MMR) Bullet Selection (`src/ranker/bullet_ranker.py`)
Balances **Relevance** (how well a bullet matches the job description) against **Diversity** (preventing multiple bullet points from repeating the exact same topic).

### 4. 3-Tier Multi-Provider Rewriter Stack (`src/rewriter/`)
- **Tier A (Cloud LLM Pool)**: Tries providers by priority: **1st OpenRouter $\rightarrow$ 2nd Gemini $\rightarrow$ 3rd Cerebras $\rightarrow$ 4th Groq** (or top-priority `CUSTOM_API_KEY`). If one provider hits a rate limit, it automatically tries the next.
- **Tier B (Local Ollama GPU/CPU)**: Runs local AI model (`qwen2.5:1.5b`) if cloud APIs are unavailable.
- **Tier C (Python Rule Engine)**: Zero-latency deterministic rule engine that strengthens action verbs offline.
> **Strict Anti-Hallucination Guardrails**: Before any AI rewritten bullet is accepted, it must pass a strict Python validation layer that guarantees **100% Metric Retention** (no dropped/altered numbers or percentages) and **Length Bounding** (blocks overly verbose hallucinated paragraphs).

---

## 🧪 Running Automated Unit Tests (`pytest`)

To verify that all system components, vector calculations, and timeline rules are working correctly, run:

```bash
# Run full automated test suite (24 tests)
python -m pytest tests/ -v
```

**Expected Result**: All 24 unit & integration tests pass cleanly in under 35 seconds.

---

## 🛠️ Troubleshooting & Frequently Asked Questions

### 1. `ModuleNotFoundError: No module named 'src'`
- **Fix**: Make sure your terminal is opened in the main project directory (`CV pipeline`), and use `python -m src ...` instead of `python src/__main__.py`.

### 2. `Can't find model 'en_core_web_sm'`
- **Fix**: Run `python -m spacy download en_core_web_sm` in your terminal.

### 3. `No local LaTeX compiler found`
- **Fix**: If you don't have TeX Live or MiKTeX installed locally, use `python -m src jobs/google_backend.txt --copy --no-pdf` to copy your raw LaTeX code, then paste it directly into [Overleaf.com](https://www.overleaf.com) to download your PDF!

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
