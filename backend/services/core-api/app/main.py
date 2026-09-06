"""
core-api — see README.md for scope and R&D doc references.
Phase 2 adds real auth/onboarding/consent endpoints (all under
/internal/*, guarded by app.security.verify_internal_secret — only
Next.js's own server should ever call these, never the browser).
"""
from fastapi import FastAPI

from app.routers import auth, checkins, tiny_actions, users

app = FastAPI(title="core-api", version="0.1.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(checkins.router)
app.include_router(tiny_actions.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "core-api"}
