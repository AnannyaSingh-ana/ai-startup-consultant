# Founders' Forge — Backend

AI-powered startup consultant backend. A team of 10 CrewAI agents research and generate a complete, grounded business plan from a user's business idea, target country, and target customer.

## Tech Stack
- Python 3.13
- CrewAI (multi-agent orchestration)
- OpenAI GPT-4o
- Serper API (live web search grounding)
- FastAPI
- PostgreSQL + SQLAlchemy

## Setup

1. Clone the repository:
   git clone https://github.com/AnannyaSingh-ana/ai-startup-consultant.git
   cd ai-startup-consultant
2. Create and activate a virtual environment:
   python -m venv venv
venv\Scripts\Activate.ps1
(If PowerShell blocks activation, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` first.)

3. Install dependencies:

pip install -r requirements.txt


4. Copy `.env.example` to `.env` and fill in your own keys:

OPENAI_API_KEY=your_openai_key_here
SERPER_API_KEY=your_serper_key_here
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/founders_forge


5. Make sure PostgreSQL is running locally (or point `DATABASE_URL` at a hosted instance). The required table is created automatically on first run.

6. Launch the API:

uvicorn api:app --reload


7. Visit `http://127.0.0.1:8000/docs` to confirm it's running and try the endpoints.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| POST | `/generate-plan` | Runs the full agent pipeline and returns a structured business plan |
| GET | `/plans` | Lists all saved plans |
| GET | `/plans/{plan_id}` | Returns one full saved plan |

## Evaluation

See `notebooks/evaluation_notebook.ipynb` for a runnable verification of JSON-parsing reliability and financial arithmetic accuracy.
