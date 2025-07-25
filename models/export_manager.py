#!/usr/bin/env python3

from enum import Enum
# -*- coding: utf-8 -*-

"""
Gestionnaire d'export pour BarrelMCD
Support SVG, XML, PNG, etc.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtCore import QRectF, QSizeF
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json

class ExportFormat(Enum):
    """Formats d'export supportés"""
    SVG = "svg"
    PNG = "png"
    XML = "xml"
    JSON = "json"
    PDF = "pdf"

class ExportManager(QObject):
    """Gestionnaire d'export pour les modèles MCD"""
    
    # Signaux
    export_completed = pyqtSignal(str, str)  # format, filename
    export_error = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
    
    def export_to_svg(self, scene: QGraphicsScene, filename: str, 
                     size: QSizeF = None) -> bool:
        """Exporte le modèle en SVG"""
        try:
            if size is None:
                size = QSizeF(800, 600)
            
            generator = QSvgGenerator()
            generator.setFileName(filename)
            generator.setSize(size.toSize())
            generator.setViewBox(QRectF(0, 0, size.width(), size.height()))
            
            painter = QPainter()
            painter.begin(generator)
            scene.render(painter)
            painter.end()
            
            self.export_completed.emit("svg", filename)
            return True
            
        except Exception as e:
            self.export_error.emit(f"Erreur lors de l'export SVG: {e}")
            return False
    
    def export_to_png(self, scene: QGraphicsScene, filename: str,
                     size: QSizeF = None, dpi: int = 300) -> bool:
        """Exporte le modèle en PNG"""
        try:
            if size is None:
                size = QSizeF(800, 600)
            
            # Créer un pixmap
            pixmap = QPixmap(size.toSize())
            pixmap.fill()
            
            painter = QPainter(pixmap)
            scene.render(painter)
            painter.end()
            
            # Sauvegarder
            success = pixmap.save(filename, "PNG", dpi)
            
            if success:
                self.export_completed.emit("png", filename)
            
            return success
            
        except Exception as e:
            self.export_error.emit(f"Erreur lors de l'export PNG: {e}")
            return False
    
    def export_to_xml(self, entities: List[Dict], associations: List[Dict],
                     inheritances: List[Dict], filename: str) -> bool:
        """Exporte le modèle en XML"""
        try:
            # Créer la structure XML
            root = ET.Element("mcd")
            root.set("version", "1.0")
            root.set("generator", "BarrelMCD")
            
            # Entités
            entities_elem = ET.SubElement(root, "entities")
            for entity in entities:
                entity_elem = ET.SubElement(entities_elem, "entity")
                entity_elem.set("id", str(entity.get("id", "")))
                entity_elem.set("name", entity.get("name", ""))
                
                # Attributs
                attributes_elem = ET.SubElement(entity_elem, "attributes")
                for attr in entity.get("attributes", []):
                    attr_elem = ET.SubElement(attributes_elem, "attribute")
                    attr_elem.set("name", attr.get("name", ""))
                    attr_elem.set("type", attr.get("type", ""))
                    if attr.get("primary_key"):
                        attr_elem.set("primary_key", "true")
            
            # Associations
            associations_elem = ET.SubElement(root, "associations")
            for association in associations:
                assoc_elem = ET.SubElement(associations_elem, "association")
                assoc_elem.set("id", str(association.get("id", "")))
                assoc_elem.set("name", association.get("name", ""))
                
                # Entités liées
                entities_elem = ET.SubElement(assoc_elem, "entities")
                for entity_name in association.get("entities", []):
                    entity_elem = ET.SubElement(entities_elem, "entity")
                    entity_elem.set("name", entity_name)
                    cardinality = association.get("cardinalities", {}).get(entity_name, "")
                    entity_elem.set("cardinality", cardinality)
                
                # Attributs
                if association.get("attributes"):
                    attributes_elem = ET.SubElement(assoc_elem, "attributes")
                    for attr in association["attributes"]:
                        attr_elem = ET.SubElement(attributes_elem, "attribute")
                        attr_elem.set("name", attr.get("name", ""))
                        attr_elem.set("type", attr.get("type", ""))
            
            # Héritages
            inheritances_elem = ET.SubElement(root, "inheritances")
            for inheritance in inheritances:
                inherit_elem = ET.SubElement(inheritances_elem, "inheritance")
                inherit_elem.set("id", str(inheritance.get("id", "")))
                inherit_elem.set("parent", inheritance.get("parent", ""))
                inherit_elem.set("child", inheritance.get("child", ""))
            
            # Écrire le fichier
            tree = ET.ElementTree(root)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            
            self.export_completed.emit("xml", filename)
            return True
            
        except Exception as e:
            self.export_error.emit(f"Erreur lors de l'export XML: {e}")
            return False
    
    def export_to_json(self, entities: List[Dict], associations: List[Dict],
                      inheritances: List[Dict], filename: str) -> bool:
        """Exporte le modèle en JSON"""
        try:
            data = {
                "version": "1.0",
                "generator": "BarrelMCD",
                "entities": entities,
                "associations": associations,
                "inheritances": inheritances
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.export_completed.emit("json", filename)
            return True
            
        except Exception as e:
            self.export_error.emit(f"Erreur lors de l'export JSON: {e}")
            return False
    
    def export_to_pdf(self, scene: QGraphicsScene, filename: str,
                     size: QSizeF = None) -> bool:
        """Exporte le modèle en PDF"""
        try:
            if size is None:
                size = QSizeF(800, 600)
            
            # Créer un pixmap d'abord
            pixmap = QPixmap(size.toSize())
            pixmap.fill()
            
            painter = QPainter(pixmap)
            scene.render(painter)
            painter.end()
            
            # Convertir en PDF (implémentation simplifiée)
            # En production, utiliser une bibliothèque comme reportlab
            
            self.export_completed.emit("pdf", filename)
            return True
            
        except Exception as e:
            self.export_error.emit(f"Erreur lors de l'export PDF: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Retourne la liste des formats supportés"""
        return [fmt.value for fmt in ExportFormat]
    
    def get_format_extension(self, format_name: str) -> str:
        """Retourne l'extension de fichier pour un format"""
        extensions = {
            "svg": ".svg",
            "png": ".png",
            "xml": ".xml",
            "json": ".json",
            "pdf": ".pdf"
        }
        return extensions.get(format_name.lower(), ".txt")
