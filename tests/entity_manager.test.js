import { entityManager } from '../dist/js/entity_manager.min.js';

describe('EntityManager', () => {
    beforeEach(() => {
        localStorage.clear();
        entityManager.init();
    });

    test('initialisation du gestionnaire', () => {
        expect(entityManager.entities).toEqual([]);
    });

    test('création d\'une entité', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        expect(entity).toEqual({
            id: expect.any(String),
            name: 'Client',
            x: 100,
            y: 100,
            attributes: []
        });
    });

    test('ajout d\'un attribut', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        const attribute = entityManager.addAttribute(entity.id, 'id', 'int', true);
        expect(attribute).toEqual({
            id: expect.any(String),
            name: 'id',
            type: 'int',
            isPrimary: true
        });
    });

    test('déplacement d\'une entité', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        entityManager.moveEntity(entity.id, 200, 200);
        const updatedEntity = entityManager.entities.find(e => e.id === entity.id);
        expect(updatedEntity.x).toBe(200);
        expect(updatedEntity.y).toBe(200);
    });

    test('suppression d\'une entité', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        entityManager.deleteEntity(entity.id);
        expect(entityManager.entities).toEqual([]);
    });

    test('sauvegarde des entités', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        entityManager.addAttribute(entity.id, 'id', 'int', true);
        entityManager.saveEntities();
        const saved = JSON.parse(localStorage.getItem('entities'));
        expect(saved).toHaveLength(1);
        expect(saved[0].attributes).toHaveLength(1);
    });

    test('chargement des entités', () => {
        const entity = entityManager.createEntity('Client', 100, 100);
        entityManager.addAttribute(entity.id, 'id', 'int', true);
        entityManager.saveEntities();
        entityManager.entities = [];
        entityManager.loadEntities();
        expect(entityManager.entities).toHaveLength(1);
        expect(entityManager.entities[0].attributes).toHaveLength(1);
    });
}); 