# -*- coding: utf-8 -*-
"""
Service MCD : adapte les données canvas/Flutter au format attendu par
model_converter et expose parse markdown, validate, mcd->mld, mld->sql.

Logique métier alignée sur les règles Merise (voir api.services.merise_rules).
"""

import sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from typing import Dict, List, Any, Optional

from api.services.merise_rules import (
    normalize_cardinality,
    validate_mcd as merise_validate_mcd,
)


def _canvas_mcd_to_converter_format(data: Dict, exclude_fictive: bool = True) -> Dict:
    """
    Convertit le format MCD renvoyé par le canvas (ou Flutter)
    vers le format attendu par ModelConverter.
    - entities: list of {name, position, attributes, is_fictive, ...} -> dict name -> {name, attributes}
    - Si exclude_fictive: les entités avec is_fictive=True ne sont pas incluses (non générées dans le MLD).
    """
    entities_dict = {}
    for e in data.get("entities", []):
        if exclude_fictive and e.get("is_fictive") is True:
            continue
        name = e.get("name", "Sans nom")
        attrs = []
        for a in e.get("attributes", []):
            if isinstance(a, dict):
                attrs.append({
                    "name": a.get("name", ""),
                    "type": a.get("type", "VARCHAR(255)"),
                    "primary_key": a.get("is_primary_key", a.get("primary_key", False)),
                    "description": a.get("description", ""),
                })
        entities_dict[name] = {"name": name, "attributes": attrs}

    # Construire les relations (uniquement entre entités présentes dans entities_dict)
    relations = []
    for a in data.get("associations", []):
        name = a.get("name", "Association")
        entities = list(a.get("entities") or [])
        cardinalities = dict(a.get("cardinalities") or {})
        if not entities and data.get("association_links"):
            links_to_this = [l for l in data["association_links"] if l.get("association") == name]
            for link in links_to_this:
                ent = link.get("entity")
                if ent and ent not in entities:
                    entities.append(ent)
                if ent:
                    cardinalities[ent] = normalize_cardinality(link.get("cardinality", "1,n"))
        if len(entities) >= 2:
            e1, e2 = entities[0], entities[1]
            if exclude_fictive and (e1 not in entities_dict or e2 not in entities_dict):
                continue
            relations.append({
                "name": name,
                "entity1": e1,
                "entity2": e2,
                "cardinality1": normalize_cardinality(cardinalities.get(e1, "1,1")),
                "cardinality2": normalize_cardinality(cardinalities.get(e2, "0,n")),
            })
        elif len(entities) == 1 and (not exclude_fictive or entities[0] in entities_dict):
            relations.append({
                "name": name,
                "entity1": entities[0],
                "entity2": entities[0],
                "cardinality1": "1,1",
                "cardinality2": "0,n",
            })

    mcd = {
        "entities": entities_dict,
        "associations": relations,
        "inheritance": {},
    }
    for link in data.get("inheritance_links", []):
        child = link.get("child")
        parent = link.get("parent")
        if child and parent:
            mcd["inheritance"][child] = parent

    return mcd


def parse_markdown(content: str) -> Dict[str, Any]:
    """Parse du Markdown vers structure MCD (entités + associations)."""
    from views.markdown_mcd_parser import MarkdownMCDParser
    parser = MarkdownMCDParser(verbose=False)
    return parser.parse_markdown(content)


def parse_mots_codes(content: str) -> Dict[str, Any]:
    """
    Parse un texte « mots codés » (style Mocodo) vers le format canvas.
    Ex. "Client: id, nom" et "Commande, 11 Client, 1N Produit".
    Retourne directement le format canvas (entities, associations, association_links, inheritance_links).
    """
    from api.services.mocodo_style_parser import parse_mots_codes as _parse
    return _parse(content)


def validate_mcd(mcd_structure: Dict) -> List[str]:
    """
    Valide la structure MCD (format canvas) selon les règles Merise uniquement.
    Source unique : api.services.merise_rules (pas de validateur Markdown).
    """
    entities = mcd_structure.get("entities", [])
    associations = mcd_structure.get("associations", [])
    association_links = mcd_structure.get("association_links", [])
    inheritance_links = mcd_structure.get("inheritance_links", [])
    return merise_validate_mcd(
        entities=entities,
        associations=associations,
        association_links=association_links,
        inheritance_links=inheritance_links,
    )


