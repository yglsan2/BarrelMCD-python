from PyQt6.QtCore import QObject, Qt, QPointF, QRectF, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from .styles import AppStyles
from .error_handler import ErrorHandler

class HelpSystem(QObject):
    """Système d'aide contextuelle et de tutoriels"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialisation du gestionnaire d'erreurs
        self.error_handler = ErrorHandler(self)
        
        self.tooltips = []
        self.highlights = []
        self.current_tutorial = None
        self.tutorial_steps = []
        self.current_step = 0
        self.show_help = True
        
        # Configuration des styles
        try:
            self.tooltip_style = AppStyles.get_ui_style("tooltip")
            self.highlight_style = {
                "color": AppStyles.ACCENT_COLOR,
                "border": AppStyles.SECONDARY_COLOR,
                "border_width": 2
            }
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de l'initialisation des styles"
            )
        
    def show_tooltip(self, text: str, pos: QPointF, target: QGraphicsItem = None, style=None, duration: int = 3000):
        """Affiche une infobulle d'aide"""
        try:
            if not self.show_help:
                return
            
            tooltip = QGraphicsTextItem(text)
            tooltip.setDefaultTextColor(style["text_color"])
            tooltip.setFont(style["font"])
            tooltip.setPos(pos)
            tooltip.setZValue(1000)
            
            # Style de l'infobulle
            tooltip.setBackgroundBrush(QBrush(style["background_color"]))
            tooltip.setPadding(style["padding"])
            
            # Animation d'apparition
            tooltip.setOpacity(0)
            self.parent().scene().addItem(tooltip)
            
            # Animation d'opacité
            animation = QPropertyAnimation(tooltip, b"opacity")
            animation.setDuration(200)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.start()
            
            # Suppression après la durée
            QTimer.singleShot(duration, lambda: self._fade_out_tooltip(tooltip))
            
            self.tooltips.append(tooltip)
            
            # Mise en surbrillance de la cible si spécifiée
            if target:
                self.highlight_item(target)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de l'affichage de l'infobulle"
            )
        
    def highlight_item(self, item: QGraphicsItem, duration: int = 3000):
        """Met en surbrillance un élément"""
        try:
            if not self.show_help:
                return
            
            # Création du rectangle de surbrillance
            highlight = QGraphicsRectItem(item.boundingRect())
            highlight.setPos(item.pos())
            highlight.setZValue(999)
            
            # Style de la surbrillance
            highlight.setPen(QPen(self.highlight_style["border"], self.highlight_style["border_width"]))
            highlight.setBrush(QBrush(self.highlight_style["color"]))
            
            # Animation d'apparition
            highlight.setOpacity(0)
            self.parent().scene().addItem(highlight)
            
            # Animation d'opacité
            animation = QPropertyAnimation(highlight, b"opacity")
            animation.setDuration(200)
            animation.setStartValue(0)
            animation.setEndValue(1)
            animation.start()
            
            # Suppression après la durée
            QTimer.singleShot(duration, lambda: self._fade_out_highlight(highlight))
            
            self.highlights.append(highlight)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la mise en surbrillance"
            )
        
    def start_tutorial(self, tutorial_name: str):
        """Démarre un tutoriel"""
        try:
            self.current_tutorial = tutorial_name
            self.current_step = 0
            self.tutorial_steps = self._get_tutorial_steps(tutorial_name)
            self._show_next_step()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                f"Erreur lors du démarrage du tutoriel : {tutorial_name}"
            )
        
    def _get_tutorial_steps(self, tutorial_name: str) -> list:
        """Retourne les étapes d'un tutoriel"""
        tutorials = {
            "create_entity": [
                {
                    "text": "Pour créer une entité, cliquez sur le bouton 'Nouvelle entité' dans la barre d'outils",
                    "target": "toolbar_new_entity",
                    "action": "wait_for_click"
                },
                {
                    "text": "Choisissez un template prédéfini ou créez une entité personnalisée",
                    "target": "entity_menu",
                    "action": "wait_for_selection"
                },
                {
                    "text": "Cliquez sur le canvas pour placer l'entité",
                    "target": "canvas",
                    "action": "wait_for_click"
                }
            ],
            "create_relation": [
                {
                    "text": "Pour créer une relation, cliquez sur le bouton 'Nouvelle relation'",
                    "target": "toolbar_new_relation",
                    "action": "wait_for_click"
                },
                {
                    "text": "Sélectionnez l'entité source",
                    "target": "canvas",
                    "action": "wait_for_entity_selection"
                },
                {
                    "text": "Sélectionnez l'entité cible",
                    "target": "canvas",
                    "action": "wait_for_entity_selection"
                }
            ],
            "edit_entity": [
                {
                    "text": "Pour modifier une entité, faites un appui long sur celle-ci",
                    "target": "canvas",
                    "action": "wait_for_long_press"
                },
                {
                    "text": "Choisissez l'action souhaitée dans le menu contextuel",
                    "target": "context_menu",
                    "action": "wait_for_selection"
                }
            ]
        }
        return tutorials.get(tutorial_name, [])
        
    def _show_next_step(self):
        """Affiche l'étape suivante du tutoriel"""
        try:
            if self.current_step >= len(self.tutorial_steps):
                self.end_tutorial()
                return
            
            step = self.tutorial_steps[self.current_step]
            self.show_tooltip(step["text"], QPointF(0, 0))
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de l'affichage de l'étape du tutoriel"
            )
        
    def end_tutorial(self):
        """Termine le tutoriel en cours"""
        try:
            self.current_tutorial = None
            self.current_step = 0
            self.tutorial_steps = []
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la fin du tutoriel"
            )
        
    def show_quick_help(self):
        """Affiche l'aide rapide"""
        try:
            help_text = """
            Raccourcis clavier :
            - S : Mode sélection
            - E : Mode entité
            - A : Mode association
            - R : Mode relation
            - Z : Zoom avant
            - X : Zoom arrière
            - F : Ajuster la vue
            - G : Afficher/masquer la grille
            
            Gestes tactiles :
            - Double tap : Zoom avant
            - Appui long : Menu contextuel
            - Pincement : Zoom
            - Glissement : Déplacement
            """
            self.show_tooltip(help_text, QPointF(0, 0), duration=5000)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de l'affichage de l'aide rapide"
            )
        
    def toggle_help(self):
        """Active/désactive l'aide"""
        try:
            self.show_help = not self.show_help
            if not self.show_help:
                self._clear_all_help()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la modification de l'état de l'aide"
            )
        
    def _clear_all_help(self):
        """Supprime tous les éléments d'aide"""
        try:
            for tooltip in self.tooltips:
                self._fade_out_tooltip(tooltip)
            for highlight in self.highlights:
                self._fade_out_highlight(highlight)
            self.tooltips.clear()
            self.highlights.clear()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la suppression des éléments d'aide"
            )
        
    def _fade_out_tooltip(self, tooltip: QGraphicsTextItem):
        """Fait disparaître une infobulle"""
        try:
            animation = QPropertyAnimation(tooltip, b"opacity")
            animation.setDuration(200)
            animation.setStartValue(1)
            animation.setEndValue(0)
            animation.finished.connect(lambda: self._remove_tooltip(tooltip))
            animation.start()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la disparition de l'infobulle"
            )
        
    def _fade_out_highlight(self, highlight: QGraphicsRectItem):
        """Fait disparaître une surbrillance"""
        try:
            animation = QPropertyAnimation(highlight, b"opacity")
            animation.setDuration(200)
            animation.setStartValue(1)
            animation.setEndValue(0)
            animation.finished.connect(lambda: self._remove_highlight(highlight))
            animation.start()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la disparition de la surbrillance"
            )
        
    def _remove_tooltip(self, tooltip: QGraphicsTextItem):
        """Supprime une infobulle"""
        try:
            if tooltip in self.tooltips:
                self.tooltips.remove(tooltip)
                self.parent().scene().removeItem(tooltip)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la suppression de l'infobulle"
            )
        
    def _remove_highlight(self, highlight: QGraphicsRectItem):
        """Supprime une surbrillance"""
        try:
            if highlight in self.highlights:
                self.highlights.remove(highlight)
                self.parent().scene().removeItem(highlight)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la suppression de la surbrillance"
            ) 