# Alpha Insights - AI Sales Analytics System

## Architecture Overview

**Hybrid Deployment Model**: React SPA frontend + Flask serverless backend, both deployed on Vercel with Supabase as external database.

- **Frontend**: React 18 + TypeScript + Vite (port 8080 local, CDN in production)
- **Backend**: Flask API (port 5000 local, serverless functions in production via `api/index.py`)
- **Database**: Supabase (PostgreSQL) - single table `vendas_2024` with 2600+ sales records
- **AI**: Google Gemini 2.5 Flash for natural language sales analysis

### Critical Design Decisions

1. **No pandas in serverless**: `api/index.py` uses manual aggregation (loops/dicts) instead of pandas to avoid cold start timeouts in Vercel's serverless environment. See `api/index_original_backup.py` for pandas version.

2. **Dynamic imports**: Gemini SDK imported only in `/api/analyze` endpoint to minimize cold start time for other routes.

3. **Proxy configuration**: In development, Vite proxies `/api/*` to `http://localhost:5000` (see `vite.config.ts`). In production, Vercel routes handle this via `vercel.json`.

## Development Workflow

### Starting the Application

**Recommended (Windows)**:
```cmd
start-all.bat
```
This launches two separate CMD windows:
- Backend: `cd api && python run_simple.py` (port 5000)
- Frontend: `npm run dev` (port 8080)

**Alternative**: VS Code tasks defined in `.vscode/tasks.json`:
- "Start Backend" → runs `python run_simple.py` in `api/` folder
- "Start Frontend" → runs `npm run dev`
- "Start All Servers" → depends on both above

**IMPORTANT**: Backend must use `use_reloader=False` (see `api/run_simple.py`) to avoid double-loading issues on Windows.

### Environment Variables

Located in `api/.env` (NOT root `.env`):
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<anon_key>
GEMINI_API_KEY=<api_key>
SUPABASE_TABLE_NAME=vendas_2024
```

Use `python-dotenv` to load in backend. Frontend has no `.env` dependency (API calls proxied).

### Testing the Stack

1. **Health check**: `http://localhost:5000/api/health` - verifies env vars configured
2. **Metrics**: `http://localhost:5000/api/metrics` - tests Supabase connection and aggregation
3. **Frontend**: `http://localhost:8080` - should show dashboard with real metrics

## Code Conventions

### Backend (Python)

- **Serverless compatibility**: Avoid heavy imports at module level. Keep `api/index.py` lean.
- **Currency formatting**: Use `"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')` for Brazilian format (R$ 1.234,56)
- **Date handling**: Store as ISO format in DB (`YYYY-MM-DD`), display as `DD/MM/YYYY`
- **Error responses**: Return HTTP 200 with error fields (e.g., `{"error": "...", "no_data": True}`) to maintain frontend stability

### Frontend (React + TypeScript)

- **UI Components**: All use `shadcn/ui` from `src/components/ui/`. Never write raw Radix UI imports - use the abstraction layer.
- **Icons**: `lucide-react` only. Avoid other icon libraries.
- **Notifications**: Use `sonner` toast library: `import { toast } from "sonner"` then `toast.success()`, `toast.error()`, etc.
- **API calls**: Always use `/api/*` paths (proxy handles routing). Example:
  ```typescript
  const response = await fetch('/api/metrics');
  const data = await response.json();
  ```

### File Upload Pattern

Upload endpoint: `POST /api/upload-data` (multipart/form-data)
- Accepts: `.xlsx`, `.xls`, `.csv` (max 10MB)
- Expected columns: `Data`, `ID_Transacao`, `Produto`, `Categoria`, `Regiao`, `Quantidade`, `Preco_Unitario`, `Receita_Total`
- See `FORMATO_PLANILHAS.md` for complete spec and validation rules
- Backend normalizes column names (removes accents, lowercases, replaces spaces with `_`)

## Database Schema

Table: `vendas_2024` (see `api/supabase_schema.sql`)

Key columns:
- `data` (DATE) - indexed
- `produto`, `categoria`, `regiao` - indexed for fast filtering
- `quantidade`, `preco_unitario`, `receita_total` (NUMERIC)
- `mes_origem` (TEXT) - source file identifier
- `id_transacao` (TEXT) - unique transaction ID

**RLS enabled** but policy allows all operations (using service_role key in production).

## AI Integration

**Gemini Prompt Pattern** (see `api/index.py` line ~190):
```python
model = genai.GenerativeModel('gemini-2.5-flash')
prompt = f"""Baseado nos dados de vendas:
{sample_data[:5]}

Responda a pergunta: {question}
Responda em português, de forma clara e objetiva."""
```

**3-Level Fallback System**:
1. Try Gemini AI with sample data (100 rows limit)
2. If blocked/error, return generic response based on question keywords
3. If both fail, return friendly error message

Frontend suggests specific questions (see `SUGGESTED_QUESTIONS` in `src/pages/Index.tsx`) to reduce API blocks from vague prompts.

## Deployment (Vercel)

**Build configuration** (`vercel.json`):
- Frontend: `@vercel/static-build` → outputs to `dist/`
- Backend: Two Python functions:
  - `api/index.py` - main API (routes: `/api/health`, `/api/metrics`, `/api/analyze`, `/api/upload-data`)
  - `api/diagnostic.py` - minimal health check

**Environment variables** (set in Vercel dashboard):
- Same as local `.env` file
- Required for all environments: Production, Preview, Development

**Deployment trigger**: Every `git push` to `main` auto-deploys. See `DEPLOY_VERCEL.md` for complete guide.

## Common Patterns

### Adding a New Metrics Card
1. Update `/api/metrics` endpoint to include new calculation
2. Update `MetricsData` interface in `src/pages/Index.tsx`
3. Add `<MetricsCard />` component in dashboard grid

### Adding a New API Endpoint
1. Add route in `api/index.py`: `@app.route('/api/your-endpoint', methods=['GET'])`
2. Test locally: `http://localhost:5000/api/your-endpoint`
3. Frontend calls via: `fetch('/api/your-endpoint')`

### Debugging Vercel Serverless Issues
- Check "View Function Logs" in Vercel deployment page
- Common issue: Cold start timeout (>10s) - reduce imports or optimize queries
- Test locally first: `vercel dev` command simulates serverless environment

## Documentation References

- `README.md` - Setup guide, tech stack, deployment overview
- `GUIA_RAPIDO.md` - Quick reference for all API endpoints
- `FORMATO_PLANILHAS.md` - Complete spreadsheet format specification
- `DEPLOY_VERCEL.md` - Step-by-step Vercel deployment
- `CHECKLIST.md` - Pre-deployment verification checklist
