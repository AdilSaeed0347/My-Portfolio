# Dev Guide - Pre-Deployment Audit (Current State)

Generated: April 17, 2026  
Scope: Workspace reality check after recent fixes  
Project: AI-Powered Portfolio Assistant with RAG

---

## 1) Current Architecture Snapshot

### Frontend
- Stack: Static HTML/CSS/JavaScript.
- Hosting target: Vercel static hosting.
- Routing: Clean route mapping configured in `frontend/vercel.json`.
- Runtime API endpoint strategy:
  - `frontend/config.js` builds `window.CONFIG.BACKEND_URL`.
  - Chat and contact clients consume this value.

### Backend
- Stack: FastAPI + Uvicorn.
- Core services: RAG pipeline, safety checks, contact/email service.
- Storage model:
  - Vector data on filesystem (`rag/vectorstore`).
  - Session/rate-limit state in memory or local files.
- CORS: Config-driven via `ALLOWED_ORIGINS` in settings.

### External Dependencies
- Groq API: LLM responses.
- Resend API: Contact email delivery.

---

## 2) What Is Already Fixed

These are verified in the current codebase and should be marked as resolved from the previous audit.

### Fixed A: Hardcoded contact localhost URL
- Previous issue: Contact endpoint was hardcoded to localhost.
- Current state:
  - `frontend/utils/contact.js` now uses `window.CONFIG.BACKEND_URL` fallback pattern.
- Result: Production endpoint can be configured centrally.

### Fixed B: Chat endpoint central configuration
- Previous issue: Chat endpoint depended on unsafe direct fallback without shared config.
- Current state:
  - `frontend/utils/chatbot.js` now reads `window.CONFIG.BACKEND_URL`.
- Result: Chat and contact both follow one config source.

### Fixed C: Config script is wired into all pages
- Current state:
  - `frontend/pages/home.html`, `frontend/pages/about.html`, `frontend/pages/projects.html`, `frontend/pages/contact.html` all include `../config.js`.
- Result: Config loading is consistent across site pages.

### Fixed D: Vercel routing and baseline static headers improved
- Current state in `frontend/vercel.json`:
  - Explicit routes for `/`, `/home`, `/about`, `/projects`, `/contact`.
  - Added headers:
    - `X-Content-Type-Options: nosniff`
    - `X-Frame-Options: SAMEORIGIN`
- Result: Better page routing and initial hardening at edge layer.

### Fixed E: Safer default CORS value in settings
- Current state:
  - `backend/config/settings.py` default `ALLOWED_ORIGINS` is now local explicit origins, not wildcard by default.
- Result: Better baseline security posture for local/dev defaults.

---

## 3) Remaining Blockers (Must Resolve Before Production)

## BLOCKER 1 - Runtime backend URL injection is incomplete
Severity: High

Why this is still open:
- `frontend/config.js` expects `window.__ENV__.BACKEND_URL` to be injected by server/runtime.
- No verified mechanism currently exists in this repo to inject `window.__ENV__` during Vercel static deploy.

Failure mode:
- If runtime injection does not occur, frontend falls back to `http://127.0.0.1:8000` and production API calls fail.

What to do:
1. Choose one approach and standardize it:
   - Build-time replacement script for `frontend/config.js`, or
   - A generated `env.js` served with deployment, or
   - Proxy API route under same origin.
2. Add deployment check that fails if production still contains localhost fallback.

## BLOCKER 2 - No production build/minification pipeline
Severity: High

Why this is still open:
- `frontend/package.json` only has `start`/`dev` with `live-server`.
- No `build` script, no minification, no fingerprinting, no artifact step.

Impact:
- Larger payload, weaker caching behavior, less predictable deployment quality.

What to do:
1. Add `npm run build` process.
2. Minify CSS/JS/HTML.
3. Add cache strategy (hashed assets or robust cache-control policy).

## BLOCKER 3 - Backend security headers are still missing
Severity: High

Why this is still open:
- Backend code currently only adds `X-Process-Time` custom header.
- No backend-level `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`, etc.

Impact:
- Incomplete HTTP hardening. Frontend edge headers help, but API responses remain under-protected.

What to do:
1. Add backend middleware for security headers.
2. Ensure reverse proxy/CDN and backend headers are aligned (no policy conflicts).

## BLOCKER 4 - Rate limiting is in-memory only
Severity: High

Why this is still open:
- `backend/routes/contact.py` uses an in-memory dict (`defaultdict(list)`).

