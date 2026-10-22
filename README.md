
# VeriFlow AI
### Multi-Agent Evidence Intelligence Platform

**VeriFlow AI** is an AI-powered claim verification platform that combines autonomous research, semantic evidence analysis, quotation validation, and transparent decision-making.

Powered by NVIDIA Nemotron through Nebius AI, VeriFlow AI investigates factual claims and produces preliminary, evidence-based assessments with traceable sources.

## The Problem

AI-generated answers can sound convincing even when the underlying evidence is weak, irrelevant, or incorrectly interpreted.

Traditional fact-checking workflows can also require significant manual research.

VeriFlow AI addresses this challenge through a structured, multi-agent verification pipeline.

## Our Solution

Instead of asking one AI model to decide whether a claim is true or false, VeriFlow AI divides the process into five specialized agents.

### 1. Planning Agent
Analyzes the claim and generates targeted research queries.

### 2. Research Agent
Retrieves relevant web sources using Tavily.

### 3. Verification Agent
Uses NVIDIA Nemotron to assess whether retrieved evidence supports, contradicts, or is insufficient to evaluate the claim.

Includes an additional semantic audit to examine whether decisive evidence actually justifies its assigned stance.

### 4. Evidence Validator
Checks whether cited quotations occur in the retrieved source content.

Invalid or unverified decisive quotations are downgraded.

### 5. Decision Agent
Aggregates validated evidence and generates a preliminary verdict.

## Architecture

```text
User Claim
    |
    v
Planning Agent
    |
    v
Research Agent (Tavily)
    |
    v
Verification Agent (NVIDIA Nemotron)
    |
    v
Semantic Evidence Audit
    |
    v
Evidence Validator
    |
    v
Decision Agent
    |
    v
Verification Report
    |
    +--> Evidence & Source Links
    |
    +--> PDF Report
```

## Verdict Categories

| Verdict | Meaning |
|---|---|
| PRELIMINARY_SUPPORT | Available validated evidence supports the claim |
| PRELIMINARY_CONTRADICTION | Available validated evidence contradicts the claim |
| CONFLICTING_EVIDENCE | Available evidence contains competing findings |
| INSUFFICIENT_EVIDENCE | Available evidence is not sufficient for a decisive assessment |

These verdicts are preliminary assessments, not guarantees of factual truth.

## Key Features

- Five-agent AI verification pipeline
- NVIDIA Nemotron integration through Nebius
- Live research through Tavily
- Semantic evidence auditing
- Exact quotation validation
- Traceable source links
- Real-time agent progress using Server-Sent Events
- Explainable preliminary verdicts
- Downloadable PDF reports
- Responsive web interface
- Conservative handling of insufficient evidence

## Technology Stack

**AI**
- NVIDIA Nemotron
- Nebius AI API

**Research**
- Tavily Search API

**Backend**
- Python
- FastAPI
- Pydantic

**Frontend**
- HTML
- CSS
- JavaScript
- Server-Sent Events (SSE)

**Reporting**
- PDF generation

## Project Structure

```text
VeriFlow-AI/
├── backend/
│   ├── main.py
│   ├── streaming.py
│   ├── planning_agent.py
│   ├── research_agent.py
│   ├── verification_agent.py
│   ├── evidence_validator.py
│   ├── decision_agent.py
│   └── pdf_generator.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .gitignore
└── README.md
```

Additional test scripts are included in the repository.

## Getting Started

### Requirements

- Python 3.12 or compatible version
- Nebius API key
- Tavily API key

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/VeriFlow-AI.git
cd VeriFlow-AI
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Install dependencies

Install the Python dependencies required by the backend.

### 4. Configure environment variables

Create a `.env` file:

```env
NEBIUS_API_KEY=your_nebius_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Never commit real API keys.

### 5. Start the server

On Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 6. Open the application

Visit:

http://127.0.0.1:8000

Enter a claim, run the analysis, inspect the evidence, and optionally download a PDF report.

## Testing

The project includes tests covering:

- Agent functionality
- Evidence validation
- Semantic auditing
- Decision logic
- Prompt-injection resistance
- Adversarial scenarios
- Streaming integration
- API connectivity

A live integration test successfully completed all five agents for the claim:

> Water is made of hydrogen and oxygen.

Observed results:

- HTTP status: 200
- Completed agents: 5/5
- Preliminary verdict: PRELIMINARY_SUPPORT
- Supporting assessments: 5
- Insufficient assessments: 1
- Execution time: 45.57 seconds

These results describe one successful live test, not a comprehensive accuracy benchmark.

Earlier benchmark experiments identified limitations involving semantic evidence assessment, incomplete API responses, and latency. Improvements were implemented afterward, but comprehensive accuracy has not yet been remeasured.

## Security and Reliability

- API credentials are stored in environment variables.
- Sensitive local environment files are excluded from Git.
- Source content is treated as untrusted input.
- Decisive quotations require validation.
- Technical failures are distinguished from insufficient evidence.
- The interface presents preliminary findings with appropriate limitations.

## Limitations

- Results depend on available online sources.
- AI-generated interpretations may be incorrect.
- Exact quotation matching does not independently prove that a source is trustworthy.
- Evidence may be incomplete, outdated, or misleading.
- Live analysis requires third-party API access and may incur costs.
- Human review is recommended for important decisions.

## Hackathon

Developed for the **Nebius × NVIDIA Global AI Hackathon 2026**.

The project demonstrates an application of NVIDIA Nemotron in multi-agent evidence analysis and explainable AI workflows.

## Author

Dana Almutairi

Software Engineering Graduate

## Disclaimer

VeriFlow AI is a research and decision-support prototype. Its outputs should not be treated as definitive factual judgments or professional advice.
