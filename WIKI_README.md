# CV Pipeline - Python & Package Reference Wiki

Welcome to the **CV Pipeline Technical Wiki**! This document provides an educational reference for Python programming fundamentals as well as a complete breakdown of all Python packages used in this project with working code examples.

---

## Python Core Concepts Used

### 1. Classes and Constructors (`__init__`)
In Python, think of a **Class** as a cookie cutter (a blueprint), and an **Object** as the cookie you make from it. You use classes to group related data and functions together into a single, organized unit. 
The **Constructor** (which is always named `__init__` in Python) is a special setup function that runs automatically the moment you create a new object. It sets up the initial state (the "ingredients") for that specific object.

```python
class Experience:
    # The constructor is called the moment we create a new Experience
    def __init__(self, company_name: str, job_title: str):
        # We attach these variables to 'self' so the object remembers them
        self.company = company_name
        self.title = job_title
        self.bullets = []  # Starts with an empty list of resume bullets

    # A method (function) that belongs to this class
    def add_bullet(self, text: str):
        self.bullets.append(text)
        print(f"Added bullet to {self.company}: '{text}'")

    def get_summary(self) -> str:
        return f"{self.title} at {self.company} ({len(self.bullets)} bullets)"

# 1. Instantiation (creating the object). This automatically calls __init__
my_job = Experience(company_name="Amazon", job_title="Backend Engineer")

# 2. Using the object's methods
my_job.add_bullet("Built a highly scalable Kafka streaming pipeline.")
my_job.add_bullet("Reduced server costs by 15%.")

# 3. Viewing the result
print(my_job.get_summary()) 
# Output: Backend Engineer at Amazon (2 bullets)
```

### 2. Control Flow & Fallback Exception Handling (`try / except`)
Sometimes things go wrong in programming—like an API goes offline, or you lose internet connection. Instead of letting the program crash abruptly, we use `try` and `except` blocks to handle "Exceptions" (errors).
- **`try`**: "Try to do this risky thing."
- **`except`**: "If an error happens, don't crash! Do this backup plan instead."

```python
def fetch_user_data(user_id: int):
    # Imagine this function connects to a database over the internet
    if user_id < 0:
        raise ConnectionError("Database server is unreachable right now!")
    return {"name": "Alice", "role": "Engineer"}

def safe_get_user(user_id: int):
    try:
        # We try the risky operation
        print(f"Attempting to fetch user {user_id}...")
        data = fetch_user_data(user_id)
        print("Success!", data)
        
    except ConnectionError as e:
        # If the database fails, we catch the specific error and run a backup plan
        print(f"Network failure: {e}")
        print("Switching to offline backup data instead.")
        
    except Exception as e:
        # This catches ANY other unexpected errors (like a typo in our code)
        print(f"An unexpected disaster happened: {e}")

# This will succeed
safe_get_user(5)

# This will trigger the ConnectionError, but the program WON'T crash!
safe_get_user(-1)
```

### 3. Module Execution (`python -m src` vs `python src/__main__.py`)
When working with multi-file Python projects:
- `python script.py` executes a single file, adding that file's directory to Python's module search path (`sys.path`).
- `python -m package_name` executes a directory or package as a module, adding the **current working directory** to `sys.path` and searching for `__main__.py`.

Using `python -m src` ensures that relative package imports (like `from .models.config import PipelineConfig`) resolve correctly across all subdirectories and submodules regardless of operating system.

---

## Comprehensive Package Reference & Code Examples

Here is the complete list of third-party Python packages used in this pipeline and what each one does. If you're new to Machine Learning (ML) or Python, we've broken down all the concepts for you!

### 1. `pydantic`
- **What it does**: Enforces strict rules on what data should look like (Data Validation) using Python "Type Hints". If a function expects an integer (a whole number), Pydantic guarantees it doesn't accidentally receive a text string like `"five"`.
- **Why we use it**: It acts as an automated safety net. Without it, malformed data (like a missing field in a YAML file) might crash our program deep inside the code where it's hard to debug. With Pydantic, the program catches the mistake at the very front door.
- **Code Example Breakdown**: We define a nested model where a `Job` contains multiple `Bullet` objects. Pydantic ensures everything is typed correctly.

