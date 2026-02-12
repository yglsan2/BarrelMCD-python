# -*- coding: utf-8 -*-
"""
Règles de gestion — logique métier sans Qt.
Règles métier : règles avec condition, action, possibilité de code SQL.
Utilisable par l'API (CRUD, export doc).
"""

from typing import List, Dict, Any, Optional

# --- Types de règles (alignés sur models/business_rules.py, sans PyQt5) ---
RULE_TYPE_ENTITY = "entity"
RULE_TYPE_ASSOCIATION = "association"
RULE_TYPE_ATTRIBUTE = "attribute"
RULE_TYPE_GLOBAL = "global"
RULE_TYPES = (RULE_TYPE_ENTITY, RULE_TYPE_ASSOCIATION, RULE_TYPE_ATTRIBUTE, RULE_TYPE_GLOBAL)


def normalize_business_rule(data: Dict) -> Dict:
    """Normalise une règle de gestion pour l'API."""
    out = {
        "name": (data.get("name") or "").strip() or "Règle",
        "type": data.get("type", RULE_TYPE_GLOBAL),
        "description": (data.get("description") or "").strip(),
        "target": (data.get("target") or "").strip(),
        "condition": (data.get("condition") or "").strip(),
        "action": (data.get("action") or "").strip(),
        "is_enabled": data.get("is_enabled", True),
        "priority": int(data.get("priority", 0)) if data.get("priority") is not None else 0,
    }
    if out["type"] not in RULE_TYPES:
        out["type"] = RULE_TYPE_GLOBAL
    return out


def validate_business_rule(rule: Dict) -> List[str]:
    """Valide une règle (nom, type)."""
    errors = []
    if not (rule.get("name") or "").strip():
        errors.append("Une règle de gestion doit avoir un nom.")
    return errors


def business_rules_to_documentation(rules: List[Dict]) -> str:
    """Génère une documentation texte des règles (documentation des règles)."""
    lines = ["# Règles de Gestion", ""]
    for r in sorted(rules, key=lambda x: (-x.get("priority", 0), (x.get("name") or ""))):
        if not r.get("is_enabled", True):
            continue
        name = r.get("name", "Sans nom")
        rtype = r.get("type", RULE_TYPE_GLOBAL)
        lines.append(f"## {name} ({rtype})")
        lines.append("")
        if r.get("description"):
            lines.append(f"**Description :** {r['description']}")
            lines.append("")
        if r.get("target"):
            lines.append(f"**Cible :** {r['target']}")
            lines.append("")
        if r.get("condition"):
            lines.append(f"**Condition :** {r['condition']}")
            lines.append("")
        if r.get("action"):
            lines.append(f"**Action :** {r['action']}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def business_rules_from_canvas(mcd: Dict) -> List[Dict]:
    """Récupère les règles depuis le MCD canvas (si présent)."""
    return list(mcd.get("business_rules") or [])
