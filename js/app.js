import { themeManager } from './theme_manager.js';

class BarrelApp {
    constructor() {
        this.currentModel = 'mcd';
        this.gridVisible = true;
        this.init();
    }

    init() {
        // Initialiser le gestionnaire de thème
        themeManager.init();
        
        // Initialiser les écouteurs d'événements
        this.initializeEventListeners();
        
        // Initialiser la grille
        this.initializeGrid();
    }

    initializeEventListeners() {
        // Gestion des boutons de modèle
        const modelButtons = document.querySelectorAll('.model-button');
        modelButtons.forEach(button => {
            button.addEventListener('click', () => this.handleModelChange(button.dataset.model));
        });

        // Gestion du bouton de grille
        const gridToggle = document.getElementById('grid-toggle');
        if (gridToggle) {
            gridToggle.addEventListener('click', () => this.toggleGrid());
        }

        // Gestion du drag & drop pour les entités
        const diagramArea = document.querySelector('.diagram-area');
        if (diagramArea) {
            diagramArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            diagramArea.addEventListener('drop', (e) => this.handleDrop(e));
        }
    }

    initializeGrid() {
        const diagramArea = document.querySelector('.diagram-area');
        if (diagramArea) {
            diagramArea.style.backgroundImage = this.gridVisible ? 
                'linear-gradient(#2b73b9 1px, transparent 1px), linear-gradient(90deg, #2b73b9 1px, transparent 1px)' : 
                'none';
            diagramArea.style.backgroundSize = '20px 20px';
        }
    }

    handleModelChange(modelType) {
        this.currentModel = modelType;
        document.documentElement.style.setProperty('--model-color', themeManager.getModelColor(modelType));
        
        // Mettre à jour les boutons actifs
        document.querySelectorAll('.model-button').forEach(button => {
            button.classList.toggle('active', button.dataset.model === modelType);
        });
    }

    toggleGrid() {
        this.gridVisible = !this.gridVisible;
        this.initializeGrid();
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
        const entity = document.createElement('div');
        entity.className = 'entity';
        entity.style.left = `${x}px`;
        entity.style.top = `${y}px`;
        
        const title = document.createElement('div');
        title.className = 'entity-title';
        title.textContent = type;
        
        entity.appendChild(title);
        document.querySelector('.diagram-area').appendChild(entity);
    }
}

// Initialiser l'application quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    window.barrelApp = new BarrelApp();
}); 