Impact:
- Limits reset on restart/redeploy.
- In multi-instance deployment, limits are inconsistent.

What to do:
1. Move to Redis-backed rate limiting.
2. Add IP + route keys and consistent window policy.

## BLOCKER 5 - Session and operational persistence is still ephemeral
Severity: High

Why this is still open:
- App state relies on local filesystem/memory for conversational/session runtime behavior.

Impact:
- State loss on restart.
- Scaling/rolling deploy instability for session continuity.

What to do:
1. Define persistent state strategy (Redis/Postgres/object storage).
2. Keep filesystem only for non-critical cache unless durable volumes are guaranteed.

## BLOCKER 6 - Containerized deployment path is still absent
Severity: Medium-High

Why this is still open:
- No `Dockerfile` or `.dockerignore` found.

Impact:
- Harder to guarantee environment parity and reproducible production builds.

What to do:
1. Add Dockerfile + healthcheck + minimal runtime image.
2. Add .dockerignore for clean build context.

---

## 4) Important To Consider (Not Immediate Blockers, But Critical for Reliability)

### Priority A - Startup diagnostics and fail-fast policy
- Current behavior: Missing `GROQ_API_KEY` fails startup (good).
- Remaining improvement: Missing `RESEND_API_KEY` is warning-only.
- Recommendation:
  - In production mode, decide explicit policy:
    - Fail startup if contact form is mission-critical, or
    - Disable contact route cleanly with explicit health/report status.

### Priority B - Observability and alerts
- Current logging is local-file oriented.
- Recommendation:
  - Add centralized logs, error tracking (e.g., Sentry), and uptime checks.
  - Track p95 latency, error rate, and external API failures.

### Priority C - SEO and metadata completeness
- Pages have basic title/viewport setup.
- Recommendation:
  - Add canonical URL, description, Open Graph, Twitter Card metadata.

### Priority D - Readme consistency
- README still includes claims/config snippets that no longer fully match current deployment posture.
- Recommendation:
  - Align README with actual runtime config flow and deployment steps.

### Priority E - Production mode controls
- Ensure production env enforces:
  - `DEBUG=False`
  - strict CORS allowlist
  - secure cookies/credentials policy (if auth/session evolves)

---

## 5) Updated Readiness Verdict

Current verdict: NOT production-ready yet.

Reason:
- Major improvements were made and are valid.
- However, deployment can still break without robust API URL injection and production build pipeline.
- Security and state durability also remain below production standard.

---

## 6) Recommended 7-Step Finalization Plan

1. Implement one deterministic production API URL injection strategy.
2. Add frontend `build` pipeline (minify + cache strategy).
3. Add backend security-headers middleware.
4. Move rate limiting to Redis.
5. Move session/runtime critical state to durable store.
6. Add Dockerfile/.dockerignore and standard deployment command path.
7. Add monitoring + alerting and run pre-deploy smoke checks.

---

## 7) Quick Smoke Checks Before Go-Live

Use these as release gates:

1. Frontend never references localhost in built assets.
2. Chat endpoint works from production frontend origin.
3. Contact endpoint respects rate limit across restarts.
4. Health endpoint confirms external API readiness.
5. Security headers are present on both frontend and backend responses.
6. App restart does not lose critical operational state unexpectedly.

---

## 8) Summary Table (Delta from Previous Audit)

| Area | Previous Status | Current Status | Decision |
|------|------------------|----------------|----------|
| Contact URL hardcoded | Blocker | Fixed via `window.CONFIG` | Closed |
| Chat URL config | Risky fallback only | Uses `window.CONFIG` | Improved |
| Config inclusion across pages | Missing | Added on all main pages | Closed |
| Vercel routing | Weak/inconsistent | Explicit clean routes added | Closed |
| Frontend security headers | Missing | `nosniff` + `SAMEORIGIN` added | Partially Closed |
| CORS default wildcard | High risk default | Explicit local defaults | Improved |
| Runtime env injection guarantee | Missing | Still not guaranteed | Open Blocker |
| Build optimization pipeline | Missing | Still missing | Open Blocker |
| Backend security headers | Missing | Still missing | Open Blocker |
| Persistent rate/session state | Missing | Still missing | Open Blocker |
| Containerization | Missing | Still missing | Open Blocker |

---

This file is now aligned to your current state: what you already fixed is acknowledged, what remains is explicit, and what matters most before deployment is prioritized.
