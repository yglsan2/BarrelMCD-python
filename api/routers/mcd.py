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


class ValidateCreateAssociationRequest(BaseModel):
    mcd: Dict[str, Any]
    name: str


class ValidateAddLinkRequest(BaseModel):
    mcd: Dict[str, Any]
    association_name: str
    entity_name: str
    card_entity: str = "1,n"
    card_assoc: str = "1,n"


class ValidateAssociationAfterUpdateRequest(BaseModel):
    mcd: Dict[str, Any]
    association_name: str
    new_attributes: Optional[List[Dict[str, Any]]] = None


class McdToSqlRequest(BaseModel):
    mcd: Dict[str, Any]
    dbms: str = "mysql"  # mysql | postgresql | sqlite | sqlserver (Barrel)


class McdToMpdRequest(BaseModel):
    mcd: Dict[str, Any]
    dbms: str = "mysql"


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


@router.post("/validate-create-association", response_model=Dict)
def validate_create_association(req: ValidateCreateAssociationRequest):
    """Valide la création d'une association (logique Barrel)."""
    try:
        errors = mcd_service.validate_create_association(req.mcd or {}, req.name)
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-add-link", response_model=Dict)
def validate_add_link(req: ValidateAddLinkRequest):
    """Valide l'ajout d'un lien association–entité (logique Barrel)."""
    try:
        errors = mcd_service.validate_add_link(
            req.mcd or {},
            req.association_name,
            req.entity_name,
            req.card_entity,
            req.card_assoc,
        )
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate-association-after-update", response_model=Dict)
def validate_association_after_update(req: ValidateAssociationAfterUpdateRequest):
    """Valide qu'après mise à jour (ex. ajout d'attributs), l'association reste cohérente (règle Barrel 1,1 + rubriques)."""
    try:
        errors = mcd_service.validate_association_after_update(
            req.mcd or {},
            req.association_name,
            req.new_attributes,
        )
        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-mld", response_model=Dict)
def to_mld(req: McdToMldRequest):
    """Convertit un MCD (format canvas) en MLD."""
    try:
        logger.info("POST /api/to-mld entities=%s associations=%s", len(req.mcd.get("entities") or []), len(req.mcd.get("associations") or []))
        return mcd_service.mcd_to_mld(req.mcd)
    except Exception as e:
        logger.exception("to-mld ERROR: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-mld-text", response_model=Dict)
def to_mld_text(req: McdToMldRequest):
    """Export MLD textuel (format lisible : format lisible)."""
    try:
        text = mcd_service.mcd_to_mld_text(req.mcd)
        return {"mld_text": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-mpd", response_model=Dict)
def to_mpd(req: McdToMpdRequest):
    """Convertit un MCD (format canvas) en MPD (Modèle Physique de Données). dbms: mysql, postgresql, sqlite, sqlserver."""
    logger.info("POST /api/to-mpd dbms=%s", req.dbms)
    try:
        mpd = mcd_service.mcd_to_mpd(req.mcd, dbms=req.dbms)
        return {"mpd": mpd}
    except Exception as e:
        logger.exception("to-mpd ERROR: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/to-sql", response_model=Dict)
def to_sql(req: McdToSqlRequest):
    """Convertit un MCD en script SQL. Retourne sql, sql_original (types non traduits), translations (liste des conversions automatiques)."""
    logger.info("POST /api/to-sql dbms=%s", req.dbms)
    try:
        result = mcd_service.mcd_to_sql(req.mcd, dbms=req.dbms)
        logger.info("to-sql OK (sql length=%s, translations=%s)", len(result.get("sql") or ""), len(result.get("translations") or []))
        return result
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
