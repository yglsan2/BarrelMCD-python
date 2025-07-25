#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de connexion intelligente style Db-Main
"""

import math
from typing import List, Tuple, Optional, Set
from PyQt5.QtCore import QPointF, QRectF, QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPainterPath, QPen, QColor, QPainter, QBrush
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem, QGraphicsEllipseItem

class Obstacle:
    """Représente un obstacle à éviter"""
    def __init__(self, rect: QRectF, item: QGraphicsItem):
        self.rect = rect
        self.item = item
        self.padding = 10  # Marge de sécurité
        
    def get_avoidance_rect(self) -> QRectF:
        """Retourne le rectangle d'évitement avec marge"""
        return QRectF(
            self.rect.x() - self.padding,
            self.rect.y() - self.padding,
            self.rect.width() + 2 * self.padding,
            self.rect.height() + 2 * self.padding
        )
        
    def contains_point(self, point: QPointF) -> bool:
        """Vérifie si un point est dans l'obstacle"""
        return self.get_avoidance_rect().contains(point)

class PathNode:
    """Nœud pour l'algorithme de recherche de chemin"""
    def __init__(self, pos: QPointF, g_cost: float = 0, h_cost: float = 0):
        self.pos = pos
        self.g_cost = g_cost  # Coût depuis le départ
        self.h_cost = h_cost  # Coût heuristique vers l'arrivée
        self.f_cost = g_cost + h_cost  # Coût total
        self.parent = None
        
    def __lt__(self, other):
        return self.f_cost < other.f_cost

class SmartConnector(QObject):
    """Système de connexion intelligente style Db-Main"""
    
    path_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.obstacles: List[Obstacle] = []
        self.grid_size = 20
        self.connection_margin = 15
        
    def add_obstacle(self, item: QGraphicsItem):
        """Ajoute un obstacle à éviter"""
        rect = item.boundingRect()
        pos = item.pos()
        world_rect = QRectF(
            pos.x() + rect.x(),
            pos.y() + rect.y(),
            rect.width(),
            rect.height()
        )
        obstacle = Obstacle(world_rect, item)
        self.obstacles.append(obstacle)
        
    def remove_obstacle(self, item: QGraphicsItem):
        """Retire un obstacle"""
        self.obstacles = [obs for obs in self.obstacles if obs.item != item]
        
    def update_obstacle(self, item: QGraphicsItem):
        """Met à jour la position d'un obstacle"""
        self.remove_obstacle(item)
        self.add_obstacle(item)
        
    def is_point_free(self, point: QPointF) -> bool:
        """Vérifie si un point est libre d'obstacles"""
        for obstacle in self.obstacles:
            if obstacle.contains_point(point):
                return False
        return True
        
    def get_neighbors(self, pos: QPointF) -> List[QPointF]:
        """Retourne les voisins valides d'un point"""
        neighbors = []
        directions = [
            (0, -1), (1, 0), (0, 1), (-1, 0),  # Cardinal
            (1, -1), (1, 1), (-1, 1), (-1, -1)  # Diagonal
        ]
        
        for dx, dy in directions:
            neighbor = QPointF(
                pos.x() + dx * self.grid_size,
                pos.y() + dy * self.grid_size
            )
            if self.is_point_free(neighbor):
                neighbors.append(neighbor)
                
        return neighbors
        
    def heuristic(self, a: QPointF, b: QPointF) -> float:
        """Calcul de la distance heuristique (distance euclidienne)"""
        dx = a.x() - b.x()
        dy = a.y() - b.y()
        return math.sqrt(dx*dx + dy*dy)
        
    def find_path(self, start: QPointF, end: QPointF) -> List[QPointF]:
        """Trouve le chemin optimal avec algorithme A*"""
        if not self.is_point_free(start) or not self.is_point_free(end):
            return [start, end]  # Chemin direct si points invalides
            
        open_set = [PathNode(start)]
        closed_set = set()
        came_from = {}
        
        g_scores = {start: 0}
        f_scores = {start: self.heuristic(start, end)}
        
        while open_set:
            # Trouver le nœud avec le plus petit f_cost
            open_set.sort()
            current_node = open_set.pop(0)
            current_pos = current_node.pos
            
            if self.heuristic(current_pos, end) < self.grid_size:
                # Chemin trouvé
                path = []
                while current_pos in came_from:
                    path.append(current_pos)
                    current_pos = came_from[current_pos]
                path.append(start)
                path.reverse()
                path.append(end)
                return path
                
            closed_set.add(current_pos)
            
            # Explorer les voisins
            for neighbor_pos in self.get_neighbors(current_pos):
                if neighbor_pos in closed_set:
                    continue
                    
                tentative_g = g_scores[current_pos] + self.heuristic(current_pos, neighbor_pos)
                
                if neighbor_pos not in [node.pos for node in open_set]:
                    open_set.append(PathNode(neighbor_pos))
                elif tentative_g >= g_scores.get(neighbor_pos, float('inf')):
                    continue
                    
                came_from[neighbor_pos] = current_pos
                g_scores[neighbor_pos] = tentative_g
                f_scores[neighbor_pos] = tentative_g + self.heuristic(neighbor_pos, end)
                
        # Aucun chemin trouvé, retourner chemin direct
        return [start, end]
        
    def smooth_path(self, path: List[QPointF]) -> List[QPointF]:
        """Lisse le chemin en supprimant les points inutiles"""
        if len(path) <= 2:
            return path
            
        smoothed = [path[0]]
        i = 1
        
        while i < len(path) - 1:
            current = path[i]
            next_point = path[i + 1]
            
            # Vérifier si on peut aller directement au point suivant
            can_skip = True
            for obstacle in self.obstacles:
                if self.line_intersects_obstacle(smoothed[-1], next_point, obstacle):
                    can_skip = False
                    break
                    
            if can_skip:
                i += 1
            else:
                smoothed.append(current)
                i += 1
                
        smoothed.append(path[-1])
        return smoothed
        
    def line_intersects_obstacle(self, start: QPointF, end: QPointF, obstacle: Obstacle) -> bool:
        """Vérifie si une ligne intersecte un obstacle"""
        # Test simple : vérifier si le segment traverse l'obstacle
        rect = obstacle.get_avoidance_rect()
        
        # Test des coins du rectangle
        corners = [
            QPointF(rect.x(), rect.y()),
            QPointF(rect.x() + rect.width(), rect.y()),
            QPointF(rect.x() + rect.width(), rect.y() + rect.height()),
            QPointF(rect.x(), rect.y() + rect.height())
        ]
        
        for i, corner in enumerate(corners):
            next_corner = corners[(i + 1) % 4]
            if self.segments_intersect(start, end, corner, next_corner):
                return True
                
        return False
        
    def segments_intersect(self, a1: QPointF, a2: QPointF, b1: QPointF, b2: QPointF) -> bool:
        """Vérifie si deux segments se croisent"""
        def ccw(A, B, C):
            return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())
            
        return ccw(a1, b1, b2) != ccw(a2, b1, b2) and ccw(a1, a2, b1) != ccw(a1, a2, b2)