```python
from pydantic import BaseModel, Field, ValidationError

class Bullet(BaseModel):
    id: int
    text: str

class Job(BaseModel):
    company: str
    # Ensures 'bullets' is specifically a list of Bullet objects
    bullets: list[Bullet] = Field(default_factory=list)

try:
    # This works perfectly
    good_job = Job(
        company="Google", 
        bullets=[{"id": 1, "text": "Wrote Python code."}]
    )
    print("Successfully created Job for:", good_job.company)

    # This will FAIL because 'id' is a string ("one") instead of an integer
    bad_job = Job(
        company="Microsoft",
        bullets=[{"id": "one", "text": "Oops."}]
    )
except ValidationError as e:
    print("Pydantic caught an error!")
    print(e)
    # Output clearly states: "Input should be a valid integer" for the bullet id
```

### 2. `pyyaml`
- **What it does**: Reads `.yaml` files and translates them into native Python data structures (like dictionaries and lists). YAML prioritizes human readability, using indentation (spaces) instead of curly braces `{}` or commas.
- **Why we use it**: We store your actual resume experiences (the raw data) in YAML files because they are extremely easy for a human to read and edit.
- **Code Example Breakdown**: We simulate writing data to a YAML file, and then reading it back into a Python dictionary.

```python
import yaml
import os

# 1. The data we want to save
my_resume_data = {
    "name": "John Doe",
    "skills": ["Python", "Machine Learning", "Docker"],
    "experience": {
        "company": "Startup Inc",
        "years": 2
    }
}

# 2. Write the Python dictionary to a YAML file
with open("test_resume.yaml", "w") as file:
    # default_flow_style=False makes it human-readable (indented)
    yaml.dump(my_resume_data, file, default_flow_style=False)

# 3. Read it back from the file into Python
with open("test_resume.yaml", "r") as file:
    loaded_data = yaml.safe_load(file)

print("Loaded Skills:", loaded_data["skills"])
# Output: Loaded Skills: ['Python', 'Machine Learning', 'Docker']

# Cleanup
os.remove("test_resume.yaml")
```

### 3. `python-dotenv`
- **What it does**: Loads "environment variables" from a hidden text file named `.env` directly into your computer's memory. 
- **Why we use it**: Security! You never want to save sensitive data (like your OpenAI API key) directly in your code files (`.py`), because if you share your code online, hackers will steal your keys. 
- **Code Example Breakdown**: We load a `.env` file and show how to safely handle a missing key without crashing.

```python
import os
from dotenv import load_dotenv

# Let's pretend this file exists on your computer:
# --- .env ---
# SECRET_API_KEY=sk-abc123def456
# ----------------

# 1. Load the hidden variables into Python's memory
load_dotenv() 

# 2. Retrieve the key safely. 
# We use os.getenv() so it returns None if it's missing, rather than crashing.
api_key = os.getenv("SECRET_API_KEY")

if api_key is None:
    print("CRITICAL ERROR: Please add SECRET_API_KEY to your .env file!")
else:
    # Only print the first few characters for security!
    masked_key = api_key[:6] + "..."
    print(f"Successfully loaded API key: {masked_key}")
```

### 4. `fastembed`
- **What it does**: Generates "vector embeddings". AI models don't read words; they need numbers. An "embedding" model translates a sentence into a coordinate (a vector) of numbers. The magic is that sentences with similar meanings end up with similar numbers! `fastembed` does this on your CPU extremely fast.
- **Why we use it**: We use it to mathematically compare how well your resume bullet points match the requirements in a job description.
- **Code Example Breakdown**: We embed two sentences. The output is a massive list of numbers that represent the "meaning" of the text.

```python
from fastembed import TextEmbedding

# 1. Load the AI embedding model (it downloads it the first time)
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 2. Provide a list of text we want to convert to numbers
sentences = [
    "I love programming in Python.",
    "Software engineering is my passion."
]

# 3. Generate the embeddings (this is almost instant)
embeddings_generator = model.embed(sentences)
embeddings_list = list(embeddings_generator)

print(f"We embedded {len(embeddings_list)} sentences.")

# Let's look at the first sentence's "meaning" in numbers
first_sentence_vector = embeddings_list[0]
print(f"The vector has {len(first_sentence_vector)} dimensions (numbers).")
print("Here are the first 5 numbers representing the text's meaning:")
print(first_sentence_vector[:5])
# Output: [-0.015,  0.042, -0.110,  0.088,  0.001]
```

### 5. `scikit-learn`
- **What it does**: A massive Machine Learning library. We use **TF-IDF** (penalizes common words like "the", rewards rare words like "Kafka") and **Cosine Similarity** (measures the angle between two mathematical vectors to see how similar they are).
- **Why we use it**: It calculates the final "Match Score" between your experience and a job description. 
- **Code Example Breakdown**: We take a Job Description and 3 of your resume bullets, and mathematically calculate which bullet matches the job best.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. The setup
job_description = "We need a backend developer experienced with Java and Kafka streaming."
my_bullets = [
    "Designed the frontend UI using React and CSS.",          # Unrelated
    "Managed database migrations for user accounts.",         # Slightly related
    "Built a high-throughput Java backend using Apache Kafka." # Perfect match
]

