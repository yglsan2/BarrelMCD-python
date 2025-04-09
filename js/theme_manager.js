// Charte graphique BarrelMCD
const GRAPHIC_CHARTER = {
    dark: {
        primary: '#121212',      // Fond principal (noir)
        secondary: '#1a1a2e',    // Panneau de travail (bleu très foncé)
        tertiary: '#2d2d44',     // Barre d'outils (bleu foncé)
        accent: '#1a5276',       // Accent (bleu sombre)
        textPrimary: '#ffffff',  // Texte principal (blanc)
        textSecondary: '#b3b3b3',// Texte secondaire (gris clair)
        grid: 'rgba(255, 255, 255, 0.1)', // Grille
        buttonBg: '#2d2d44',     // Fond des boutons
        buttonHover: '#3d3d4d',  // Survol des boutons
        entityBg: '#2a2a3a',     // Fond des entités
        entityBorder: '#3d3d4d', // Bordure des entités
        associationBg: '#1a2a3a',// Fond des associations
        associationBorder: '#2d3d4d' // Bordure des associations
    },
    light: {
        primary: '#ffffff',      // Fond principal (blanc)
        secondary: '#f0f0f0',    // Panneau de travail (gris très clair)
        tertiary: '#1a5276',     // Barre d'outils (bleu sombre)
        accent: '#f6a316',       // Accent (orange)
        textPrimary: '#333333',  // Texte principal (noir)
        textSecondary: '#666666',// Texte secondaire (gris)
        grid: 'rgba(0, 0, 0, 0.15)', // Grille
        buttonBg: '#1a5276',     // Fond des boutons
        buttonHover: '#154360',  // Survol des boutons
        entityBg: '#ffffff',     // Fond des entités
        entityBorder: '#e0e0e0', // Bordure des entités
        associationBg: '#f5f5f5',// Fond des associations
        associationBorder: '#e0e0e0' // Bordure des associations
    }
};

// Couleurs des modèles
const MODEL_COLORS = {
    mcd: '#4caf50',  // Vert
    uml: '#2196f3',  // Bleu
    mld: '#ff9800',  // Orange
    mpd: '#9c27b0',  // Violet
    sql: '#f44336'   // Rouge
};

// Couleurs des attributs
const ATTRIBUTE_COLORS = {
    primary: '#4caf50',  // Vert
    foreign: '#2196f3'   // Bleu
};

export const themeManager = {
    init() {
        // Vérifier si un thème est déjà enregistré
        const savedTheme = localStorage.getItem('barrel-theme');
        if (savedTheme) {
            document.body.className = savedTheme;
        } else {
            // Par défaut, utiliser le thème sombre
            document.body.className = 'dark-theme';
        }

        // Initialiser le bouton de changement de thème
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    },

    toggleTheme() {
        const currentTheme = document.body.className;
        const newTheme = currentTheme === 'dark-theme' ? 'light-theme' : 'dark-theme';
        
        document.body.className = newTheme;
        localStorage.setItem('barrel-theme', newTheme);
    },

    getModelColor(modelType) {
        const theme = document.body.className;
        const colors = {
            'dark-theme': {
                'mcd': '#6a1b9a',
                'uml': '#2b73b9',
                'mld': '#f6a316',
                'mpd': '#4caf50',
                'sql': '#e91e63'
            },
            'light-theme': {
                'mcd': '#2b73b9',
                'uml': '#6a1b9a',
                'mld': '#f6a316',
                'mpd': '#4caf50',
                'sql': '#e91e63'
            }
        };

        return colors[theme][modelType] || colors[theme]['mcd'];
    }
};

// Initialisation du gestionnaire de thèmes
document.addEventListener('DOMContentLoaded', () => {
    themeManager.init();
}); 