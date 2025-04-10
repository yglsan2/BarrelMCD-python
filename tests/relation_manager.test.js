import { relationManager } from '../dist/js/relation_manager.min.js';

describe('RelationManager', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="workspace"></div>
            <div id="relation-list"></div>
        `;
        localStorage.clear();
        relationManager.init();
    });

    test('initialisation du gestionnaire', () => {
        expect(relationManager.relations).toEqual([]);
    });

    test('création d\'une relation', () => {
        const source = document.createElement('div');
        source.classList.add('entity');
        source.dataset.id = '1';
        source.dataset.name = 'Client';

        const target = document.createElement('div');
        target.classList.add('entity');
        target.dataset.id = '2';
        target.dataset.name = 'Commande';

        const relation = relationManager.createRelation(source, target, '1,n');
        expect(relation).toBeDefined();
        expect(relation.classList.contains('relation')).toBe(true);
        expect(relation.querySelector('.cardinality').textContent).toBe('1,n');
    });

    test('sauvegarde des relations', () => {
        const source = document.createElement('div');
        source.classList.add('entity');
        source.dataset.id = '1';
        source.dataset.name = 'Client';

        const target = document.createElement('div');
        target.classList.add('entity');
        target.dataset.id = '2';
        target.dataset.name = 'Commande';

        relationManager.createRelation(source, target, '1,n');
        relationManager.saveRelations();
        const saved = JSON.parse(localStorage.getItem('relations'));
        expect(saved).toHaveLength(1);
        expect(saved[0].sourceId).toBe('1');
        expect(saved[0].targetId).toBe('2');
    });

    test('chargement des relations', () => {
        const source = document.createElement('div');
        source.classList.add('entity');
        source.dataset.id = '1';
        source.dataset.name = 'Client';

        const target = document.createElement('div');
        target.classList.add('entity');
        target.dataset.id = '2';
        target.dataset.name = 'Commande';

        relationManager.createRelation(source, target, '1,n');
        relationManager.saveRelations();
        relationManager.loadRelations();
        expect(relationManager.relations).toHaveLength(1);
    });

    test('mise à jour de la cardinalité', () => {
        const source = document.createElement('div');
        source.classList.add('entity');
        source.dataset.id = '1';
        source.dataset.name = 'Client';

        const target = document.createElement('div');
        target.classList.add('entity');
        target.dataset.id = '2';
        target.dataset.name = 'Commande';

        const relation = relationManager.createRelation(source, target, '1,n');
        relationManager.updateCardinality(relation, '0,n');
        const saved = JSON.parse(localStorage.getItem('relations'));
        expect(saved[0].cardinality).toBe('0,n');
    });
}); 