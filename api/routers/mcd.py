# -*- coding: utf-8 -*-
"""
Routes API MCD : parse markdown, validate, MCD -> MLD -> SQL.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from api.services import mcd_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ParseMarkdownRequest(BaseModel):
    content: str


class ParseMotsCodesRequest(BaseModel):
    content: str


class ValidateMcdRequest(BaseModel):
    mcd: Dict[str, Any]


class McdToMldRequest(BaseModel):
    mcd: Dict[str, Any]


class McdToSqlRequest(BaseModel):
    mcd: Dict[str, Any]
    dbms: str = "mysql"  # mysql | postgresql | sqlite


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


@router.post("/parse-mots-codes", response_model=Dict)
def parse_mots_codes(req: ParseMotsCodesRequest):
    """Parse un texte « mots codés » (style Mocodo) et retourne le format canvas pour l'UI."""
    logger.info("POST /api/parse-mots-codes (content length=%s)", len(req.content or ""))
    try:
        canvas_format = mcd_service.parse_mots_codes(req.content)
        logger.info("parse-mots-codes OK: %s entities", len(canvas_format.get("entities") or []))
        return {"canvas": canvas_format}
    except Exception as e:
        logger.exception("parse-mots-codes ERROR: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", response_model=Dict)
def validate_mcd(req: ValidateMcdRequest):
    """Valide une structure MCD et retourne la liste des erreurs."""
    logger.info("POST /api/validate (mcd keys=%s)", list((req.mcd or {}).keys()))
    try:
        errors = mcd_service.validate_mcd(req.mcd)
        logger.info("validate OK: valid=%s errors=%s", len(errors) == 0, len(errors))
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        logger.exception("validate ERROR: %s", e)
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
    """Convertit un MCD (format canvas) en script SQL. dbms: mysql, postgresql, sqlite."""
    logger.info("POST /api/to-sql dbms=%s", req.dbms)
    try:
        sql = mcd_service.mcd_to_sql(req.mcd, dbms=req.dbms)
        logger.info("to-sql OK (sql length=%s)", len(sql or ""))
        return {"sql": sql}
    except Exception as e:
        logger.exception("to-sql ERROR: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-data", response_model=Dict)
def analyze_data(req: AnalyzeDataRequest):
    """Analyse des données brutes (JSON/CSV-like) et retourne un MCD."""
    logger.info("POST /api/analyze-data format_type=%s", req.format_type)
    try:
        mcd = mcd_service.analyze_data(req.data, format_type=req.format_type)
        logger.info("analyze-data OK")
        return {"mcd": mcd}
    except Exception as e:
        logger.exception("analyze-data ERROR: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
