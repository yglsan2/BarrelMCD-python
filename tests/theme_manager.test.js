import { themeManager } from '../dist/js/theme_manager.min.js';

describe('ThemeManager', () => {
    beforeEach(() => {
        localStorage.clear();
        document.body.className = '';
        themeManager.init();
    });

    test('initialisation du gestionnaire', () => {
        expect(document.body.className).toBe('dark-theme');
    });

    test('changement de thème', () => {
        themeManager.toggleTheme();
        expect(document.body.className).toBe('light-theme');
        
        themeManager.toggleTheme();
        expect(document.body.className).toBe('dark-theme');
    });

    test('persistance du thème', () => {
        themeManager.toggleTheme();
        expect(localStorage.getItem('theme')).toBe('light-theme');
        
        themeManager.toggleTheme();
        expect(localStorage.getItem('theme')).toBe('dark-theme');
    });

    test('chargement du thème sauvegardé', () => {
        localStorage.setItem('theme', 'light-theme');
        themeManager.init();
        expect(document.body.className).toBe('light-theme');
    });

    test('couleurs des modèles en mode sombre', () => {
        expect(themeManager.getModelColor('mcd')).toBe('#6a1b9a');
        expect(themeManager.getModelColor('uml')).toBe('#2b73b9');
        expect(themeManager.getModelColor('mld')).toBe('#f6a316');
        expect(themeManager.getModelColor('mpd')).toBe('#43a047');
        expect(themeManager.getModelColor('sql')).toBe('#e53935');
    });

    test('couleurs des modèles en mode clair', () => {
        themeManager.toggleTheme();
        expect(themeManager.getModelColor('mcd')).toBe('#6a1b9a');
        expect(themeManager.getModelColor('uml')).toBe('#2b73b9');
        expect(themeManager.getModelColor('mld')).toBe('#f6a316');
        expect(themeManager.getModelColor('mpd')).toBe('#43a047');
        expect(themeManager.getModelColor('sql')).toBe('#e53935');
    });
}); 