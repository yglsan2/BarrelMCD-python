from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFileDialog,
                             QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
                             QDockWidget, QSplitter, QTabWidget, QApplication,
                             QDesktopWidget, QInputDialog, QDialog,
                             QListWidget, QSizePolicy, QScrollArea, QFrame,
                             QStyle, QStyleOptionButton, QLineEdit, QDialogButtonBox,
                             QGraphicsLineItem, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import Qt, QSettings, QSize, QPoint, QTimer, QEvent, QRect, QDateTime, QLineF
from PyQt5.QtGui import QIcon, QFont, QCloseEvent, QResizeEvent, QPainter, QColor, QPalette, QBrush, QPen
from .dialogs import AttributeDialog, ModelDialog, SQLConversionDialog
from .model_manager import ModelManager
from .data_analyzer import DataAnalyzer
from .sql_generator import SQLGenerator, SQLDialect
from models.attribute import Attribute
from models.model import Model
from models.data_types import DataType, DataTypeManager
from models.quantity_manager import QuantityManager, QuantityUnit
import hashlib
import os
import json
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import math
from .logo_widget import LogoWidget
from pathlib import Path

class SecurityManager:
    """Gestionnaire de sécurité pour l'application"""
    
    def __init__(self):
        self.key = None
        self.fernet = None
        self.max_login_attempts = 3
        self.login_attempts = 0
        self.lockout_time = None
        self.lockout_duration = 300  # 5 minutes en secondes
        
        # Configuration du logging
        logging.basicConfig(
            filename='security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def initialize(self, password):
        """Initialise le système de sécurité avec un mot de passe"""
        try:
            # Génération de la clé à partir du mot de passe
            salt = b'barrelmcd_salt'  # En production, utiliser un sel unique
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.fernet = Fernet(key)
            
            logging.info("Système de sécurité initialisé")
            return True
        except Exception as e:
            logging.error(f"Erreur d'initialisation de la sécurité: {str(e)}")
            return False
            
    def encrypt_data(self, data):
        """Chiffre les données"""
        try:
            if isinstance(data, str):
                data = data.encode()
            return self.fernet.encrypt(data)
        except Exception as e:
            logging.error(f"Erreur de chiffrement: {str(e)}")
            return None
            
    def decrypt_data(self, encrypted_data):
        """Déchiffre les données"""
        try:
            return self.fernet.decrypt(encrypted_data)
        except Exception as e:
            logging.error(f"Erreur de déchiffrement: {str(e)}")
            return None
            
    def verify_password(self, password):
        """Vérifie le mot de passe"""
        if self.lockout_time and (QDateTime.currentDateTime().toSecsSinceEpoch() - self.lockout_time) < self.lockout_duration:
            remaining_time = self.lockout_duration - (QDateTime.currentDateTime().toSecsSinceEpoch() - self.lockout_time)
            logging.warning(f"Tentative de connexion bloquée - Verrouillage actif ({remaining_time}s restantes)")
            return False, f"Compte verrouillé. Réessayez dans {remaining_time} secondes."
            
        if self.login_attempts >= self.max_login_attempts:
            self.lockout_time = QDateTime.currentDateTime().toSecsSinceEpoch()
            logging.warning("Compte verrouillé après trop de tentatives")
            return False, "Trop de tentatives. Compte verrouillé pendant 5 minutes."
            
        # Vérification du mot de passe (à adapter selon votre système)
        if password == "votre_mot_de_passe_hashé":  # À remplacer par votre système de vérification
            self.login_attempts = 0
            logging.info("Connexion réussie")
            return True, "Connexion réussie"
        else:
            self.login_attempts += 1
            logging.warning(f"Tentative de connexion échouée ({self.login_attempts}/{self.max_login_attempts})")
            return False, f"Mot de passe incorrect. Tentatives restantes: {self.max_login_attempts - self.login_attempts}"
            
    def validate_input(self, input_data):
        """Valide les entrées utilisateur"""
        # Protection contre l'injection SQL
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', ';', '--']
        for keyword in sql_keywords:
            if keyword.lower() in input_data.lower():
                logging.warning(f"Tentative d'injection SQL détectée: {input_data}")
                return False
                
        # Protection contre les attaques XSS
        xss_patterns = ['<script>', 'javascript:', 'onerror=', 'onload=']
        for pattern in xss_patterns:
            if pattern.lower() in input_data.lower():
                logging.warning(f"Tentative XSS détectée: {input_data}")
                return False
                
        return True

class LoginDialog(QDialog):
    """Dialogue de connexion sécurisé"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Champ de mot de passe
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Mot de passe")
        layout.addWidget(self.password_input)
        
        # Boutons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_password(self):
        return self.password_input.text()

class TouchButton(QPushButton):
    """Bouton optimisé pour les écrans tactiles"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(80, 40)  # Taille minimale pour le toucher
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Style pour les écrans tactiles
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
        """)
        
        # Animation de pression
        self.press_animation = None
        self.setProperty("pressed", False)
        
    def event(self, event):
        """Gestion des événements tactiles"""
        if event.type() == QEvent.TouchBegin:
            self.setProperty("pressed", True)
            self.style().unpolish(self)
            self.style().polish(self)
            return True
        elif event.type() == QEvent.TouchEnd:
            self.setProperty("pressed", False)
            self.style().unpolish(self)
            self.style().polish(self)
            return True
        return super().event(event)

class ResponsiveWidget(QWidget):
    """Widget de base avec des capacités de redimensionnement"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.min_width = 200
        self.min_height = 100
        
        # Détection de l'écran tactile
        self.is_touch_screen = False
        if QApplication.instance():
            screen = QApplication.instance().primaryScreen()
            if screen:
                self.is_touch_screen = screen.capabilities() & screen.SupportsTouch
        
    def resizeEvent(self, event):
        """Gère le redimensionnement du widget"""
        super().resizeEvent(event)
        self.updateLayout()
        
    def updateLayout(self):
        """Met à jour la mise en page en fonction de la taille"""
        # À implémenter dans les classes dérivées
        pass

class ResponsiveDockWidget(QDockWidget):
    """Panneau latéral avec des capacités de redimensionnement"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setFeatures(QDockWidget.DockWidgetMovable | 
                         QDockWidget.DockWidgetFloatable |
                         QDockWidget.DockWidgetClosable)
        
        # Configuration pour le redimensionnement
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        # Widget interne avec mise en page responsive
        self.content_widget = ResponsiveWidget()
        self.setWidget(self.content_widget)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement du panneau"""
        super().resizeEvent(event)
        if hasattr(self.content_widget, 'updateLayout'):
            self.content_widget.updateLayout()

class RelationLine(QGraphicsLineItem):
    """Ligne de relation personnalisée"""
    
    def __init__(self, start_item=None, end_item=None, parent=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.is_dashed = False
        self.has_arrows = True
        self.update_style()
        
    def set_dashed(self, dashed):
        """Active ou désactive le style pointillé"""
        self.is_dashed = dashed
        self.update_style()
        
    def set_arrows(self, arrows):
        """Active ou désactive les flèches"""
        self.has_arrows = arrows
        self.update_style()
        
    def update_style(self):
        """Met à jour le style de la ligne"""
        if self.is_dashed:
            self.setPen(QPen(Qt.black, 2, Qt.DashLine))
        else:
            self.setPen(QPen(Qt.black, 2, Qt.SolidLine))
            
    def paint(self, painter, option, widget):
        """Dessine la ligne avec ou sans flèches"""
        super().paint(painter, option, widget)
        
        if self.has_arrows:
            # Dessiner les flèches
            line = self.line()
            angle = line.angle()
            length = 20
            
            # Calcul des points pour les flèches
            arrow_p1 = line.p2()
            arrow_p2 = QPointF(
                arrow_p1.x() - length * 0.5 * math.cos(math.radians(angle - 45)),
                arrow_p1.y() - length * 0.5 * math.sin(math.radians(angle - 45))
            )
            arrow_p3 = QPointF(
                arrow_p1.x() - length * 0.5 * math.cos(math.radians(angle + 45)),
                arrow_p1.y() - length * 0.5 * math.sin(math.radians(angle + 45))
            )
            
            # Dessiner les flèches
            painter.setPen(self.pen())
            painter.setBrush(QBrush(self.pen().color()))
            painter.drawPolygon([arrow_p1, arrow_p2, arrow_p3])

class EntityScene(QGraphicsScene):
    """Scène pour afficher les entités et leurs relations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entities = []
        self.relations = []
        self.current_relation = None
        self.start_entity = None
        
    def mousePressEvent(self, event):
        """Gère le clic de souris pour commencer une relation"""
        item = self.itemAt(event.scenePos(), QTransform())
        
        if isinstance(item, EntityItem):
            self.start_entity = item
            self.current_relation = RelationLine()
            self.current_relation.setLine(QLineF(event.scenePos(), event.scenePos()))
            self.addItem(self.current_relation)
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Gère le mouvement de la souris pour dessiner la relation"""
        if self.current_relation:
            line = self.current_relation.line()
            line.setP2(event.scenePos())
            self.current_relation.setLine(line)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Gère le relâchement de la souris pour terminer la relation"""
        if self.current_relation:
            item = self.itemAt(event.scenePos(), QTransform())
            
            if isinstance(item, EntityItem) and item != self.start_entity:
                # Relation valide
                self.current_relation.start_item = self.start_entity
                self.current_relation.end_item = item
                self.relations.append(self.current_relation)
            else:
                # Relation invalide, supprimer la ligne
                self.removeItem(self.current_relation)
                
            self.current_relation = None
            self.start_entity = None
        else:
            super().mouseReleaseEvent(event)
            
    def add_entity(self, entity):
        """Ajoute une entité à la scène"""
        self.entities.append(entity)
        self.addItem(entity)
        
    def add_relation(self, relation):
        """Ajoute une relation à la scène"""
        self.relations.append(relation)
        self.addItem(relation)
        
    def clear_relations(self):
        """Supprime toutes les relations"""
        for relation in self.relations:
            self.removeItem(relation)
        self.relations.clear()

class EntityItem(QGraphicsItem):
    """Représentation graphique d'une entité"""
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.attributes = []
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
    def boundingRect(self):
        """Définit la zone occupée par l'entité"""
        return QRectF(-50, -30, 100, 60)
        
    def paint(self, painter, option, widget):
        """Dessine l'entité"""
        # Dessiner le rectangle
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawRect(self.boundingRect())
        
        # Dessiner le nom
        painter.setPen(Qt.black)
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.name)
        
    def add_attribute(self, attribute):
        """Ajoute un attribut à l'entité"""
        self.attributes.append(attribute)
        self.update()

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("BarrelMCD")
            self.setMinimumSize(1024, 768)
            
            # Initialisation des gestionnaires avec gestion d'erreurs
            try:
                self.security_manager = SecurityManager()
                self.model_manager = ModelManager()
                self.data_analyzer = DataAnalyzer()
                self.sql_generator = SQLGenerator()
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'initialisation", 
                    f"Erreur lors de l'initialisation des gestionnaires: {str(e)}")
                raise
            
            # Configuration de l'interface avec gestion d'erreurs
            try:
                self.setup_ui()
                self.setup_menu()
                self.setup_toolbar()
                self.setup_statusbar()
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'interface", 
                    f"Erreur lors de la configuration de l'interface: {str(e)}")
                raise
            
            # Restauration de la géométrie
            self.restore_geometry()
            
            # Connexion des signaux avec gestion d'erreurs
            try:
                self.connect_signals()
            except Exception as e:
                QMessageBox.critical(self, "Erreur de connexion", 
                    f"Erreur lors de la connexion des signaux: {str(e)}")
                raise
                
            # Configuration du logging
            self.setup_logging()
            
        except Exception as e:
            logging.error(f"Erreur critique lors de l'initialisation de MainWindow: {str(e)}")
            raise
            
    def setup_logging(self):
        """Configure le système de logging"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / f"barrelmcd_{QDateTime.currentDateTime().toString('yyyy-MM-dd')}.log"
            
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            logger = logging.getLogger('BarrelMCD')
            logger.addHandler(file_handler)
            logger.setLevel(logging.DEBUG)
            
            self.logger = logger
            
        except Exception as e:
            print(f"Erreur lors de la configuration du logging: {str(e)}")
            
    def cleanup_resources(self):
        """Nettoie les ressources avant la fermeture"""
        try:
            # Sauvegarde des paramètres
            self.save_geometry()
            
            # Fermeture des connexions de base de données
            if hasattr(self, 'model_manager'):
                self.model_manager.cleanup()
                
            # Nettoyage des fichiers temporaires
            temp_dir = Path("temp")
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    try:
                        file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Impossible de supprimer le fichier temporaire {file}: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des ressources: {str(e)}")
            
    def closeEvent(self, event: QCloseEvent):
        """Gère la fermeture de la fenêtre"""
        try:
            # Nettoyage des ressources
            self.cleanup_resources()
            
            # Vérification des modifications non sauvegardées
            if self.model_manager.has_unsaved_changes():
                reply = QMessageBox.question(
                    self,
                    "Modifications non sauvegardées",
                    "Voulez-vous sauvegarder les modifications avant de quitter ?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if not self.save_model():
                        event.ignore()
                        return
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                    
            event.accept()
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la fermeture: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la fermeture: {str(e)}")
            event.ignore()
            
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        try:
            # Widget central
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout principal
            main_layout = QVBoxLayout(central_widget)
            
            # Zone de travail
            self.work_area = QSplitter(Qt.Horizontal)
            main_layout.addWidget(self.work_area)
            
            # Panneau de modèle
            self.model_panel = QDockWidget("Modèle", self)
            self.model_panel.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.model_panel)
            
            # Zone de dessin
            self.drawing_area = QGraphicsView()
            self.drawing_scene = QGraphicsScene()
            self.drawing_area.setScene(self.drawing_scene)
            self.work_area.addWidget(self.drawing_area)
            
            # Panneau de propriétés
            self.properties_panel = QDockWidget("Propriétés", self)
            self.properties_panel.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la configuration de l'interface: {str(e)}")
            raise
            
    def setup_menu(self):
        """Configure le menu principal"""
        try:
            menubar = self.menuBar()
            
            # Menu Fichier
            file_menu = menubar.addMenu("Fichier")
            new_action = QAction("Nouveau", self)
            new_action.setShortcut("Ctrl+N")
            new_action.triggered.connect(self.new_model)
            file_menu.addAction(new_action)
            
            open_action = QAction("Ouvrir", self)
            open_action.setShortcut("Ctrl+O")
            open_action.triggered.connect(self.open_model)
            file_menu.addAction(open_action)
            
            save_action = QAction("Enregistrer", self)
            save_action.setShortcut("Ctrl+S")
            save_action.triggered.connect(self.save_model)
            file_menu.addAction(save_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("Quitter", self)
            exit_action.setShortcut("Alt+F4")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Menu Édition
            edit_menu = menubar.addMenu("Édition")
            undo_action = QAction("Annuler", self)
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self.undo)
            edit_menu.addAction(undo_action)
            
            redo_action = QAction("Rétablir", self)
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self.redo)
            edit_menu.addAction(redo_action)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la configuration du menu: {str(e)}")
            raise
            
    def setup_toolbar(self):
        """Configure la barre d'outils"""
        try:
            toolbar = QToolBar()
            toolbar.setMovable(False)
            self.addToolBar(toolbar)
            
            # Boutons de la barre d'outils
            new_btn = QAction(QIcon("images/new.png"), "Nouveau", self)
            new_btn.triggered.connect(self.new_model)
            toolbar.addAction(new_btn)
            
            open_btn = QAction(QIcon("images/open.png"), "Ouvrir", self)
            open_btn.triggered.connect(self.open_model)
            toolbar.addAction(open_btn)
            
            save_btn = QAction(QIcon("images/save.png"), "Enregistrer", self)
            save_btn.triggered.connect(self.save_model)
            toolbar.addAction(save_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la configuration de la barre d'outils: {str(e)}")
            raise
            
    def setup_statusbar(self):
        """Configure la barre de statut"""
        try:
            statusbar = QStatusBar()
            self.setStatusBar(statusbar)
            
            # Labels de statut
            self.status_label = QLabel()
            statusbar.addWidget(self.status_label)
            
            self.coords_label = QLabel()
            statusbar.addPermanentWidget(self.coords_label)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la configuration de la barre de statut: {str(e)}")
            raise
            
    def connect_signals(self):
        """Connecte les signaux aux slots"""
        try:
            # Signaux de la zone de dessin
            self.drawing_area.mouseMoveEvent = self.update_coordinates
            
            # Signaux du modèle
            self.model_manager.model_changed.connect(self.update_model_view)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la connexion des signaux: {str(e)}")
            raise
            
    def restore_geometry(self):
        """Restaure la géométrie de la fenêtre"""
        try:
            settings = QSettings("BarrelMCD", "MainWindow")
            geometry = settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            state = settings.value("windowState")
            if state:
                self.restoreState(state)
        except Exception as e:
            print(f"Erreur lors de la restauration de la géométrie: {str(e)}")
            
    def save_geometry(self):
        """Sauvegarde la géométrie de la fenêtre"""
        try:
            settings = QSettings("BarrelMCD", "MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la géométrie: {str(e)}")
            
    def update_coordinates(self, event):
        """Met à jour les coordonnées dans la barre de statut"""
        try:
            pos = self.drawing_area.mapToScene(event.pos())
            self.coords_label.setText(f"X: {int(pos.x())}, Y: {int(pos.y())}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour des coordonnées: {str(e)}")
            
    def update_model_view(self):
        """Met à jour la vue du modèle"""
        try:
            self.drawing_scene.clear()
            # Mise à jour de la vue avec le modèle actuel
            # TODO: Implémenter la logique de mise à jour
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de la vue: {str(e)}")
            
    def new_model(self):
        """Crée un nouveau modèle"""
        try:
            if self.model_manager.has_unsaved_changes():
                reply = QMessageBox.question(
                    self,
                    "Modifications non sauvegardées",
                    "Voulez-vous sauvegarder les modifications avant de créer un nouveau modèle ?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if not self.save_model():
                        return
                elif reply == QMessageBox.Cancel:
                    return
                    
            self.model_manager.new_model()
            self.update_model_view()
            self.status_label.setText("Nouveau modèle créé")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du modèle: {str(e)}")
            
    def open_model(self):
        """Ouvre un modèle existant"""
        try:
            if self.model_manager.has_unsaved_changes():
                reply = QMessageBox.question(
                    self,
                    "Modifications non sauvegardées",
                    "Voulez-vous sauvegarder les modifications avant d'ouvrir un autre modèle ?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if not self.save_model():
                        return
                elif reply == QMessageBox.Cancel:
                    return
                    
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Ouvrir un modèle",
                "",
                "Fichiers BarrelMCD (*.bcd);;Tous les fichiers (*.*)"
            )
            
            if file_name:
                if self.model_manager.open_model(file_name):
                    self.update_model_view()
                    self.status_label.setText(f"Modèle ouvert: {file_name}")
                else:
                    QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir le modèle")
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du modèle: {str(e)}")
            
    def save_model(self):
        """Sauvegarde le modèle actuel"""
        try:
            if not self.model_manager.current_model:
                file_name, _ = QFileDialog.getSaveFileName(
                    self,
                    "Enregistrer le modèle",
                    "",
                    "Fichiers BarrelMCD (*.bcd);;Tous les fichiers (*.*)"
                )
                
                if not file_name:
                    return False
                    
                if not file_name.endswith('.bcd'):
                    file_name += '.bcd'
                    
                return self.model_manager.save_model(file_name)
            else:
                return self.model_manager.save_model()
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde du modèle: {str(e)}")
            return False
            
    def undo(self):
        """Annule la dernière action"""
        try:
            if self.model_manager.undo():
                self.update_model_view()
                self.status_label.setText("Action annulée")
            else:
                self.status_label.setText("Rien à annuler")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation: {str(e)}")
            
    def redo(self):
        """Rétablit la dernière action annulée"""
        try:
            if self.model_manager.redo():
                self.update_model_view()
                self.status_label.setText("Action rétablie")
            else:
                self.status_label.setText("Rien à rétablir")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du rétablissement: {str(e)}") 