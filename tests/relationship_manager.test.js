import { relationshipManager } from '../dist/js/relationship_manager.min.js';
import { entityManager } from '../dist/js/entity_manager.min.js';

describe('RelationshipManager', () => {
    let entity1, entity2;

    beforeEach(() => {
        localStorage.clear();
        entityManager.init();
        relationshipManager.init();
        
        entity1 = entityManager.createEntity('Client', 100, 100);
        entity2 = entityManager.createEntity('Commande', 300, 100);
    });

    test('initialisation du gestionnaire', () => {
        expect(relationshipManager.relationships).toEqual([]);
    });

    test('création d\'une relation', () => {
        const relation = relationshipManager.createRelationship(
            entity1.id,
            entity2.id,
            '1,1',
            '0,n',
            'Commande'
        );

        expect(relation).toEqual({
            id: expect.any(String),
            sourceId: entity1.id,
            targetId: entity2.id,
            sourceCardinality: '1,1',
            targetCardinality: '0,n',
            name: 'Commande'
        });
    });

    test('mise à jour d\'une relation', () => {
        const relation = relationshipManager.createRelationship(
            entity1.id,
            entity2.id,
            '1,1',
            '0,n',
            'Commande'
        );

        relationshipManager.updateRelationship(
            relation.id,
            '0,1',
            '1,n',
            'CommandeClient'
        );

        const updated = relationshipManager.relationships.find(r => r.id === relation.id);
        expect(updated.sourceCardinality).toBe('0,1');
        expect(updated.targetCardinality).toBe('1,n');
        expect(updated.name).toBe('CommandeClient');
    });

    test('suppression d\'une relation', () => {
        const relation = relationshipManager.createRelationship(
            entity1.id,
            entity2.id,
            '1,1',
            '0,n',
            'Commande'
        );

        relationshipManager.deleteRelationship(relation.id);
        expect(relationshipManager.relationships).toEqual([]);
    });

    test('sauvegarde des relations', () => {
        const relation = relationshipManager.createRelationship(
            entity1.id,
            entity2.id,
            '1,1',
            '0,n',
            'Commande'
        );

        relationshipManager.saveRelationships();
        const saved = JSON.parse(localStorage.getItem('relationships'));
        expect(saved).toHaveLength(1);
        expect(saved[0].name).toBe('Commande');
    });

    test('chargement des relations', () => {
        const relation = relationshipManager.createRelationship(
            entity1.id,
            entity2.id,
            '1,1',
            '0,n',
            'Commande'
        );

        relationshipManager.saveRelationships();
        relationshipManager.relationships = [];
        relationshipManager.loadRelationships();
        expect(relationshipManager.relationships).toHaveLength(1);
        expect(relationshipManager.relationships[0].name).toBe('Commande');
    });
}); 