# -*- coding: utf-8 -*-
"""
Tests des règles métier Merise / Barrel (api.services.merise_rules).
Vérifie les validations : 1,1+rubriques, table de correspondance, doublons rubriques,
type rubrique manquant, entité avec au moins une association.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from api.services.merise_rules import (
    validate_mcd,
    validate_cardinality_1_1_no_attributes,
    validate_association_with_attributes_must_be_n_n,
    validate_attribute_names_no_duplicates,
    validate_attribute_type_present,
    validate_entity_has_at_least_one_association,
    normalize_cardinality,
)


def test_validate_mcd_empty_ok():
    """MCD vide (pas d'entité) : pas d'erreur entité sans association."""
    errors = validate_mcd(entities=[], associations=[], association_links=[], inheritance_links=[])
    assert isinstance(errors, list)


def test_validate_entity_has_at_least_one_association():
    """Entité non reliée à aucune association → erreur Barrel."""
    entities = [{"name": "Client", "attributes": [{"name": "id", "type": "INT"}]}]
    associations = [{"name": "Achete", "attributes": []}]
    links = []  # aucune liaison
    errors = validate_entity_has_at_least_one_association(entities, links)
    assert any("nécessite au moins une association" in e and "Client" in e for e in errors)


def test_validate_entity_has_at_least_one_association_linked_ok():
    """Entité reliée → pas d'erreur."""
    entities = [{"name": "Client", "attributes": []}]
    links = [{"association": "Achete", "entity": "Client", "card_entity": "1,1", "card_assoc": "0,n"}]
    errors = validate_entity_has_at_least_one_association(entities, links)
    assert not any("Client" in e for e in errors)


def test_validate_attribute_type_present():
    """Rubrique sans type → erreur Barrel."""
    entities = [{"name": "E1", "attributes": [{"name": "a1", "type": ""}]}]
    errors = validate_attribute_type_present(entities, [])
    assert any("Type de la rubrique manquant" in e for e in errors)


def test_validate_attribute_type_present_ok():
    """Rubrique avec type → pas d'erreur."""
    entities = [{"name": "E1", "attributes": [{"name": "a1", "type": "VARCHAR(255)"}]}]
    errors = validate_attribute_type_present(entities, [])
    assert not errors


def test_validate_attribute_names_no_duplicates():
    """Doublons dans les rubriques → erreur Barrel."""
    entities = [{"name": "E1", "attributes": [{"name": "x", "type": "INT"}, {"name": "x", "type": "INT"}]}]
    errors = validate_attribute_names_no_duplicates(entities, [])
    assert any("doublons" in e and "rubriques" in e for e in errors)


def test_validate_attribute_names_no_duplicates_ok():
    """Pas de doublons → pas d'erreur."""
    entities = [{"name": "E1", "attributes": [{"name": "a", "type": "INT"}, {"name": "b", "type": "INT"}]}]
    errors = validate_attribute_names_no_duplicates(entities, [])
    assert not errors


def test_validate_cardinality_1_1_no_attributes():
    """Association porteuse de rubriques avec lien 1,1 côté assoc → erreur."""
    associations = [{"name": "Liaison", "attributes": [{"name": "qte", "type": "INT"}]}]
    links = [{"association": "Liaison", "entity": "E1", "card_entity": "1,n", "card_assoc": "1,1"}]
    errors = validate_cardinality_1_1_no_attributes(associations, links)
    assert any("1,1" in e and "rubriques" in e for e in errors)


def test_validate_association_with_attributes_must_be_n_n():
    """Association avec attributs mais pas n-n (ex. un seul lien 1,n-0,1) → erreur."""
    associations = [{"name": "Liaison", "attributes": [{"name": "qte", "type": "INT"}]}]
    # Un seul lien : pas "table de correspondance" (il en faut au moins 2 en n-n)
    links = [{"association": "Liaison", "entity": "E1", "card_entity": "1,n", "card_assoc": "0,n"}]
    errors = validate_association_with_attributes_must_be_n_n(associations, links)
    assert any("table de correspondance" in e or "porteuses de rubriques" in e for e in errors)


def test_validate_association_with_attributes_n_n_ok():
    """Association n-n avec attributs → pas d'erreur (table de correspondance)."""
    associations = [{"name": "Liaison", "attributes": [{"name": "qte", "type": "INT"}]}]
    links = [
        {"association": "Liaison", "entity": "E1", "card_entity": "1,n", "card_assoc": "0,n"},
        {"association": "Liaison", "entity": "E2", "card_entity": "1,n", "card_assoc": "0,n"},
    ]
    errors = validate_association_with_attributes_must_be_n_n(associations, links)
    assert not errors


def test_validate_mcd_full_barrel_rules():
    """Validation MCD complète : entité sans lien + doublon rubrique + type manquant."""
    mcd = {
        "entities": [
            {"name": "Client", "attributes": [{"name": "id", "type": "INT"}, {"name": "id", "type": "INT"}]},
            {"name": "Produit", "attributes": [{"name": "nom", "type": ""}]},
            {"name": "Orpheline", "attributes": []},
        ],
        "associations": [{"name": "Achete", "attributes": []}],
        "association_links": [
            {"association": "Achete", "entity": "Client", "card_entity": "1,1", "card_assoc": "0,n"},
            {"association": "Achete", "entity": "Produit", "card_entity": "1,n", "card_assoc": "0,n"},
        ],
        "inheritance_links": [],
    }
    errors = validate_mcd(
        entities=mcd["entities"],
        associations=mcd["associations"],
        association_links=mcd["association_links"],
        inheritance_links=mcd["inheritance_links"],
    )
    assert any("doublons" in e for e in errors)
    assert any("Type de la rubrique manquant" in e for e in errors)
    assert any("Orpheline" in e and "au moins une association" in e for e in errors)
