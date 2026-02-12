# -*- coding: utf-8 -*-
"""
Logique métier des associations (inspiration Barrel).

Centralise toutes les règles Barrel pour :
- Création d'une association (nom, unicité, contraintes)
- Ajout d'un lien association–entité (cardinalités, table de correspondance, rubriques)
- Mise à jour d'une association (attributs vs cardinalités 1,1)

Source : analyse du binaire Barrel (messages d'erreur, chaînes).
"""

from typing import Dict, List, Any, Optional, Tuple

from api.services.merise_rules import (
    MCD_CARDINALITIES_SET,
    normalize_cardinality,
    is_valid_cardinality,
)


# --- Constantes Barrel ---
def _entity_names(mcd: Dict) -> set:
    return {(e.get("name") or "").strip() for e in (mcd.get("entities") or []) if (e.get("name") or "").strip()}


def _association_names(mcd: Dict) -> set:
    return {(a.get("name") or "").strip() for a in (mcd.get("associations") or []) if (a.get("name") or "").strip()}


def _get_association(mcd: Dict, name: str) -> Optional[Dict]:
    name = (name or "").strip()
    for a in mcd.get("associations") or []:
        if (a.get("name") or "").strip() == name:
            return a
    return None


def _association_has_attributes(assoc: Dict) -> bool:
    """True si l'association est porteuse de rubriques (Barrel)."""
    attrs = assoc.get("attributes") or []
    return isinstance(attrs, list) and len(attrs) > 0


def _links_for_association(mcd: Dict, association_name: str) -> List[Dict]:
    return [
        link for link in (mcd.get("association_links") or [])
        if (link.get("association") or "").strip() == (association_name or "").strip()
    ]


def _is_table_de_correspondance(mcd: Dict, association_name: str) -> bool:
    """
    Barrel : une association « gérant une table de correspondance » est une association n-n
    (tous les liens ont max = n des deux côtés). Seules ces associations peuvent être
    porteuses de rubriques avec certaines cardinalités.
    """
    links = _links_for_association(mcd, association_name)
    if len(links) < 2:
        return False
    many_cards = ("0,n", "1,n")
    for link in links:
        c_ent = normalize_cardinality(link.get("card_entity", link.get("cardinality", "1,n")))
        c_assoc = normalize_cardinality(link.get("card_assoc", link.get("cardinality", "1,n")))
        if c_ent not in many_cards or c_assoc not in many_cards:
            return False
    return True


# --- Création d'association (Barrel) ---
def validate_create_association(mcd: Dict, name: str) -> List[str]:
    """
    Valide la création d'une nouvelle association (règles Barrel).
    Retourne la liste des erreurs (vide si autorisé).
    """
    errors = []
    trimmed = (name or "").strip()
    if not trimmed:
        errors.append("Le nom de l'association ne peut pas être vide.")
        return errors
    existing = _association_names(mcd)
    if trimmed in existing:
        errors.append(f"Une association nommée « {trimmed} » existe déjà.")
    return errors