# 2. Combine them so the AI learns all the vocabulary
all_text = [job_description] + my_bullets

# 3. Convert the text into TF-IDF mathematical matrices
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(all_text)

# tfidf_matrix[0] is the Job Description. Let's compare it to the 3 bullets.
job_vector = tfidf_matrix[0]
bullet_vectors = tfidf_matrix[1:]

# 4. Calculate Cosine Similarity (Scores range from 0.0 to 1.0)
scores = cosine_similarity(job_vector, bullet_vectors)[0]

print("Match Scores against the Job Description:")
for bullet, score in zip(my_bullets, scores):
    # Convert score to a percentage
    print(f"- {score*100:.1f}% Match | {bullet}")

# Output will show the Java/Kafka bullet has a massively higher score!
```

### 6. `rapidfuzz`
- **What it does**: Calculates the "Levenshtein distance"—the number of single-character edits (insertions, deletions, or substitutions) needed to turn one word into another.
- **Why we use it**: To handle typos or variations in technical skills. If a recruiter writes "React.js" and you have "ReactJS", they are 95% the same.
- **Code Example Breakdown**: We simulate searching a database of your skills for a misspelled search query.

```python
from rapidfuzz import process, fuzz

# My actual resume skills
my_valid_skills = ["Apache Kafka", "ReactJS", "PostgreSQL", "Docker"]

# A recruiter searches with a typo and slight variation
search_query = "postgre sql"

# process.extractOne searches the list and finds the best fuzzy match
best_match = process.extractOne(
    query=search_query, 
    choices=my_valid_skills, 
    scorer=fuzz.ratio  # Use a strict character-by-character ratio
)

# best_match returns a tuple: (Matched_String, Score_out_of_100, Index_in_list)
matched_skill, match_score, index = best_match

print(f"User searched for: '{search_query}'")
print(f"Closest match found: '{matched_skill}' with a score of {match_score:.1f}/100")

if match_score > 80.0:
    print("Action: Automatically linking this skill!")
else:
    print("Action: No confident match found.")
```

### 7. `spacy`
- **What it does**: The gold-standard library for Natural Language Processing (NLP). It uses AI to teach the computer human grammar: Tokenization (slicing words), POS Tagging (finding nouns/verbs), and NER (spotting Company Names, Dates).
- **Why we use it**: Job descriptions are walls of text. We use `spacy` to intelligently highlight the hiring company's name or specific products.
- **Code Example Breakdown**: We process a sentence and extract the Nouns/Verbs, and then identify the real-world Entities.

```python
import spacy

# 1. Load the small English AI model
# (Note: Requires running `python -m spacy download en_core_web_sm` first)
nlp = spacy.load("en_core_web_sm")

text = "In 2023, Google launched a new Artificial Intelligence tool in California."
doc = nlp(text)

print("--- Parts of Speech ---")
for token in doc:
    # Only print Nouns and Verbs
    if token.pos_ in ["NOUN", "VERB", "PROPN"]: 
        print(f"Word: {token.text:15} | Type: {token.pos_}")

print("\n--- Named Entities (NER) ---")
for ent in doc.ents:
    # This will identify '2023' as a DATE, 'Google' as an ORG, 'California' as a GPE (Location)
    print(f"Entity: {ent.text:15} | Label: {ent.label_}")
```

### 8. `yake`
- **What it does**: Automatically extracts the most important phrases (keywords) from text. It is "Unsupervised"—meaning it uses pure statistical rules (like word frequency and capitalization) rather than a massive AI model.
- **Why we use it**: It acts like an automated highlighter, picking out critical technical terms from a job description so we know what skills to emphasize.
- **Code Example Breakdown**: We extract multi-word phrases and filter out the weak ones based on their statistical score.

```python
import yake

job_posting = """
We are looking for a Senior Software Engineer. The ideal candidate will have 
5 years of experience building scalable backend services. You must be proficient 
in Python, Django, and deploying containerized applications using Kubernetes. 
Experience with cloud providers like AWS is a major plus.
"""

# 1. Configure the extractor. 
# lan="en", n=2 (max 2 words per phrase), top=5 (give me the 5 best)
extractor = yake.KeywordExtractor(lan="en", n=2, top=5)

