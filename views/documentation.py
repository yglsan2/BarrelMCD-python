from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any
from ..models.entity import Entity
from ..models.association import Association
from .error_handler import ErrorHandler
import os
import datetime

class DocumentationGenerator(QObject):
    """Générateur de documentation"""
    
    # Signaux
    documentation_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_handler = ErrorHandler(self)
        
    def generate_documentation(self, entities: List[Entity], associations: List[Association], output_dir: str):
        """Génère la documentation du modèle"""
        try:
            # Création du répertoire de sortie
            os.makedirs(output_dir, exist_ok=True)
            
            # Génération du fichier HTML
            html_path = os.path.join(output_dir, "documentation.html")
            self._generate_html(entities, associations, html_path)
            
            # Génération du fichier Markdown
            md_path = os.path.join(output_dir, "documentation.md")
            self._generate_markdown(entities, associations, md_path)
            
            # Génération du fichier PDF
            pdf_path = os.path.join(output_dir, "documentation.pdf")
            self._generate_pdf(entities, associations, pdf_path)
            
            self.documentation_generated.emit(output_dir)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération de la documentation")
            self.error_occurred.emit(str(e))
            
    def _generate_html(self, entities: List[Entity], associations: List[Association], output_path: str):
        """Génère la documentation en HTML"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("<!DOCTYPE html>\n")
                f.write("<html>\n")
                f.write("<head>\n")
                f.write("<meta charset='utf-8'>\n")
                f.write("<title>Documentation du modèle de données</title>\n")
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 40px; }\n")
                f.write("h1 { color: #2c3e50; }\n")
                f.write("h2 { color: #34495e; }\n")
                f.write("table { border-collapse: collapse; width: 100%; margin: 20px 0; }\n")
                f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n")
                f.write("th { background-color: #f5f5f5; }\n")
                f.write("</style>\n")
                f.write("</head>\n")
                f.write("<body>\n")
                
                # En-tête
                f.write(f"<h1>Documentation du modèle de données</h1>\n")
                f.write(f"<p>Généré le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>\n")
                
                # Entités
                f.write("<h2>Entités</h2>\n")
                for entity in entities:
                    f.write(f"<h3>{entity.name}</h3>\n")
                    f.write("<table>\n")
                    f.write("<tr><th>Attribut</th><th>Type</th><th>Contraintes</th></tr>\n")
                    for attr in entity.attributes:
                        constraints = []
                        if attr.is_primary_key:
                            constraints.append("Clé primaire")
                        if attr.is_unique:
                            constraints.append("Unique")
                        if attr.is_not_null:
                            constraints.append("Non nul")
                        f.write(f"<tr><td>{attr.name}</td><td>{attr.data_type}</td><td>{', '.join(constraints)}</td></tr>\n")
                    f.write("</table>\n")
                    
                # Associations
                f.write("<h2>Associations</h2>\n")
                f.write("<table>\n")
                f.write("<tr><th>Source</th><th>Type</th><th>Cardinalité</th><th>Cible</th></tr>\n")
                for assoc in associations:
                    f.write(f"<tr><td>{assoc.source.name}</td><td>{assoc.type}</td><td>{assoc.cardinality}</td><td>{assoc.target.name}</td></tr>\n")
                f.write("</table>\n")
                
                f.write("</body>\n")
                f.write("</html>\n")
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du HTML")
            raise
            
    def _generate_markdown(self, entities: List[Entity], associations: List[Association], output_path: str):
        """Génère la documentation en Markdown"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                # En-tête
                f.write("# Documentation du modèle de données\n\n")
                f.write(f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
                
                # Entités
                f.write("## Entités\n\n")
                for entity in entities:
                    f.write(f"### {entity.name}\n\n")
                    f.write("| Attribut | Type | Contraintes |\n")
                    f.write("|----------|------|-------------|\n")
                    for attr in entity.attributes:
                        constraints = []
                        if attr.is_primary_key:
                            constraints.append("Clé primaire")
                        if attr.is_unique:
                            constraints.append("Unique")
                        if attr.is_not_null:
                            constraints.append("Non nul")
                        f.write(f"| {attr.name} | {attr.data_type} | {', '.join(constraints)} |\n")
                    f.write("\n")
                    
                # Associations
                f.write("## Associations\n\n")
                f.write("| Source | Type | Cardinalité | Cible |\n")
                f.write("|--------|------|-------------|-------|\n")
                for assoc in associations:
                    f.write(f"| {assoc.source.name} | {assoc.type} | {assoc.cardinality} | {assoc.target.name} |\n")
                    
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du Markdown")
            raise
            
    def _generate_pdf(self, entities: List[Entity], associations: List[Association], output_path: str):
        """Génère la documentation en PDF"""
        try:
            # Utilisation de reportlab pour la génération PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Style personnalisé pour les titres
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            
            # En-tête
            elements.append(Paragraph("Documentation du modèle de données", title_style))
            elements.append(Paragraph(f"Généré le {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Entités
            elements.append(Paragraph("Entités", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            for entity in entities:
                elements.append(Paragraph(entity.name, styles['Heading3']))
                
                # Table des attributs
                data = [['Attribut', 'Type', 'Contraintes']]
                for attr in entity.attributes:
                    constraints = []
                    if attr.is_primary_key:
                        constraints.append("Clé primaire")
                    if attr.is_unique:
                        constraints.append("Unique")
                    if attr.is_not_null:
                        constraints.append("Non nul")
                    data.append([attr.name, attr.data_type, ', '.join(constraints)])
                    
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
                
            # Associations
            elements.append(Paragraph("Associations", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            data = [['Source', 'Type', 'Cardinalité', 'Cible']]
            for assoc in associations:
                data.append([assoc.source.name, assoc.type, assoc.cardinality, assoc.target.name])
                
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
            # Génération du PDF
            doc.build(elements)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du PDF")
            raise 