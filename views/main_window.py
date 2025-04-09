from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QMessageBox, QFileDialog,
                             QMenuBar, QMenu, QAction, QToolBar, QStatusBar,
                             QDockWidget, QSplitter, QTabWidget, QApplication,
                             QScreen, QDesktopWidget, QInputDialog, QDialog,
                             QListWidget, QSizePolicy, QScrollArea, QFrame,
                             QStyle, QStyleOptionButton, QLineEdit, QDialogButtonBox,
                             QGraphicsLineItem, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import Qt, QSettings, QSize, QPoint, QTimer, QEvent, QRect, QDateTime, QLineF, QPen
from PyQt5.QtGui import QIcon, QFont, QCloseEvent, QResizeEvent, QPainter, QColor, QPalette, QPen, QBrush
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
        self.is_touch_screen = QApplication.instance().primaryScreen().capabilities() & QScreen.SupportsTouch
        
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BarrelMCD")
        self.setMinimumSize(800, 600)
        
        # Initialisation du gestionnaire de sécurité
        self.security_manager = SecurityManager()
        
        # Vérification de la connexion
        if not self.verify_login():
            sys.exit()
            
        # Détection de l'écran tactile
        self.is_touch_screen = QApplication.instance().primaryScreen().capabilities() & QScreen.SupportsTouch
        
        # Initialisation des gestionnaires
        self.model_manager = ModelManager()
        self.data_analyzer = DataAnalyzer()
        self.sql_generator = SQLGenerator()
        self.data_type_manager = DataTypeManager()
        self.quantity_manager = QuantityManager()
        
        # Configuration de l'interface
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_docks()
        
        # Chargement des paramètres
        self.load_settings()
        
        # Timer pour les mises à jour de mise en page
        self.layout_timer = QTimer(self)
        self.layout_timer.setSingleShot(True)
        self.layout_timer.timeout.connect(self.updateAllLayouts)
        
    def verify_login(self):
        """Vérifie la connexion de l'utilisateur"""
        dialog = LoginDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            password = dialog.get_password()
            success, message = self.security_manager.verify_password(password)
            
            if not success:
                QMessageBox.critical(self, "Erreur de connexion", message)
                return False
                
            return True
        return False
        
    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Widget central avec zone de défilement
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Zone de modèle avec défilement
        self.model_scroll = QScrollArea()
        self.model_scroll.setWidgetResizable(True)
        self.model_scroll.setFrameShape(QFrame.NoFrame)
        
        # Création de la scène et de la vue pour les entités
        self.scene = EntityScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Ajout de la vue à la zone de défilement
        self.model_scroll.setWidget(self.view)
        self.main_layout.addWidget(self.model_scroll)
        
        # Boutons d'action dans un conteneur responsive
        self.button_container = ResponsiveWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Boutons d'action adaptés aux écrans tactiles
        new_model_btn = TouchButton("Nouveau modèle")
        new_model_btn.clicked.connect(self.new_model)
        self.button_layout.addWidget(new_model_btn)
        
        add_attribute_btn = TouchButton("Ajouter un attribut")
        add_attribute_btn.clicked.connect(self.add_attribute)
        self.button_layout.addWidget(add_attribute_btn)
        
        convert_sql_btn = TouchButton("Convertir SQL")
        convert_sql_btn.clicked.connect(self.show_sql_conversion)
        self.button_layout.addWidget(convert_sql_btn)
        
        # Boutons pour les relations
        add_relation_btn = TouchButton("Ajouter relation")
        add_relation_btn.clicked.connect(self.add_relation)
        self.button_layout.addWidget(add_relation_btn)
        
        toggle_dashed_btn = TouchButton("Ligne pointillée")
        toggle_dashed_btn.setCheckable(True)
        toggle_dashed_btn.clicked.connect(self.toggle_dashed_line)
        self.button_layout.addWidget(toggle_dashed_btn)
        
        toggle_arrows_btn = TouchButton("Afficher flèches")
        toggle_arrows_btn.setCheckable(True)
        toggle_arrows_btn.setChecked(True)
        toggle_arrows_btn.clicked.connect(self.toggle_arrows)
        self.button_layout.addWidget(toggle_arrows_btn)
        
        self.button_layout.addStretch()
        self.main_layout.addWidget(self.button_container)
        
        # Définition de la méthode de mise à jour de la mise en page
        self.button_container.updateLayout = self.updateButtonLayout
        
    def add_relation(self):
        """Ajoute une nouvelle relation"""
        # Cette méthode est appelée lorsque l'utilisateur clique sur le bouton "Ajouter relation"
        # L'utilisateur devra ensuite cliquer sur deux entités pour créer la relation
        self.statusBar().showMessage("Cliquez sur la première entité, puis sur la deuxième pour créer la relation")
        
    def toggle_dashed_line(self, checked):
        """Active ou désactive le style pointillé pour les nouvelles relations"""
        if hasattr(self, 'scene'):
            for relation in self.scene.relations:
                relation.set_dashed(checked)
            self.statusBar().showMessage("Style de ligne pointillé " + ("activé" if checked else "désactivé"))
            
    def toggle_arrows(self, checked):
        """Active ou désactive les flèches pour les nouvelles relations"""
        if hasattr(self, 'scene'):
            for relation in self.scene.relations:
                relation.set_arrows(checked)
            self.statusBar().showMessage("Flèches " + ("activées" if checked else "désactivées"))
            
    def new_model(self):
        """Crée un nouveau modèle"""
        dialog = ModelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            model_name = dialog.get_model_name()
            model_description = dialog.get_model_description()
            
            model = Model(name=model_name, description=model_description)
            self.model_manager.add_model(model)
            
            # Créer une entité pour le modèle
            entity = EntityItem(model_name)
            self.scene.add_entity(entity)
            
            self.statusBar().showMessage(f"Nouveau modèle créé: {model_name}")
            
    def add_attribute(self):
        """Ajoute un nouvel attribut au modèle actuel avec validation de sécurité"""
        if not self.model_manager.current_model:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord créer un modèle.")
            return
            
        dialog = AttributeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            attribute = dialog.get_attribute()
            if attribute:
                # Validation des entrées
                if not self.security_manager.validate_input(attribute.name):
                    QMessageBox.warning(self, "Attention", "Nom d'attribut non valide.")
                    return
                    
                self.model_manager.current_model.add_attribute(attribute)
                
                # Ajouter l'attribut à l'entité sélectionnée
                selected_items = self.scene.selectedItems()
                if selected_items and isinstance(selected_items[0], EntityItem):
                    selected_items[0].add_attribute(attribute)
                    self.statusBar().showMessage(f"Attribut ajouté de manière sécurisée: {attribute.name}")
                else:
                    QMessageBox.warning(self, "Attention", "Veuillez sélectionner une entité pour ajouter l'attribut.")
                    
    def show_sql_conversion(self):
        """Affiche le dialogue de conversion SQL"""
        dialog = SQLConversionDialog(self)
        dialog.exec_()
        
    def updateButtonLayout(self):
        """Met à jour la mise en page des boutons en fonction de la taille"""
        width = self.button_container.width()
        
        # Ajustement de la mise en page en fonction de la largeur
        if width < 400 or self.is_touch_screen:
            # Mode vertical pour les petits écrans ou écrans tactiles
            self.button_layout.setDirection(QVBoxLayout.TopToBottom)
            for i in range(self.button_layout.count()):
                item = self.button_layout.itemAt(i)
                if item.widget():
                    item.widget().setMinimumWidth(width - 20)
                    if isinstance(item.widget(), TouchButton):
                        item.widget().setMinimumHeight(50)  # Plus grand pour le toucher
        else:
            # Mode horizontal pour les grands écrans
            self.button_layout.setDirection(QHBoxLayout.LeftToRight)
            for i in range(self.button_layout.count()):
                item = self.button_layout.itemAt(i)
                if item.widget():
                    item.widget().setMinimumWidth(100)
                    if isinstance(item.widget(), TouchButton):
                        item.widget().setMinimumHeight(40)
        
    def setup_docks(self):
        """Configure les panneaux latéraux"""
        # Panneau d'attributs
        self.attributes_dock = ResponsiveDockWidget("Attributs", self)
        self.attributes_widget = ResponsiveWidget()
        self.attributes_layout = QVBoxLayout(self.attributes_widget)
        self.attributes_layout.setContentsMargins(5, 5, 5, 5)
        
        # Zone de défilement pour les attributs
        self.attributes_scroll = QScrollArea()
        self.attributes_scroll.setWidgetResizable(True)
        self.attributes_scroll.setFrameShape(QFrame.NoFrame)
        
        self.attributes_content = ResponsiveWidget()
        self.attributes_content_layout = QVBoxLayout(self.attributes_content)
        self.attributes_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.attributes_list = QLabel("Aucun attribut")
        self.attributes_content_layout.addWidget(self.attributes_list)
        self.attributes_content_layout.addStretch()
        
        self.attributes_scroll.setWidget(self.attributes_content)
        self.attributes_layout.addWidget(self.attributes_scroll)
        
        self.attributes_dock.content_widget = self.attributes_widget
        self.addDockWidget(Qt.LeftDockWidgetArea, self.attributes_dock)
        
        # Panneau de propriétés
        self.properties_dock = ResponsiveDockWidget("Propriétés", self)
        self.properties_widget = ResponsiveWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_layout.setContentsMargins(5, 5, 5, 5)
        
        # Zone de défilement pour les propriétés
        self.properties_scroll = QScrollArea()
        self.properties_scroll.setWidgetResizable(True)
        self.properties_scroll.setFrameShape(QFrame.NoFrame)
        
        self.properties_content = ResponsiveWidget()
        self.properties_content_layout = QVBoxLayout(self.properties_content)
        self.properties_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.properties_list = QLabel("Aucune propriété sélectionnée")
        self.properties_content_layout.addWidget(self.properties_list)
        self.properties_content_layout.addStretch()
        
        self.properties_scroll.setWidget(self.properties_content)
        self.properties_layout.addWidget(self.properties_scroll)
        
        self.properties_dock.content_widget = self.properties_widget
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        
        # Panneau de sortie
        self.output_dock = ResponsiveDockWidget("Sortie", self)
        self.output_widget = ResponsiveWidget()
        self.output_layout = QVBoxLayout(self.output_widget)
        self.output_layout.setContentsMargins(5, 5, 5, 5)
        
        # Zone de défilement pour la sortie
        self.output_scroll = QScrollArea()
        self.output_scroll.setWidgetResizable(True)
        self.output_scroll.setFrameShape(QFrame.NoFrame)
        
        self.output_content = ResponsiveWidget()
        self.output_content_layout = QVBoxLayout(self.output_content)
        self.output_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output_text = QLabel("Aucune sortie")
        self.output_text.setWordWrap(True)
        self.output_content_layout.addWidget(self.output_text)
        self.output_content_layout.addStretch()
        
        self.output_scroll.setWidget(self.output_content)
        self.output_layout.addWidget(self.output_scroll)
        
        self.output_dock.content_widget = self.output_widget
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_dock)
        
        # Ajout d'un menu pour les panneaux
        self.view_menu = self.menuBar().addMenu("Affichage")
        
        # Actions pour afficher/masquer les panneaux
        self.attributes_dock_action = self.attributes_dock.toggleViewAction()
        self.attributes_dock_action.setText("Panneau d'attributs")
        self.view_menu.addAction(self.attributes_dock_action)
        
        self.properties_dock_action = self.properties_dock.toggleViewAction()
        self.properties_dock_action.setText("Panneau de propriétés")
        self.view_menu.addAction(self.properties_dock_action)
        
        self.output_dock_action = self.output_dock.toggleViewAction()
        self.output_dock_action.setText("Panneau de sortie")
        self.view_menu.addAction(self.output_dock_action)
        
        # Action pour ajouter un nouveau panneau
        self.view_menu.addSeparator()
        add_panel_action = QAction("Ajouter un panneau", self)
        add_panel_action.triggered.connect(self.add_new_panel)
        self.view_menu.addAction(add_panel_action)
        
        # Action pour gérer les écrans
        self.view_menu.addSeparator()
        manage_screens_action = QAction("Gérer les écrans", self)
        manage_screens_action.triggered.connect(self.manage_screens)
        self.view_menu.addAction(manage_screens_action)
        
        # Action pour le mode plein écran
        self.view_menu.addSeparator()
        fullscreen_action = QAction("Mode plein écran", self)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.view_menu.addAction(fullscreen_action)
        
    def setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Adaptation du menu pour les écrans tactiles
        if self.is_touch_screen:
            menubar.setStyleSheet("""
                QMenuBar {
                    background-color: #f0f0f0;
                    padding: 5px;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    margin: 2px;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
            """)
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        new_action = QAction("Nouveau", self)
        new_action.triggered.connect(self.new_model)
        file_menu.addAction(new_action)
        
        open_action = QAction("Ouvrir", self)
        open_action.triggered.connect(self.open_model)
        file_menu.addAction(open_action)
        
        save_action = QAction("Enregistrer", self)
        save_action.triggered.connect(self.save_model)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Édition
        edit_menu = menubar.addMenu("Édition")
        
        add_attribute_action = QAction("Ajouter un attribut", self)
        add_attribute_action.triggered.connect(self.add_attribute)
        edit_menu.addAction(add_attribute_action)
        
        convert_sql_action = QAction("Convertir SQL", self)
        convert_sql_action.triggered.connect(self.show_sql_conversion)
        edit_menu.addAction(convert_sql_action)
        
        # Menu Aide
        help_menu = menubar.addMenu("Aide")
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Configure la barre d'outils"""
        toolbar = QToolBar()
        toolbar.setMovable(True)
        toolbar.setFloatable(True)
        
        # Adaptation de la barre d'outils pour les écrans tactiles
        if self.is_touch_screen:
            toolbar.setIconSize(QSize(32, 32))  # Icônes plus grandes
            toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        self.addToolBar(toolbar)
        
        # Actions avec des boutons tactiles
        new_action = QAction("Nouveau", self)
        new_action.triggered.connect(self.new_model)
        toolbar.addAction(new_action)
        
        add_attribute_action = QAction("Ajouter un attribut", self)
        add_attribute_action.triggered.connect(self.add_attribute)
        toolbar.addAction(add_attribute_action)
        
        convert_sql_action = QAction("Convertir SQL", self)
        convert_sql_action.triggered.connect(self.show_sql_conversion)
        toolbar.addAction(convert_sql_action)
        
    def setup_statusbar(self):
        """Configure la barre de statut"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        statusbar.showMessage("Prêt")
        
    def load_settings(self):
        """Charge les paramètres de l'application"""
        settings = QSettings("BarrelMCD", "BarrelMCD")
        
        # Géométrie de la fenêtre
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # État des panneaux
        dock_state = settings.value("dock_state")
        if dock_state:
            self.restoreState(dock_state)
            
        # Position sur l'écran
        screen_index = settings.value("screen_index", 0, type=int)
        self.move_to_screen(screen_index)
        
        # État du mode plein écran
        is_fullscreen = settings.value("fullscreen", False, type=bool)
        if is_fullscreen:
            self.showFullScreen()
        
    def save_settings(self):
        """Enregistre les paramètres de l'application"""
        settings = QSettings("BarrelMCD", "BarrelMCD")
        
        # Géométrie de la fenêtre
        settings.setValue("geometry", self.saveGeometry())
        
        # État des panneaux
        settings.setValue("dock_state", self.saveState())
        
        # Position sur l'écran
        current_screen = QApplication.desktop().screenNumber(self)
        settings.setValue("screen_index", current_screen)
        
        # État du mode plein écran
        settings.setValue("fullscreen", self.isFullScreen())
        
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self,
            "À propos de BarrelMCD",
            "BarrelMCD - Générateur de modèles de données\n\n"
            "Version 1.0\n\n"
            "Un outil pour créer et gérer des modèles de données."
        )
        
    def add_new_panel(self):
        """Ajoute un nouveau panneau personnalisé"""
        panel_name, ok = QInputDialog.getText(
            self,
            "Nouveau panneau",
            "Nom du panneau:"
        )
        
        if ok and panel_name:
            # Création du panneau
            new_dock = ResponsiveDockWidget(panel_name, self)
            
            # Widget du panneau
            panel_widget = ResponsiveWidget()
            panel_layout = QVBoxLayout(panel_widget)
            panel_layout.setContentsMargins(5, 5, 5, 5)
            
            # Zone de défilement
            panel_scroll = QScrollArea()
            panel_scroll.setWidgetResizable(True)
            panel_scroll.setFrameShape(QFrame.NoFrame)
            
            panel_content = ResponsiveWidget()
            panel_content_layout = QVBoxLayout(panel_content)
            panel_content_layout.setContentsMargins(0, 0, 0, 0)
            
            panel_label = QLabel(f"Contenu du panneau {panel_name}")
            panel_label.setWordWrap(True)
            panel_content_layout.addWidget(panel_label)
            panel_content_layout.addStretch()
            
            panel_scroll.setWidget(panel_content)
            panel_layout.addWidget(panel_scroll)
            
            # Boutons d'action avec support tactile
            button_layout = QHBoxLayout()
            close_button = TouchButton("Fermer")
            close_button.clicked.connect(lambda: self.close_panel(new_dock))
            button_layout.addWidget(close_button)
            panel_layout.addLayout(button_layout)
            
            new_dock.content_widget = panel_widget
            new_dock.setWidget(panel_widget)
            
            # Ajout du panneau à la fenêtre
            self.addDockWidget(Qt.RightDockWidgetArea, new_dock)
            
            # Ajout de l'action dans le menu Affichage
            dock_action = new_dock.toggleViewAction()
            dock_action.setText(panel_name)
            self.view_menu.addAction(dock_action)
            
            self.statusBar().showMessage(f"Panneau '{panel_name}' ajouté")
            
    def close_panel(self, dock):
        """Ferme un panneau personnalisé"""
        self.removeDockWidget(dock)
        dock.deleteLater()
        
    def manage_screens(self):
        """Gère l'affichage sur plusieurs écrans"""
        screens = QApplication.screens()
        
        if len(screens) <= 1:
            QMessageBox.information(
                self,
                "Gestion des écrans",
                "Un seul écran est détecté."
            )
            return
            
        # Création du dialogue de gestion des écrans
        dialog = QDialog(self)
        dialog.setWindowTitle("Gestion des écrans")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Liste des écrans disponibles
        screen_label = QLabel("Écrans disponibles:")
        layout.addWidget(screen_label)
        
        screen_list = QListWidget()
        for i, screen in enumerate(screens):
            screen_list.addItem(f"Écran {i+1}: {screen.name()} ({screen.size().width()}x{screen.size().height()})")
        layout.addWidget(screen_list)
        
        # Boutons d'action avec support tactile
        button_layout = QHBoxLayout()
        
        move_button = TouchButton("Déplacer la fenêtre")
        move_button.clicked.connect(lambda: self.move_to_screen(screen_list.currentRow()))
        button_layout.addWidget(move_button)
        
        close_button = TouchButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
        
    def move_to_screen(self, screen_index):
        """Déplace la fenêtre sur un écran spécifique"""
        screens = QApplication.screens()
        
        if 0 <= screen_index < len(screens):
            screen = screens[screen_index]
            screen_geometry = screen.geometry()
            
            # Calcul de la nouvelle position
            x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
            
            self.move(x, y)
            self.statusBar().showMessage(f"Fenêtre déplacée sur l'écran {screen_index+1}")
            
    def toggle_fullscreen(self, checked):
        """Active ou désactive le mode plein écran"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
            
    def resizeEvent(self, event):
        """Gère le redimensionnement de la fenêtre"""
        super().resizeEvent(event)
        
        # Démarre un timer pour mettre à jour la mise en page après le redimensionnement
        self.layout_timer.start(100)
        
    def updateAllLayouts(self):
        """Met à jour toutes les mises en page"""
        # Met à jour la mise en page des boutons
        if hasattr(self, 'button_container') and hasattr(self.button_container, 'updateLayout'):
            self.button_container.updateLayout()
            
        # Met à jour les mises en page des panneaux
        for dock in self.findChildren(QDockWidget):
            if hasattr(dock, 'content_widget') and hasattr(dock.content_widget, 'updateLayout'):
                dock.content_widget.updateLayout()
        
    def event(self, event):
        """Gestion des événements tactiles globaux"""
        if event.type() == QEvent.TouchBegin:
            # Désactive le mode plein écran si on touche les bords
            if self.isFullScreen():
                pos = event.pos()
                if pos.x() < 10 or pos.x() > self.width() - 10:
                    self.showNormal()
                    return True
        return super().event(event)

    def closeEvent(self, event):
        """Gère la fermeture sécurisée de l'application"""
        try:
            self.save_settings()
            logging.info("Application fermée de manière sécurisée")
            event.accept()
        except Exception as e:
            logging.error(f"Erreur lors de la fermeture: {str(e)}")
            event.accept() 