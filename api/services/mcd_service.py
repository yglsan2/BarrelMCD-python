# -*- coding: utf-8 -*-
"""
Service MCD : adapte les données canvas/Flutter au format attendu par
model_converter et expose parse markdown, validate, mcd->mld, mld->sql.
"""

import sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from typing import Dict, List, Any, Optional


def _canvas_mcd_to_converter_format(data: Dict) -> Dict:
    """
    Convertit le format MCD renvoyé par le canvas (ou Flutter)
    vers le format attendu par ModelConverter.
    - entities: list of {name, position, attributes, ...} -> dict name -> {name, attributes}
    - associations: list of {name, entities[], cardinalities{}} -> list of {name, entity1, entity2, cardinality1, cardinality2}
    """
    entities_dict = {}
    for e in data.get("entities", []):
        name = e.get("name", "Sans nom")
        attrs = []
        for a in e.get("attributes", []):
            if isinstance(a, dict):
                attrs.append({
                    "name": a.get("name", ""),
                    "type": a.get("type", "VARCHAR(255)"),
                    "primary_key": a.get("is_primary_key", False),
                    "description": a.get("description", ""),
                })
        entities_dict[name] = {"name": name, "attributes": attrs}

    relations = []
    for a in data.get("associations", []):
        name = a.get("name", "Association")
        entities = a.get("entities", [])
        cardinalities = a.get("cardinalities", {})
        if len(entities) >= 2:
            e1, e2 = entities[0], entities[1]
            relations.append({
                "name": name,
                "entity1": e1,
                "entity2": e2,
                "cardinality1": cardinalities.get(e1, "1,1"),
                "cardinality2": cardinalities.get(e2, "0,n"),
            })
        elif len(entities) == 1:
            relations.append({
                "name": name,
                "entity1": entities[0],
                "entity2": entities[0],
                "cardinality1": "1,1",
                "cardinality2": "0,n",
            })

    # associations au format attendu par _convert_to_mld (liste avec entity1, entity2, etc.)
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


def validate_mcd(mcd_structure: Dict) -> List[str]:
    """
    Valide la structure MCD (format canvas ou format parser).
    Retourne la liste des erreurs.
    """
    from views.markdown_mcd_parser import MarkdownMCDParser
    parser = MarkdownMCDParser()
    # Si format canvas (entities en liste), convertir vers format avec entities dict
    if isinstance(mcd_structure.get("entities"), list):
        mcd_structure = _canvas_mcd_to_converter_format(mcd_structure)
    return parser.validate_mcd(mcd_structure)


def markdown_to_canvas_format(parsed: Dict) -> Dict:
    """
    Convertit le résultat du parser Markdown (entities dict, associations list)
    vers le format canvas/Flutter (entities list, associations avec position).
    """
    entities_list = []
    y = 100
    x = 100
    spacing = 250
    for name, ent in parsed.get("entities", {}).items():
        entities_list.append({
            "name": name,
            "position": {"x": x, "y": y},
            "attributes": ent.get("attributes", []),
            "is_weak": False,
            "parent_entity": ent.get("parent"),
        })
        x += spacing
        if x > 800:
            x = 100
            y += 200

    associations_list = []
    association_links_list = []
    for a in parsed.get("associations", []):
        e1, e2 = a.get("entity1"), a.get("entity2")
        c1, c2 = a.get("cardinality1", "1,1"), a.get("cardinality2", "0,n")
        name = a.get("name", "Association")
        associations_list.append({
            "name": name,
            "position": {"x": 400, "y": 300},
            "attributes": [],
            "entities": [e1, e2],
            "cardinalities": {e1: c1, e2: c2} if e1 and e2 else {},
        })
        if e1:
            association_links_list.append({"association": name, "entity": e1, "cardinality": c1})
        if e2 and e2 != e1:
            association_links_list.append({"association": name, "entity": e2, "cardinality": c2})

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


def mcd_to_sql(canvas_mcd: Dict) -> str:
    """Convertit MCD (format canvas) en script SQL."""
    mld = mcd_to_mld(canvas_mcd)
    return mld_to_sql(mld)


def analyze_data(data: Any, format_type: str = "json") -> Dict:
    """Analyse des données brutes (JSON/CSV) vers MCD."""
    from views.data_analyzer import DataAnalyzer
    analyzer = DataAnalyzer()
    return analyzer.analyze_data(data, format_type=format_type)
