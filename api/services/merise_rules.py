# -*- coding: utf-8 -*-
"""
Règles métier Merise (MCD / MLD).

Ce module centralise les constantes et règles pour :
- Cardinalités MCD (0,1 | 1,1 | 0,n | 1,n)
- Validation MCD (noms uniques, associations, héritage)
- Passage MCD → MLD (entité → table ; association n-n → table de liaison ; 1-n → clé étrangère)
"""

from typing import Dict, List, Any, Optional, Tuple

# --- Cardinalités MCD Merise (min,max) avec min ∈ {0,1}, max ∈ {1,n} ---
MCD_CARDINALITIES = ("0,1", "1,1", "0,n", "1,n")
MCD_CARDINALITIES_SET = frozenset(MCD_CARDINALITIES)


def normalize_cardinality(c: str) -> str:
    """
    Normalise une cardinalité vers une des 4 valeurs MCD.
    Ex. "1,N" / "n,1" → "1,n". Retourne "1,n" par défaut.
    """
    if not c:
        return "1,n"
    s = str(c).strip().lower()
    if s in MCD_CARDINALITIES_SET:
        return s
    if s in ("n,1", "1,n"):
        return "1,n"
    if s == "n,n":
        return "0,n"
    return "1,n"


def is_valid_cardinality(c: str) -> bool:
    """Vrai si c est une cardinalité MCD valide (après normalisation)."""
    return normalize_cardinality(c) in MCD_CARDINALITIES_SET


# --- Règles de validation MCD ---

def validate_entity_names_unique(entities: List[Dict]) -> List[str]:
    """Erreurs si noms d'entités dupliqués."""
    errors = []
    seen = set()
    for e in entities:
        name = (e.get("name") or "").strip()
        if not name:
            errors.append("Une entité sans nom n'est pas autorisée.")
            continue
        if name in seen:
            errors.append(f"Entité en double : « {name} ».")
        seen.add(name)
    return errors


def validate_association_names_unique(associations: List[Dict]) -> List[str]:
    """Erreurs si noms d'associations dupliqués."""
    errors = []
    seen = set()
    for a in associations:
        name = (a.get("name") or "").strip()
        if not name:
            errors.append("Une association sans nom n'est pas autorisée.")
            continue
        if name in seen:
            errors.append(f"Association en double : « {name} ».")
        seen.add(name)
    return errors


def validate_association_entities(
    associations: List[Dict],
    association_links: Optional[List[Dict]] = None,
    entity_names: Optional[set] = None,
) -> List[str]:
    """
    Vérifie que chaque association relie au moins une entité (réflexive) ou deux entités.
    Si association_links est fourni, on déduit les entités liées depuis les liens.
    """
    errors = []
    entity_names = entity_names or set()

    for a in associations:
        name = a.get("name", "Association")
        entities = list(a.get("entities") or [])
        if not entities and association_links:
            entities = list({
                link["entity"]
                for link in association_links
                if link.get("association") == name
            })

        if not entities:
            errors.append(f"L'association « {name} » ne relie aucune entité.")
        elif len(entities) == 1:
            if entity_names and entities[0] not in entity_names:
                errors.append(f"L'association « {name} » référence l'entité inconnue « {entities[0]} ».")
        else:
            for ent in entities[:2]:
                if entity_names and ent not in entity_names:
                    errors.append(f"L'association « {name} » référence l'entité inconnue « {ent} ».")

    return errors


def validate_cardinalities_on_links(
    association_links: List[Dict],
) -> List[str]:
    """Erreurs si une cardinalité de lien n'est pas une des 4 MCD."""
    errors = []
    for link in association_links:
        card = link.get("cardinality", "1,n")
        if not is_valid_cardinality(card):
            errors.append(f"Cardinalité invalide « {card} » (attendu : 0,1 | 1,1 | 0,n | 1,n).")
    return errors


def validate_inheritance_no_cycle(inheritance_links: List[Dict]) -> List[str]:
    """Erreurs si héritage avec cycle (enfant → … → enfant)."""
    errors = []
    child_to_parent: Dict[str, str] = {}
    for link in inheritance_links:
        child = (link.get("child") or "").strip()
        parent = (link.get("parent") or "").strip()
        if child and parent:
            child_to_parent[child] = parent

    visited = set()
    for start in child_to_parent:
        node = start
        path = []
        while node and node not in visited:
            if node in path:
                errors.append(f"Cycle d'héritage détecté : {' → '.join(path + [node])}.")
                break
            path.append(node)
            visited.add(node)
            node = child_to_parent.get(node)
        visited.clear()

    return errors


def validate_mcd(
    entities: List[Dict],
    associations: List[Dict],
    association_links: Optional[List[Dict]] = None,
    inheritance_links: Optional[List[Dict]] = None,
) -> List[str]:
    """
    Valide un MCD selon les règles Merise.
    Retourne la liste des messages d'erreur (vide si valide).
    """
    association_links = association_links or []
    inheritance_links = inheritance_links or []
    entity_names = {(e.get("name") or "").strip() for e in entities if (e.get("name") or "").strip()}

    errors = []
    errors.extend(validate_entity_names_unique(entities))
    errors.extend(validate_association_names_unique(associations))
    errors.extend(validate_association_entities(
        associations, association_links=association_links, entity_names=entity_names
    ))
    errors.extend(validate_cardinalities_on_links(association_links))
    errors.extend(validate_inheritance_no_cycle(inheritance_links))
    return errors


# --- Règles de passage MCD → MLD (résumé pour cohérence du converter) ---
# - Chaque entité → une table (identifiant = clé primaire).
# - Association 1,n / 0,n : pas de table dédiée ; clé étrangère côté "n" (0,n ou 1,n).
# - Association n-n (1,n–1,n ou 0,n–0,n) : table de liaison avec clés étrangères vers les deux entités.
# - Héritage : selon stratégie (table par classe, une table, etc.).

def get_relation_side_for_fk(card: str) -> str:
    """
    Pour une cardinalité, indique si ce côté porte la clé étrangère en MLD.
    Côté "1" (0,1 ou 1,1) : l'autre côté porte la FK.
    Côté "n" (0,n ou 1,n) : ce côté porte la FK (table de l'entité reçoit la FK).
    Retourne "fk_here" ou "fk_other".
    """
    c = normalize_cardinality(card)
    if c in ("0,1", "1,1"):
        return "fk_other"
    return "fk_here"
