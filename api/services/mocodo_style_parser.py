# -*- coding: utf-8 -*-
"""
Parser « mots codés » style Mocodo : texte minimaliste → MCD (format canvas).

Réinterprétation de la logique Mocodo (grammaire entités/associations, cardinalités 11/1N/01/0N).
Aucun code copié ; sortie compatible avec le format canvas Flutter (entities, associations, association_links).
"""

import re
from typing import Dict, List, Any, Tuple

from api.services.merise_rules import normalize_cardinality

# Cardinalités Mocodo → Merise
_MOCODO_TO_MERISE = {
    "11": "1,1",
    "1n": "1,n",
    "0n": "0,n",
    "01": "0,1",
}


def _parse_cardinality(s: str) -> str:
    """Normalise une chaîne type 11, 1N, 0n, 01 vers 1,1 | 1,n | 0,n | 0,1."""
    t = (s or "").strip().lower()
    return _MOCODO_TO_MERISE.get(t) or normalize_cardinality(t)


def parse_mots_codes(content: str) -> Dict[str, Any]:
    """
    Parse un texte « mots codés » :
    - Lignes "NomEntité: attr1, attr2" → entité avec attributs
    - Lignes "NomAssoc, 11 Entité1, 1N Entité2" → association avec cardinalités

    Retourne le format canvas : entities, associations, association_links, inheritance_links.
    """
    entities_by_name: Dict[str, Dict] = {}
    associations_raw: List[Tuple[str, List[Tuple[str, str]]]] = []  # (assoc_name, [(card, entity_name), ...])
    entity_order: List[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Entité : Nom: attr1, attr2
        if ":" in line:
            name_part, rest = line.split(":", 1)
            name = name_part.strip()
            if not name:
                continue
            attrs = [a.strip() for a in rest.split(",") if a.strip()]
            if name not in entities_by_name:
                entity_order.append(name)
            entities_by_name[name] = {
                "name": name,
                "attributes": [{"name": a, "type": "VARCHAR(255)", "is_primary_key": False} for a in attrs],
            }
            continue

        # Association : NomAssoc, 11 E1, 1N E2
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) < 2:
            continue
        assoc_name = parts[0]
        card_entity_pairs: List[Tuple[str, str]] = []
        card_re = re.compile(r"^(11|1n|0n|01)\s+(.+)$", re.IGNORECASE)
        for p in parts[1:]:
            m = card_re.match(p)
            if m:
                card, ent = m.group(1), m.group(2).strip()
                card_entity_pairs.append((_parse_cardinality(card), ent))
            else:
                card_entity_pairs.append((normalize_cardinality("1,n"), p))
        if card_entity_pairs:
            associations_raw.append((assoc_name, card_entity_pairs))

    # Construire le format canvas
    spacing = 250
    x, y = 100.0, 100.0
    entities_list: List[Dict] = []
    for name in entity_order:
        ent = entities_by_name.get(name, {})
        attrs = [
            {
                "name": a.get("name", ""),
                "type": a.get("type", "VARCHAR(255)"),
                "is_primary_key": a.get("is_primary_key", False),
            }
            for a in ent.get("attributes", [])
        ]
        entities_list.append({
            "name": name,
            "position": {"x": x, "y": y},
            "attributes": attrs,
            "is_weak": False,
            "is_fictive": False,
            "parent_entity": ent.get("parent_entity"),
        })
        x += spacing
        if x > 800:
            x = 100
            y += 200

    base_y = 300
    associations_list: List[Dict] = []
    association_links_list: List[Dict] = []
    for i, (assoc_name, card_entity_pairs) in enumerate(associations_raw):
        entities_in_assoc = [e for _, e in card_entity_pairs]
        cardinalities = {e: _parse_cardinality(c) for c, e in card_entity_pairs}
        assoc_x = 400 + (i % 3) * 220
        assoc_y = base_y + (i // 3) * 180
        associations_list.append({
            "name": assoc_name,
            "position": {"x": assoc_x, "y": assoc_y},
            "attributes": [],
            "entities": entities_in_assoc,
            "cardinalities": {e: normalize_cardinality(cardinalities.get(e, "1,n")) for e in entities_in_assoc},
        })
        for ent in entities_in_assoc:
            association_links_list.append({
                "association": assoc_name,
                "entity": ent,
                "cardinality": normalize_cardinality(cardinalities.get(ent, "1,n")),
            })

    return {
        "entities": entities_list,
        "associations": associations_list,
        "association_links": association_links_list,
        "inheritance_links": [],
    }
