# -*- coding: utf-8 -*-
"""
Contraintes d'intégrité fonctionnelle (CIF) — logique métier sans Qt.
CIF Barrel : CIF, contraintes d'inclusion, inter-associations.
Utilisable par l'API et par le converter (validation MCD + CIF).
"""

from enum import Enum
from typing import List, Dict, Any, Optional

# --- Types CIF (alignés sur models/cif_constraints.py, sans PyQt5) ---
CIF_TYPE_FUNCTIONAL = "functional"
CIF_TYPE_INTER_ASSOCIATION = "inter_association"
CIF_TYPE_UNIQUE = "unique"
CIF_TYPE_EXCLUSION = "exclusion"
CIF_TYPES = (CIF_TYPE_FUNCTIONAL, CIF_TYPE_INTER_ASSOCIATION, CIF_TYPE_UNIQUE, CIF_TYPE_EXCLUSION)


def normalize_cif_constraint(data: Dict) -> Dict:
    """Normalise une contrainte CIF pour l'API (noms de champs, types)."""
    out = {
        "name": (data.get("name") or "").strip() or "CIF",
        "type": data.get("type", CIF_TYPE_FUNCTIONAL),
        "description": (data.get("description") or "").strip(),
        "entities": list(data.get("entities") or []),
        "associations": list(data.get("associations") or []),
        "attributes": list(data.get("attributes") or []),
        "is_enabled": data.get("is_enabled", True),
    }
    if out["type"] not in CIF_TYPES:
        out["type"] = CIF_TYPE_FUNCTIONAL
    return out


def validate_cif_constraint(constraint: Dict) -> List[str]:
    """Valide une contrainte CIF (nom, type, cibles selon le type)."""
    errors = []
    name = (constraint.get("name") or "").strip()
    if not name:
        errors.append("Une CIF doit avoir un nom.")
    t = constraint.get("type", CIF_TYPE_FUNCTIONAL)
    if t == CIF_TYPE_INTER_ASSOCIATION:
        assocs = constraint.get("associations") or []
        if len(assocs) < 2:
            errors.append("Une contrainte inter-associations doit concerner au moins deux associations.")
    return errors


def validate_mcd_with_cif(
    entities: List[Dict],
    associations: List[Dict],
    association_links: List[Dict],
    cif_constraints: Optional[List[Dict]] = None,
) -> List[str]:
    """
    Valide le MCD en prenant en compte les CIF activées.
    Retourne la liste des erreurs (vide si valide).
    """
    errors = []
    cif_constraints = cif_constraints or []
    for c in cif_constraints:
        if not c.get("is_enabled", True):
            continue
        errors.extend(validate_cif_constraint(c))
        t = c.get("type", CIF_TYPE_FUNCTIONAL)
        if t == CIF_TYPE_INTER_ASSOCIATION:
            assocs = c.get("associations") or []
            if len(assocs) < 2:
                errors.append(f"CIF « {c.get('name', '')} » : une contrainte inter-associations concerne au moins deux associations.")
    return errors


def cif_list_to_dict_list(constraints: List[Dict]) -> List[Dict]:
    """Export des CIF pour JSON (déjà en dict)."""
    return [normalize_cif_constraint(c) for c in constraints]


def cif_dict_list_from_canvas(mcd: Dict) -> List[Dict]:
    """Récupère la liste des CIF depuis le MCD canvas (si présent)."""
    return list(mcd.get("cif_constraints") or [])
