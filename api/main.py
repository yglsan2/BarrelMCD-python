#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API BarrelMCD - Backend pour l'interface Flutter.
Expose la logique MCD/MLD/SQL et le parsing Markdown sans dépendance Qt.
"""

import sys
import os

# Ajouter la racine du projet au path pour importer views/models
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import mcd

app = FastAPI(
    title="BarrelMCD API",
    description="API de modélisation MCD/MLD/SQL pour l'interface Flutter",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev; en prod restreindre à l'origine Flutter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcd.router, prefix="/api", tags=["mcd"])


@app.get("/health")
def health():
    """Santé du serveur."""
    return {"status": "ok", "service": "barrelmcd-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