def _normalize_attr_for_canvas(attr: Dict) -> Dict:
    """Format attribut pour Flutter : name, type (string), is_primary_key."""
    name = attr.get("name", "")
    raw_type = attr.get("type", "varchar")
    if isinstance(raw_type, str):
        # Mettre en forme lisible (ex: varchar -> VARCHAR(255))
        t = raw_type.upper()
        if "VARCHAR" in t and "(" not in t:
            t = "VARCHAR(255)"
        elif t in ("INT", "INTEGER"):
            t = "INTEGER"
        typ = t
    else:
        typ = "VARCHAR(255)"
    return {
        "name": name,
        "type": typ,
        "is_primary_key": attr.get("primary_key", attr.get("is_primary_key", False)),
    }


def markdown_to_canvas_format(parsed: Dict) -> Dict:
    """
    Convertit le résultat du parser Markdown (entities dict, associations list)
    vers le format canvas/Flutter (entities list, associations avec position),
    compatible avec loadFromCanvasFormat et affichage façon Looping.
    """
    entities_list = []
    y = 100
    x = 100
    spacing = 250
    for name, ent in parsed.get("entities", {}).items():
        attrs = [_normalize_attr_for_canvas(a) for a in ent.get("attributes", []) if isinstance(a, dict)]
        entities_list.append({
            "name": name,
            "position": {"x": float(x), "y": float(y)},
            "attributes": attrs,
            "is_weak": False,
            "is_fictive": False,
            "parent_entity": ent.get("parent"),
        })
        x += spacing
        if x > 800:
            x = 100
            y += 200

    associations_list = []
    association_links_list = []
    base_y = 300
    for i, a in enumerate(parsed.get("associations", [])):
        e1, e2 = a.get("entity1"), a.get("entity2")
        c1, c2 = normalize_cardinality(a.get("cardinality1", "1,1")), normalize_cardinality(a.get("cardinality2", "0,n"))
        assoc_name = a.get("name", "Association")
        assoc_x = 400 + (i % 3) * 220
        assoc_y = base_y + (i // 3) * 180
        associations_list.append({
            "name": assoc_name,
            "position": {"x": float(assoc_x), "y": float(assoc_y)},
            "attributes": [],
            "entities": [e for e in (e1, e2) if e],
            "cardinalities": {e1: c1, e2: c2} if e1 and e2 else ({(e1 or e2): c1} if e1 or e2 else {}),
        })
        if e1:
            association_links_list.append({"association": assoc_name, "entity": e1, "cardinality": c1})
        if e2 and e2 != e1:
            association_links_list.append({"association": assoc_name, "entity": e2, "cardinality": c2})

    # Normaliser les cardinalités en sortie (règles Merise)
    for link in association_links_list:
        link["cardinality"] = normalize_cardinality(link.get("cardinality", "1,n"))

    return {
        "entities": entities_list,
        "associations": associations_list,
        "inheritance_links": [{"parent": p, "child": c} for c, p in parsed.get("inheritance", {}).items()],
        "association_links": association_links_list,
    }


def mcd_to_mld(canvas_mcd: Dict) -> Dict:
    """Convertit MCD (format canvas) en MLD."""
    from views.model_converter import ModelConverter, ConversionType
    converter = ModelConverter()
    mcd = _canvas_mcd_to_converter_format(canvas_mcd)
    return converter.convert_model(mcd, ConversionType.MCD_TO_MLD)


def mld_to_sql(mld: Dict) -> str:
    """Convertit MLD en script SQL."""
    from views.model_converter import ModelConverter
    converter = ModelConverter()
    return converter._convert_to_sql(mld)


def mcd_to_sql(canvas_mcd: Dict, dbms: str = "mysql") -> str:
    """Convertit MCD (format canvas) en script SQL. dbms: mysql, postgresql, sqlite."""
    from views.model_converter import ModelConverter
    mld = mcd_to_mld(canvas_mcd)
    converter = ModelConverter()
    if dbms in ("mysql", "postgresql", "sqlite"):
        mpd = converter.generate_mpd(mld, dbms=dbms)
        return converter.generate_sql_from_mpd(mpd)
    return mld_to_sql(mld)


def analyze_data(data: Any, format_type: str = "json") -> Dict:
    """Analyse des données brutes (JSON/CSV) vers MCD."""
    from views.data_analyzer import DataAnalyzer
    analyzer = DataAnalyzer()
    return analyzer.analyze_data(data, format_type=format_type)