# --- Ajout d'un lien association–entité (Barrel) ---
def validate_add_link(
    mcd: Dict,
    association_name: str,
    entity_name: str,
    card_entity: str,
    card_assoc: str,
) -> List[str]:
    """
    Valide l'ajout d'un lien entre une association et une entité (règles Barrel).
    À appeler avant d'ajouter le lien au MCD.
    """
    errors = []
    a = (association_name or "").strip()
    e = (entity_name or "").strip()
    if not a:
        errors.append("Le nom de l'association est requis.")
    if not e:
        errors.append("Le nom de l'entité est requis.")
    if errors:
        return errors

    entity_names = _entity_names(mcd)
    assoc_names = _association_names(mcd)

    if a not in assoc_names:
        errors.append(f"L'association « {a} » n'existe pas.")
    if e not in entity_names:
        errors.append(f"L'entité « {e} » n'existe pas.")

    # Lien doublon
    links = mcd.get("association_links") or []
    if any((l.get("association") or "").strip() == a and (l.get("entity") or "").strip() == e for l in links):
        errors.append(f"Un lien entre l'association « {a} » et l'entité « {e} » existe déjà.")

    # Cardinalités valides (0,1 | 1,1 | 0,n | 1,n)
    c_ent = normalize_cardinality(card_entity or "1,n")
    c_assoc = normalize_cardinality(card_assoc or "1,n")
    if c_ent not in MCD_CARDINALITIES_SET:
        errors.append(f"Cardinalité côté entité invalide (attendu : 0,1 | 1,1 | 0,n | 1,n).")
    if c_assoc not in MCD_CARDINALITIES_SET:
        errors.append(f"Cardinalité côté association invalide (attendu : 0,1 | 1,1 | 0,n | 1,n).")

    # Règle Barrel : la cardinalité 1,1 côté association est interdite lorsque l'association est porteuse de rubriques
    assoc = _get_association(mcd, a)
    if assoc and _association_has_attributes(assoc) and c_assoc == "1,1":
        errors.append(
            "La cardinalité 1,1 côté association est interdite lorsque l'association est porteuse de rubriques."
        )

    # Règle Barrel : une association gérant une table de correspondance ne peut pas avoir certaines cardinalités
    # (interprétation : en n-n, les deux côtés sont many ; si on ajoute un lien 1,1 côté assoc dans une table de corresp., incohérent)
    # Ici on a un seul lien en cours d'ajout ; la « table de correspondance » est déterminée par l'ensemble des liens.
    # Donc pas de blocage supplémentaire à l'ajout d'un lien, sauf la règle 1,1 + rubriques ci-dessus.

    return errors


# --- Mise à jour d'une association (ex. ajout d'attributs) ---
def validate_association_after_update(
    mcd: Dict,
    association_name: str,
    new_attributes: Optional[List[Dict]] = None,
) -> List[str]:
    """
    Après mise à jour d'une association (ex. ajout de rubriques), vérifie les règles Barrel :
    - 1,1 côté association interdit si association porteuse de rubriques
    - Seules les associations n-n (table de correspondance) peuvent être porteuses de rubriques
    """
    errors = []
    a = (association_name or "").strip()
    assoc = _get_association(mcd, a)
    if not assoc:
        return errors
    attrs = new_attributes if new_attributes is not None else (assoc.get("attributes") or [])
    if not (isinstance(attrs, list) and len(attrs) > 0):
        return errors
    # Règle Barrel : seules les associations n-n peuvent avoir des rubriques
    if not _is_table_de_correspondance(mcd, a):
        errors.append(
            "Seules les associations gérant une table de correspondance peuvent être porteuses de rubriques. "
            f"L'association « {a} » doit avoir au moins deux liens avec cardinalités 0,n ou 1,n des deux côtés."
        )
    for link in _links_for_association(mcd, a):
        c_assoc = normalize_cardinality(link.get("card_assoc", link.get("cardinality", "1,n")))
        if c_assoc == "1,1":
            errors.append(
                f"La cardinalité 1,1 côté association est interdite lorsque l'association « {a} » est porteuse de rubriques. "
                "Modifiez les cardinalités des liens ou retirez les attributs de l'association."
            )
            break
    return errors


# --- Résumé des règles Barrel implémentées ---
def get_barrel_association_rules_summary() -> List[str]:
    """Retourne un résumé des règles Barrel appliquées (pour doc / UI)."""
    return [
        "Une association doit avoir un nom non vide et unique.",
        "Un lien associe une association à une entité avec deux cardinalités (côté entité, côté association).",
        "Cardinalités autorisées : 0,1 | 1,1 | 0,n | 1,n.",
        "La cardinalité 1,1 côté association est interdite lorsque l'association est porteuse de rubriques (attributs).",
        "Seules les associations gérant une table de correspondance (n-n) peuvent être porteuses de rubriques.",
        "Pas de doublons dans les rubriques d'une même entité ou association.",
        "Chaque rubrique doit avoir un type.",
        "Chaque entité doit être reliée à au moins une association.",
    ]
