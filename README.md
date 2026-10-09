# AgenticDev

AgenticDev is a web-based AI coding agent that turns natural-language
development requests into project files. It analyzes the supplied workspace,
creates an implementation plan, waits for optional human approval, generates
code, validates the result, reviews the changes, and presents the generated
project for preview.

## Highlights

- Natural-language coding requests with optional project/file context
- Multi-agent workflow powered by LangGraph
- Planner, Coder, Validator, and Reviewer agents
- Human approval gate before code generation
- Configurable OpenAI primary model and Groq fallback model
- FastAPI REST endpoints and Server-Sent Events (SSE) streaming
- Session event history for each agent run
- React + Vite JavaScript frontend
- Monaco-based file editing and project file explorer
- Browser-side project execution and live preview through WebContainers
- Downloadable generated project files

## Architecture

```text
React + Vite frontend
        |
        | REST + Server-Sent Events
        v
FastAPI backend
        |
        v
LangGraph workflow
        |
        +--> Planner
        |      |
        |      +--> Understand the request and project context
        |      +--> Produce an implementation plan
        |      +--> Request human approval
        |
        +--> Coder
        |      |
        |      +--> Generate or modify project files
        |      +--> Emit file-created events
        |
        +--> Validator
        |      |
        |      +--> Perform static project inspection
        |      +--> Report errors and warnings
        |
        +--> Reviewer
               |
               +--> Review quality and requirement coverage
               +--> Produce the final workflow summary
```

The workflow is exposed through an asynchronous event queue. The FastAPI
streaming endpoint converts workflow events into SSE messages so the frontend
can show agent progress, approval requests, generated files, validation
results, and completion status in real time.

## Technology stack

### Backend

- Python 3.12+
- FastAPI and Uvicorn
- LangChain and LangGraph
- Pydantic models for request, project, approval, event, validation, and review
  schemas
- YAML and environment-based configuration

### Frontend

- React 18
- Vite
- JavaScript
- Monaco Editor
- WebContainers
- JSZip
- Lucide React

## Workflow

1. The user submits a prompt and may include a project snapshot.
2. The Planner creates an implementation plan and identifies relevant files.
3. The workflow pauses for human plan approval.
4. After approval, the Coder generates or modifies project files.
5. The Validator statically checks paths, imports, configuration, entrypoints,
   and requirement coverage.
6. The Reviewer evaluates the generated result and returns a summary.
7. The frontend displays the files and makes the project available for preview.

If the coding response cannot be parsed or the Coder fails, the workflow
creates a small fallback project so the run still produces an explicit result.

## API endpoints

The backend runs on `http://localhost:8000` by default.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Check backend availability and configured agent framework |
| `POST` | `/api/agent/run` | Run the workflow and return a non-streaming response |
| `POST` | `/api/agent/run/stream` | Run the workflow and stream SSE events |
| `GET` | `/api/agent/{run_id}/approval` | Read a pending approval |
| `POST` | `/api/agent/{run_id}/approval` | Approve or reject a plan |
| `GET` | `/api/agent/session/{session_id}/memory` | Read recent session events |

Example request:

```json
{
  "prompt": "Create a modern task dashboard",
  "project": {
    "name": "my-project",
    "framework": "react",
    "entrypoint": "src/main.jsx",
    "files": []
  }
}
```

## Configuration

Model and workflow defaults are defined in [config.yaml](./config.yaml).
Environment variables are loaded by the backend configuration module and should
be used for credentials and deployment-specific overrides. Never commit API
keys or other secrets.

The default model configuration includes:

- OpenAI as the primary provider
- Groq as the fallback provider
- Configurable temperature and request timeout
- A required plan-approval gate

Set the frontend API URL when the backend is not running locally:

```env
VITE_API_URL=http://localhost:8000
```

## Local development

### Backend

Create or activate a Python 3.12+ environment, install the dependencies, and
start FastAPI:

```powershell
uv sync
uv run uvicorn backend.main:app --reload --port 8000
```

If `uv` is not available, install the packages from
[requirements.txt](./requirements.txt) into an equivalent Python environment.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually
`http://localhost:5173`. The frontend uses the backend URL from
`VITE_API_URL`, falling back to `http://localhost:8000`.

### Production build

```powershell
cd frontend
npm run build
npm run preview
```

## Project structure

```text
backend/
  main.py                         FastAPI application and API routes
  models.py                       Pydantic request/response models
  langgraph_app/
    agents/                       Planner, Coder, Validator, Reviewer, and LLM setup
    workflow/                     LangGraph graph, runner, and session context
  adk_app/workflow/               Shared approval and file-event utilities
frontend/
  src/
    components/                   Editor, activity, preview, and workspace UI
    services/api.js                REST, SSE, approval, and memory clients
    runtime/                      WebContainer project runtime
config.yaml                       Model and workflow defaults
requirements.txt                  Python dependency list
pyproject.toml                    Python project metadata and uv configuration
```

## Validation

Run the backend test suite with:

```powershell
uv run pytest
```

Build the frontend to verify the production bundle:

```powershell
cd frontend
npm run build
```

