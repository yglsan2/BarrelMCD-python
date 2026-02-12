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
    """Erreurs si une cardinalité de lien n'est pas une des 4 MCD (côté entité et/ou association)."""
    errors = []
    for link in association_links:
        card_entity = link.get("card_entity", link.get("cardinality", "1,n"))
        card_assoc = link.get("card_assoc", link.get("cardinality", "1,n"))
        bad_entity = not is_valid_cardinality(card_entity)
        bad_assoc = not is_valid_cardinality(card_assoc)
        if bad_entity and bad_assoc and card_entity == card_assoc:
            errors.append(f"Cardinalité invalide « {card_entity} » (attendu : 0,1 | 1,1 | 0,n | 1,n).")
        else:
            if bad_entity:
                errors.append(f"Cardinalité côté entité invalide « {card_entity} » (attendu : 0,1 | 1,1 | 0,n | 1,n).")
            if bad_assoc:
                errors.append(f"Cardinalité côté association invalide « {card_assoc} » (attendu : 0,1 | 1,1 | 0,n | 1,n).")
    return errors


def validate_cardinality_1_1_no_attributes(
    associations: List[Dict],
    association_links: List[Dict],
) -> List[str]:
    """
    Règle Barrel : la cardinalité 1,1 côté association est interdite lorsque l'association est porteuse de rubriques.
    Une association avec des attributs ne peut pas avoir de lien en 1,1 côté association.
    """
    errors = []
    assoc_with_attrs = set()
    for a in associations:
        name = (a.get("name") or "").strip()
        if not name:
            continue
        attrs = a.get("attributes") or []
        if isinstance(attrs, list) and len(attrs) > 0:
            assoc_with_attrs.add(name)
    for link in association_links:
        assoc_name = (link.get("association") or "").strip()
        card_assoc = normalize_cardinality(link.get("card_assoc", link.get("cardinality", "1,n")))
        if assoc_name in assoc_with_attrs and card_assoc == "1,1":
            errors.append(
                f"La cardinalité 1,1 côté association est interdite lorsque l'association « {assoc_name} » est porteuse de rubriques (attributs)."
            )
    return errors


def _association_is_table_correspondance(association_name: str, association_links: List[Dict]) -> bool:
    """True si l'association est n-n (tous les liens ont max = n des deux côtés)."""
    links = [l for l in association_links if (l.get("association") or "").strip() == (association_name or "").strip()]
    if len(links) < 2:
        return False
    many_cards = ("0,n", "1,n")
    for link in links:
        c_ent = normalize_cardinality(link.get("card_entity", link.get("cardinality", "1,n")))
        c_assoc = normalize_cardinality(link.get("card_assoc", link.get("cardinality", "1,n")))
        if c_ent not in many_cards or c_assoc not in many_cards:
            return False
    return True


def validate_association_with_attributes_must_be_n_n(
    associations: List[Dict],
    association_links: List[Dict],
) -> List[str]:
    """
    Règle Barrel : seules les associations gérant une table de correspondance (n-n) peuvent être porteuses de rubriques.
    Si une association a des attributs, tous ses liens doivent être en 0,n ou 1,n des deux côtés.
    """
    errors = []
    for a in associations:
        name = (a.get("name") or "").strip()
        if not name:
            continue
        attrs = a.get("attributes") or []
        if not (isinstance(attrs, list) and len(attrs) > 0):
            continue
        if not _association_is_table_correspondance(name, association_links):
            errors.append(
                f"Seules les associations gérant une table de correspondance peuvent être porteuses de rubriques. "
                f"L'association « {name} » a des attributs mais n'est pas n-n (ou n'a pas au moins deux liens en 0,n ou 1,n)."
            )
    return errors


def validate_attribute_names_no_duplicates(
    entities: List[Dict],
    associations: List[Dict],
) -> List[str]:
    """
    Règle Barrel : il ne doit pas y avoir de doublons dans les rubriques (attributs) d'une même entité ou association.
    """
    errors = []
    for e in entities:
        name = (e.get("name") or "").strip() or "Entité"
        attrs = e.get("attributes") or []
        if not isinstance(attrs, list):
            continue
        names = []
        for a in attrs:
            n = (a.get("name") or "").strip() if isinstance(a, dict) else ""
            if n:
                names.append(n)
        if len(names) != len(set(names)):
            seen = set()
            for n in names:
                if n in seen:
                    errors.append(f"Il existe des doublons dans les rubriques de l'entité « {name} ».")
                    break
                seen.add(n)
    for a in associations:
        name = (a.get("name") or "").strip() or "Association"
        attrs = a.get("attributes") or []
        if not isinstance(attrs, list):
            continue
        names = []
        for x in attrs:
            n = (x.get("name") or "").strip() if isinstance(x, dict) else ""
            if n:
                names.append(n)
        if len(names) != len(set(names)):
            seen = set()
            for n in names:
                if n in seen:
                    errors.append(f"Il existe des doublons dans les rubriques de l'association « {name} ».")
                    break
                seen.add(n)
    return errors


def validate_attribute_type_present(
    entities: List[Dict],
    associations: List[Dict],
) -> List[str]:
    """
    Règle Barrel : chaque rubrique (attribut) doit avoir un type.
    """
    errors = []
    for e in entities:
        name = (e.get("name") or "").strip() or "Entité"
        for i, a in enumerate(e.get("attributes") or []):
            if not isinstance(a, dict):
                continue
            attr_name = (a.get("name") or "").strip()
            if not attr_name:
                continue
            if not (a.get("type") or "").strip():
                errors.append(f"Type de la rubrique manquant : « {attr_name} » dans l'entité « {name} ».")
    for a in associations:
        name = (a.get("name") or "").strip() or "Association"
        for x in a.get("attributes") or []:
            if not isinstance(x, dict):
                continue
            attr_name = (x.get("name") or "").strip()
            if not attr_name:
                continue
            if not (x.get("type") or "").strip():
                errors.append(f"Type de la rubrique manquant : « {attr_name} » dans l'association « {name} ».")
    return errors


def validate_entity_has_at_least_one_association(
    entities: List[Dict],
    association_links: List[Dict],
) -> List[str]:
    """
    Règle Barrel : chaque entité doit être reliée à au moins une association (l'entité nécessite au moins une association).
    """
    errors = []
    entity_names = {(e.get("name") or "").strip() for e in entities if (e.get("name") or "").strip()}
    linked_entities = { (link.get("entity") or "").strip() for link in association_links if (link.get("entity") or "").strip() }
    for name in entity_names:
        if name not in linked_entities:
            errors.append(f"L'entité « {name} » nécessite au moins une association.")
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
    errors.extend(validate_cardinality_1_1_no_attributes(associations, association_links))
    errors.extend(validate_association_with_attributes_must_be_n_n(associations, association_links))
    errors.extend(validate_attribute_names_no_duplicates(entities, associations))
    errors.extend(validate_attribute_type_present(entities, associations))
    errors.extend(validate_entity_has_at_least_one_association(entities, association_links))
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
