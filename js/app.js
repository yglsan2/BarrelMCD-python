import { themeManager } from './theme_manager.js';
import { entityManager } from '../dist/js/entity_manager.min.js';
import { relationshipManager } from '../dist/js/relationship_manager.min.js';

class BarrelApp {
    constructor() {
        this.currentModel = 'mcd';
        this.gridVisible = true;
        this.init();
    }

    init() {
        // Initialiser les gestionnaires
        themeManager.init();
        entityManager.init();
        relationshipManager.init();
        
        // Initialiser les écouteurs d'événements
        this.initializeEventListeners();
        
        // Initialiser la grille
        this.initializeGrid();
    }

    initializeEventListeners() {
        // Gestion des boutons de modèle
        const modelButtons = document.querySelectorAll('.model-btn');
        modelButtons.forEach(button => {
            button.addEventListener('click', () => this.handleModelChange(button.dataset.model));
        });

        // Gestion du bouton de grille
        const gridToggle = document.getElementById('grid-toggle');
        if (gridToggle) {
            gridToggle.addEventListener('click', () => this.toggleGrid());
        }

        // Gestion du drag & drop pour les entités
        const entities = document.querySelectorAll('.entity');
        entities.forEach(entity => {
            entity.setAttribute('draggable', 'true');
            entity.addEventListener('dragstart', (e) => this.handleDragStart(e));
        });

        const diagramArea = document.querySelector('.diagram-area');
        if (diagramArea) {
            diagramArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            diagramArea.addEventListener('drop', (e) => this.handleDrop(e));
        }
    }

    initializeGrid() {
        const diagramArea = document.querySelector('.diagram-area');
        if (diagramArea) {
            if (this.gridVisible) {
                diagramArea.classList.add('show-grid');
            } else {
                diagramArea.classList.remove('show-grid');
            }
        }
    }

    handleModelChange(modelType) {
        this.currentModel = modelType;
        
        // Mettre à jour les boutons actifs
        document.querySelectorAll('.model-btn').forEach(button => {
            button.classList.toggle('active', button.dataset.model === modelType);
        });
    }

    toggleGrid() {
        this.gridVisible = !this.gridVisible;
        this.initializeGrid();
    }

    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.dataset.type);
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    }

    handleDrop(e) {
        e.preventDefault();
        const entityType = e.dataTransfer.getData('text/plain');
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        this.createEntity(entityType, x, y);
    }

    createEntity(type, x, y) {
        const entity = entityManager.createEntity(type, x, y);
        
        // Créer l'élément visuel
        const entityElement = document.createElement('div');
        entityElement.className = 'entity-diagram';
        entityElement.dataset.id = entity.id;
        entityElement.style.left = `${x}px`;
        entityElement.style.top = `${y}px`;
        
        const title = document.createElement('div');
        title.className = 'entity-title';
        title.textContent = type;
        
        entityElement.appendChild(title);
        document.querySelector('.diagram-area').appendChild(entityElement);
    }
}

// Initialiser l'application quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.barrelApp = new BarrelApp();
}); 