# 2. Extract keywords. 
# NOTE: YAKE scores are weird—a LOWER score means it is MORE important!
keywords = extractor.extract_keywords(job_posting)

print("Top extracted keywords from the job posting:")
for rank, (phrase, score) in enumerate(keywords, 1):
    print(f"#{rank}: '{phrase}' (Score: {score:.3f})")
```

### 9. `jinja2`
- **What it does**: A "template engine". Think of it like a very advanced "mail merge". You write a document layout with placeholders, and Jinja2 injects the real data. It supports `if` statements and `for` loops inside the text template!
- **Why we use it**: We separate the Python logic from the LaTeX design. Jinja2 injects the final text into a beautiful template to generate the PDF.
- **Code Example Breakdown**: We create a multi-line HTML/LaTeX-style template with a `for` loop, and pass it a list of dictionaries.

```python
import jinja2

# 1. Create a template string with placeholders and a for-loop
template_text = """
RESUME: {{ name.upper() }}
=======================
Experience:
{% for job in jobs %}
  - {{ job.title }} at {{ job.company }}
    {% if job.promoted %} (Promoted!) {% endif %}
{% endfor %}
"""

# 2. Compile the template
template = jinja2.Template(template_text)

# 3. Define our real Python data
my_data = {
    "name": "Jane Doe",
    "jobs": [
        {"title": "Senior Dev", "company": "Apple", "promoted": True},
        {"title": "Junior Dev", "company": "StartupX", "promoted": False}
    ]
}

# 4. Render it! The variables replace the {{ }} placeholders.
final_document = template.render(name=my_data["name"], jobs=my_data["jobs"])

print(final_document)
# Output will cleanly list both jobs, and conditionally add "(Promoted!)" to Apple.
```

### 10. `openai`
- **What it does**: The official library to communicate with Large Language Models (LLMs) over the internet. This library is an industry standard and can talk to OpenRouter, Gemini, Cerebras, Groq, or OpenAI.
- **Why we use it**: We use AI to dynamically rewrite and polish your resume bullet points to sound highly professional.
- **Code Example Breakdown**: We set up the client, provide a "System Prompt" (instructions) and a "User Prompt" (data), and parse the response.

```python
from openai import OpenAI
import os

# 1. Setup the client (Make sure your API key is set in your environment!)
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY", "dummy_key_for_example"),
    # Pointing this to OpenRouter endpoint (Priority 1) as an example
    base_url="https://openrouter.ai/api/v1" 
)

def rewrite_bullet(raw_bullet: str) -> str:
    try:
        # 2. Make the API call
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a professional resume writer. Make the text sound highly impactful."},
                {"role": "user", "content": f"Rewrite this: {raw_bullet}"}
            ],
            temperature=0.3
        )
        
        # 3. Dig into the response object to pull out just the text string
        return response.choices[0].message.content
        
    except Exception as e:
        return f"API Error: {str(e)}"

# Example Usage:
# print(rewrite_bullet("I fixed some bugs in the database"))
# Output: "Resolved critical database anomalies, optimizing system performance..."
```

### 11. `requests`
- **What it does**: The industry standard for sending HTTP requests from Python. When you type a URL into Chrome, it sends a "GET request". Python can do exactly the same thing.
- **Why we use it**: To "ping" our local AI server (Ollama) to check if it's turned on before running the pipeline, avoiding a crash later.
- **Code Example Breakdown**: We wrap the request in a `try/except` block to handle cases where the server is completely turned off (which would throw a `ConnectionError`).

```python
import requests

