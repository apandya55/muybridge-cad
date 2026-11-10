# Contributing to Muybridge CAD

Thanks for taking an interest in Muybridge CAD. We welcome bug reports, test cases, and pull requests.

## Development Workflow

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenSCAD (optional, required if validating OpenSCAD source: `brew install openscad` on macOS)

### 1. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run tests from the repository root:

```bash
pytest tests -v
```

Start the FastAPI server:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The Next.js dev server runs at `http://localhost:3000` and proxies `/api` and `/jobs` to the backend on `:8000`.

Check formatting and types:

```bash
cd frontend
npm run lint
npm run build
```

## Pull Request Guidelines

1. **Keep changes focused**: One feature or bug fix per PR.
2. **Include tests**: If you add a geometry check, compiler feature, or API endpoint, add a test in `tests/`.
3. **Verify locally**: Make sure `pytest tests -v` and `npm run build` pass before submitting.
4. **Clean commit messages**: Write descriptive, imperative commit messages (e.g. `fix: inward ray offset for wall thickness measurement`).
