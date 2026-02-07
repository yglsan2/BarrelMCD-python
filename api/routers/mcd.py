# -*- coding: utf-8 -*-
"""
Routes API MCD : parse markdown, validate, MCD -> MLD -> SQL.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from api.services import mcd_service

router = APIRouter()


class ParseMarkdownRequest(BaseModel):
    content: str


class ValidateMcdRequest(BaseModel):
    mcd: Dict[str, Any]


class McdToMldRequest(BaseModel):
    mcd: Dict[str, Any]


class McdToSqlRequest(BaseModel):
    mcd: Dict[str, Any]


class AnalyzeDataRequest(BaseModel):
    data: Any
    format_type: str = "json"


@router.post("/parse-markdown", response_model=Dict)
def parse_markdown(req: ParseMarkdownRequest):
    """Parse un contenu Markdown et retourne la structure MCD + format canvas pour l'UI."""
    try:
        parsed = mcd_service.parse_markdown(req.content)
        canvas_format = mcd_service.markdown_to_canvas_format(parsed)
        return {
            "parsed": parsed,
            "canvas": canvas_format,
            "precision_score": parsed.get("metadata", {}).get("precision_score", 0.0),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=Dict)
def validate_mcd(req: ValidateMcdRequest):
    """Valide une structure MCD et retourne la liste des erreurs."""
    try:
        errors = mcd_service.validate_mcd(req.mcd)
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-mld", response_model=Dict)
def to_mld(req: McdToMldRequest):
    """Convertit un MCD (format canvas) en MLD."""
    try:
        return mcd_service.mcd_to_mld(req.mcd)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-sql", response_model=Dict)
def to_sql(req: McdToSqlRequest):
    """Convertit un MCD (format canvas) en script SQL."""
    try:
        sql = mcd_service.mcd_to_sql(req.mcd)
        return {"sql": sql}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-data", response_model=Dict)
def analyze_data(req: AnalyzeDataRequest):
    """Analyse des données brutes (JSON/CSV-like) et retourne un MCD."""
    try:
        mcd = mcd_service.analyze_data(req.data, format_type=req.format_type)
        return {"mcd": mcd}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