def check_local_server_health():
    url = "http://localhost:11434/api/tags" # Standard Ollama port
    
    try:
        print(f"Pinging {url}...")
        # timeout=2 ensures we don't wait forever if the server is frozen
        response = requests.get(url, timeout=2)
        
        # Status 200 means "OK" in web protocols
        if response.status_code == 200:
            print("Local AI server is online and ready!")
        else:
            print(f"Server responded, but with an error code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("CRITICAL: The server is turned off. Please start Ollama!")
    except requests.exceptions.Timeout:
        print("CRITICAL: The server took too long to respond.")

# Run the health check
check_local_server_health()
```

### 12. `numpy`
- **What it does**: The absolute backbone of data science and math in Python. Normal Python lists are extremely slow at doing math. Numpy provides "Arrays" which are written in highly optimized C-code, making them lightning fast.
- **Why we use it**: We use Numpy to calculate vector dot products to mathematically rank your resume bullet points.
- **Code Example Breakdown**: We perform math on entire arrays simultaneously, and use `np.argmax` to find the highest score.

```python
import numpy as np

# Normal Python lists
prices = [10, 20, 30]
# prices * 2 in Python just duplicates the list: [10, 20, 30, 10, 20, 30]

# 1. Convert to Numpy Arrays
np_prices = np.array([10, 20, 30])

# 2. Math is applied element-wise instantly!
np_discounted = np_prices * 0.8 
print("Discounted prices:", np_discounted) # [ 8. 16. 24.]

# 3. Vector math (Dot Product)
vec_a = np.array([1.0, 2.0, 3.0])
vec_b = np.array([4.0, 5.0, 6.0])
dot_product = np.dot(vec_a, vec_b) # (1*4) + (2*5) + (3*6)
print(f"Dot product: {dot_product}") # 32.0

# 4. Finding the best score
scores = np.array([0.45, 0.92, 0.33, 0.88])
best_index = np.argmax(scores) # Returns the index of the highest number
print(f"The highest score is at index {best_index} ({scores[best_index]})")
```

### 13. `pyperclip`
- **What it does**: A simple tool that lets Python interact directly with your computer's copy-paste clipboard (Ctrl+C / Ctrl+V).
- **Why we use it**: You can copy a job description from LinkedIn, and the pipeline can instantly read it from your clipboard.
- **Code Example Breakdown**: Reading the clipboard, modifying the text, and copying it back.

```python
import pyperclip

def capitalize_clipboard():
    # 1. Read whatever the user just copied (Ctrl+C)
    current_text = pyperclip.paste()
    
    if not current_text:
        print("Your clipboard is empty!")
        return

    print(f"Read from clipboard: '{current_text}'")
    
    # 2. Modify the text
    shouting_text = current_text.upper()
    
    # 3. Write it back to the clipboard (Ctrl+V will now paste the new text)
    pyperclip.copy(shouting_text)
    print("Success! Try pasting somewhere now.")

# Example Usage:
# capitalize_clipboard()
```

### 14. `pytest`
- **What it does**: A framework for writing and running "Automated Tests". Tests are mini-scripts that run your main code, pass it fake data, and verify the output matches exactly what you expected.
- **Why we use it**: To guarantee reliability! `pytest` runs hundreds of checks in the background to ensure no recent code changes accidentally broke the pipeline.
- **Code Example Breakdown**: We write a test function for a piece of our logic. If `assert` fails, `pytest` raises a loud red error.

```python
# --- Our main application code (math_utils.py) ---
def calculate_discount(price: float, discount_percent: float) -> float:
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - (discount_percent / 100))

# --- Our test code (test_math.py) ---
import pytest
# from math_utils import calculate_discount

def test_calculate_discount_normal():
    # 1. Setup the inputs and expected output
    price = 100.0
    discount = 20.0
    expected = 80.0
    
    # 2. Run the actual function
    result = calculate_discount(price, discount)
    
    # 3. Assert (Guarantee) the result is correct
    assert result == expected

def test_calculate_discount_invalid_input():
    # We can also test that our program correctly THROWS an error 
    # when given bad data, using pytest.raises
    with pytest.raises(ValueError):
        calculate_discount(100.0, 150.0) # 150% discount should trigger ValueError

# To run these tests, you would type `pytest test_math.py` in your terminal!
```

---

## Complete Terminal Command Cheat-Sheet

Here is a handy reference for all terminal execution and testing commands:

### Running the Resume Generator
```bash
# 1. Basic tailoring from a file
python -m src jobs/google_backend.txt

# 2. Read JD directly from clipboard
python -m src --clipboard

# 3. Apply target company weighting boost (e.g., google)
python -m src jobs/google_backend.txt --company google

# 4. Display ATS report, diff report, and manifest
python -m src jobs/google_backend.txt --ats --diff --manifest

# 5. Output raw LaTeX string only & copy to clipboard (no PDF compile)
python -m src jobs/google_backend.txt --no-pdf --copy

# 6. Run pure vector ranking without AI bullet rewriting
python -m src jobs/google_backend.txt --no-rewrite
```

### Running Automated Tests
```bash
# 1. Run full test suite
python -m pytest tests/

# 2. Run with verbose test details
python -m pytest tests/ -v

# 3. Run and print console logs/output
python -m pytest tests/ -s

# 4. Stop execution on first failing test
python -m pytest tests/ --maxfail=1

# 5. Run a specific test file
python -m pytest tests/test_multi_api_stack.py

# 6. Run tests matching a keyword
python -m pytest tests/ -k "timeline"
```