class SmartConnection(QGraphicsPathItem):
    """Connexion intelligente avec chemin optimal style Db-Main"""
    
    # Modes de raidissement
    MODE_STRAIGHT = "straight"      # Ligne droite
    MODE_ORTHOGONAL = "orthogonal"  # Angles droits (style Db-Main)
    MODE_CURVED = "curved"          # Courbes de Bézier
    MODE_STEPPED = "stepped"        # Escalier
    
    def __init__(self, start_item: QGraphicsItem, end_item: QGraphicsItem, connector: SmartConnector):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.connector = connector
        self.path_points = []
        self.is_manual = False
        self.manual_points = []
        self.is_destroyed = False  # Flag pour éviter les doubles suppressions
        
        # Mode de raidissement
        self.stiffness_mode = self.MODE_ORTHOGONAL  # Par défaut, style Db-Main
        self.control_points = []  # Points de contrôle visibles
        self.selected_control_point = None
        
        # Style
        self.setPen(QPen(QColor(100, 150, 255), 2))
        self.setZValue(-1)  # Sous les autres éléments
        
        # Configuration interactive
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        
        # Calculer le chemin initial
        self.update_path()
        
    def __del__(self):
        """Destructeur pour nettoyer les références"""
        self.is_destroyed = True
        
    def set_stiffness_mode(self, mode):
        """Définit le mode de raidissement"""
        self.stiffness_mode = mode
        self.update_path()
        
    def get_stiffness_modes(self):
        """Retourne les modes de raidissement disponibles"""
        return [
            (self.MODE_STRAIGHT, "Ligne droite"),
            (self.MODE_ORTHOGONAL, "Angles droits (Db-Main)"),
            (self.MODE_CURVED, "Courbe"),
            (self.MODE_STEPPED, "Escalier")
        ]
        
    def update_path(self):
        """Met à jour le chemin de la connexion selon le mode de raidissement"""
        if not self.start_item or not self.end_item:
            return
            
        start_pos = self.start_item.pos()
        end_pos = self.end_item.pos()
        
        if self.is_manual and self.manual_points:
            # Utiliser les points manuels
            self.path_points = [start_pos] + self.manual_points + [end_pos]
        else:
            # Calculer le chemin selon le mode de raidissement
            if self.stiffness_mode == self.MODE_STRAIGHT:
                self.path_points = self.calculate_straight_path(start_pos, end_pos)
            elif self.stiffness_mode == self.MODE_ORTHOGONAL:
                self.path_points = self.calculate_orthogonal_path(start_pos, end_pos)
            elif self.stiffness_mode == self.MODE_CURVED:
                self.path_points = self.calculate_curved_path(start_pos, end_pos)
            elif self.stiffness_mode == self.MODE_STEPPED:
                self.path_points = self.calculate_stepped_path(start_pos, end_pos)
            else:
                # Mode automatique avec évitement d'obstacles
                path = self.connector.find_path(start_pos, end_pos)
                self.path_points = self.connector.smooth_path(path)
            
        # Créer le chemin visuel
        self.update_visual_path()
        
    def calculate_straight_path(self, start_pos, end_pos):
        """Calcule un chemin en ligne droite"""
        return [start_pos, end_pos]
        
    def calculate_orthogonal_path(self, start_pos, end_pos):
        """Calcule un chemin avec angles droits (style Db-Main)"""
        # Déterminer la direction principale
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        if abs(dx) > abs(dy):
            # Mouvement principal horizontal
            mid_x = start_pos.x() + dx / 2
            return [
                start_pos,
                QPointF(mid_x, start_pos.y()),
                QPointF(mid_x, end_pos.y()),
                end_pos
            ]
        else:
            # Mouvement principal vertical
            mid_y = start_pos.y() + dy / 2
            return [
                start_pos,
                QPointF(start_pos.x(), mid_y),
                QPointF(end_pos.x(), mid_y),
                end_pos
            ]
            
    def calculate_curved_path(self, start_pos, end_pos):
        """Calcule un chemin courbe avec points de contrôle"""
        # Point de contrôle au milieu avec décalage
        mid_x = (start_pos.x() + end_pos.x()) / 2
        mid_y = (start_pos.y() + end_pos.y()) / 2
        
        # Ajouter un décalage pour la courbure
        offset = 50
        if abs(end_pos.x() - start_pos.x()) > abs(end_pos.y() - start_pos.y()):
            # Courbure verticale
            control_point = QPointF(mid_x, mid_y + offset)
        else:
            # Courbure horizontale
            control_point = QPointF(mid_x + offset, mid_y)
            
        return [start_pos, control_point, end_pos]
        
    def calculate_stepped_path(self, start_pos, end_pos):
        """Calcule un chemin en escalier"""
        # Créer des marches horizontales et verticales
        if abs(end_pos.x() - start_pos.x()) > abs(end_pos.y() - start_pos.y()):
            # Escalier horizontal
            step1 = QPointF(end_pos.x(), start_pos.y())
            return [start_pos, step1, end_pos]
        else:
            # Escalier vertical
            step1 = QPointF(start_pos.x(), end_pos.y())
            return [start_pos, step1, end_pos]
        
    def update_visual_path(self):
        """Met à jour le chemin visuel"""
        if len(self.path_points) < 2:
            return
            
        path = QPainterPath()
        path.moveTo(self.path_points[0])
        
        for i in range(1, len(self.path_points)):
            path.lineTo(self.path_points[i])
            
        self.setPath(path)
        
    def add_manual_point(self, point: QPointF):
        """Ajoute un point de contrôle manuel"""
        self.is_manual = True
        self.manual_points.append(point)
        self.update_path()
        
    def remove_manual_point(self, index: int):
        """Retire un point de contrôle manuel"""
        if 0 <= index < len(self.manual_points):
            self.manual_points.pop(index)
            if not self.manual_points:
                self.is_manual = False
            self.update_path()
            
    def clear_manual_points(self):
        """Efface tous les points manuels"""
        self.is_manual = False
        self.manual_points.clear()
        self.update_path()
        
    def get_connection_points(self) -> List[QPointF]:
        """Retourne tous les points de la connexion"""
        return self.path_points.copy()
        
    def set_connection_points(self, points: List[QPointF]):
        """Définit les points de la connexion"""
        if len(points) >= 2:
            self.path_points = points
            self.update_visual_path() 

    def create_control_points(self):
        """Crée les points de contrôle visibles pour l'édition manuelle"""
        self.control_points.clear()
        
        if len(self.path_points) < 2:
            return
            
        # Créer des points de contrôle pour chaque segment
        for i in range(1, len(self.path_points) - 1):
            control_point = QGraphicsEllipseItem(-4, -4, 8, 8)
            control_point.setPos(self.path_points[i])
            control_point.setPen(QPen(QColor(255, 255, 0), 1))
            control_point.setBrush(QBrush(QColor(255, 255, 0, 150)))
            control_point.setZValue(10)
            control_point.setVisible(False)  # Visible seulement en mode édition
            
            # Stocker les informations du point de contrôle
            self.control_points.append({
                'item': control_point,
                'index': i,
                'pos': self.path_points[i]
            })
            
    def show_control_points(self, show=True):
        """Affiche ou masque les points de contrôle"""
        for cp in self.control_points:
            cp['item'].setVisible(show)
            
    def mousePressEvent(self, event):
        """Gère l'événement de clic sur la connexion"""
        if event.button() == Qt.LeftButton:
            # Vérifier si on clique sur un point de contrôle
            pos = event.pos()
            for cp in self.control_points:
                if cp['item'].contains(cp['item'].mapFromParent(pos)):
                    self.selected_control_point = cp
                    self.setCursor(Qt.SizeAllCursor)
                    event.accept()
                    return
                    
            # Double-clic pour éditer le mode de raidissement
            if event.type() == event.MouseButtonDblClick:
                self.show_stiffness_menu(event.screenPos())
                event.accept()
                return
                
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Gère l'événement de mouvement"""
        if self.selected_control_point:
            # Déplacer le point de contrôle
            new_pos = event.pos()
            self.selected_control_point['pos'] = new_pos
            self.selected_control_point['item'].setPos(new_pos)
            
            # Mettre à jour le chemin
            self.update_path_from_control_points()
            event.accept()
            return
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Gère l'événement de relâchement"""
        if event.button() == Qt.LeftButton:
            self.selected_control_point = None
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseReleaseEvent(event)
        
    def update_path_from_control_points(self):
        """Met à jour le chemin à partir des points de contrôle"""
        if not self.path_points:
            return
            
        # Reconstruire le chemin avec les nouveaux points de contrôle
        new_path = [self.path_points[0]]  # Point de départ
        
        for cp in self.control_points:
            new_path.append(cp['pos'])
            
        new_path.append(self.path_points[-1])  # Point d'arrivée
        
        self.path_points = new_path
        self.update_visual_path()
        
    def show_stiffness_menu(self, pos):
        """Affiche le menu pour changer le mode de raidissement"""
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu()
        
        for mode, name in self.get_stiffness_modes():
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, m=mode: self.set_stiffness_mode(m))
            
        menu.exec_(pos) 

    def auto_connect_new_item(self, new_item):
        """Connecte automatiquement un nouvel élément aux éléments existants"""
        try:
            # Ajouter l'élément comme obstacle
            self.add_obstacle(new_item)
            
            # Trouver les éléments existants à proximité
            nearby_items = self.find_nearby_items(new_item)
            
            # Créer des connexions automatiques si nécessaire
            for item in nearby_items:
                if self.should_auto_connect(new_item, item):
                    # Créer une connexion intelligente
                    connection = SmartConnection(new_item, item, self)
                    # La connexion sera gérée par le canvas
                    return connection
                    
        except Exception as e:
            print(f"Erreur dans auto_connect_new_item: {e}")
            return None
    
    def find_nearby_items(self, item, max_distance=200):
        """Trouve les éléments à proximité"""
        nearby = []
        item_pos = item.pos()
        
        # Cette méthode sera implémentée selon les besoins
        # Pour l'instant, retourner une liste vide
        return nearby
    
    def should_auto_connect(self, item1, item2):
        """Détermine si deux éléments doivent être connectés automatiquement"""
        # Logique simple : connecter si les éléments sont proches
        distance = self.heuristic(item1.pos(), item2.pos())
        return distance < 150  # Distance de connexion automatique 