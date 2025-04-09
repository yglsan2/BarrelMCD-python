import os
import sys
import inspect
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import re

class DocGenerator:
    """
    Générateur de documentation au format HTML style Javadoc.
    
    Cette classe analyse le code source Python et génère une documentation HTML
    complète à partir des docstrings, similaire au format Javadoc.
    
    Features:
        - Génération de documentation HTML
        - Support des docstrings Google style
        - Navigation par classe/méthode
        - Recherche intégrée
        - Support multilingue
    """
    
    def __init__(self, output_dir: str = "docs"):
        """
        Initialise le générateur de documentation.
        
        Args:
            output_dir: Répertoire de sortie pour la documentation
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir = Path(__file__).parent / "templates" / "doc"
        self.current_module = ""
        self.current_class = ""
        
    def generate_docs(self, source_dir: str) -> bool:
        """
        Génère la documentation pour un répertoire source.
        
        Args:
            source_dir: Répertoire contenant le code source
            
        Returns:
            bool: True si la génération a réussi
        """
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                logging.error(f"Le répertoire source n'existe pas: {source_dir}")
                return False
                
            # Générer l'index principal
            self._generate_index(source_path)
            
            # Analyser tous les fichiers Python
            for python_file in source_path.rglob("*.py"):
                self._process_file(python_file)
                
            # Copier les ressources (CSS, JS, images)
            self._copy_resources()
            
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de la génération de la documentation: {e}")
            return False
            
    def _process_file(self, file_path: Path) -> None:
        """
        Traite un fichier Python et génère sa documentation.
        
        Args:
            file_path: Chemin du fichier Python
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Analyser le fichier
            tree = ast.parse(content)
            
            # Extraire les informations du module
            module_doc = ast.get_docstring(tree)
            self.current_module = file_path.stem
            
            # Générer la documentation du module
            self._generate_module_doc(file_path, module_doc, tree)
            
        except Exception as e:
            logging.error(f"Erreur lors du traitement du fichier {file_path}: {e}")
            
    def _generate_module_doc(self, file_path: Path, module_doc: Optional[str], tree: ast.AST) -> None:
        """
        Génère la documentation HTML pour un module.
        
        Args:
            file_path: Chemin du fichier
            module_doc: Docstring du module
            tree: AST du module
        """
        try:
            # Créer le répertoire de sortie pour le module
            module_dir = self.output_dir / self.current_module
            module_dir.mkdir(exist_ok=True)
            
            # Générer le fichier HTML du module
            with open(module_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write(self._generate_module_html(file_path, module_doc, tree))
                
        except Exception as e:
            logging.error(f"Erreur lors de la génération de la documentation du module {file_path}: {e}")
            
    def _generate_module_html(self, file_path: Path, module_doc: Optional[str], tree: ast.AST) -> str:
        """
        Génère le HTML pour un module.
        
        Args:
            file_path: Chemin du fichier
            module_doc: Docstring du module
            tree: AST du module
            
        Returns:
            str: HTML généré
        """
        html = []
        
        # En-tête
        html.append("<!DOCTYPE html>")
        html.append("<html lang='fr'>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <title>Documentation - " + self.current_module + "</title>")
        html.append("    <link rel='stylesheet' href='../style.css'>")
        html.append("</head>")
        html.append("<body>")
        
        # Navigation
        html.append(self._generate_navigation())
        
        # Contenu principal
        html.append("<div class='content'>")
        html.append(f"<h1>Module {self.current_module}</h1>")
        
        # Description du module
        if module_doc:
            html.append("<div class='module-description'>")
            html.append(self._format_docstring(module_doc))
            html.append("</div>")
            
        # Classes
        html.append("<h2>Classes</h2>")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                html.append(self._generate_class_html(node))
                
        # Fonctions
        html.append("<h2>Fonctions</h2>")
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Vérifier si la fonction n'est pas une méthode de classe
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        for child in parent.body:
                            if child == node:
                                is_method = True
                                break
                if not is_method:
                    html.append(self._generate_function_html(node))
                
        html.append("</div>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
        
    def _generate_class_html(self, node: ast.ClassDef) -> str:
        """
        Génère le HTML pour une classe.
        
        Args:
            node: Nœud AST de la classe
            
        Returns:
            str: HTML généré
        """
        html = []
        self.current_class = node.name
        
        # En-tête de la classe
        html.append(f"<div class='class' id='{node.name}'>")
        html.append(f"<h3>{node.name}</h3>")
        
        # Description de la classe
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            html.append("<div class='class-description'>")
            html.append(self._format_docstring(node.body[0].value.s))
            html.append("</div>")
            
        # Méthodes
        html.append("<h4>Méthodes</h4>")
        for method in node.body:
            if isinstance(method, ast.FunctionDef):
                html.append(self._generate_method_html(method))
                
        html.append("</div>")
        return "\n".join(html)
        
    def _generate_method_html(self, node: ast.FunctionDef) -> str:
        """
        Génère le HTML pour une méthode.
        
        Args:
            node: Nœud AST de la méthode
            
        Returns:
            str: HTML généré
        """
        html = []
        
        # En-tête de la méthode
        html.append(f"<div class='method' id='{self.current_class}.{node.name}'>")
        html.append(f"<h5>{node.name}</h5>")
        
        # Description de la méthode
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            html.append("<div class='method-description'>")
            html.append(self._format_docstring(node.body[0].value.s))
            html.append("</div>")
            
        # Paramètres
        if node.args.args:
            html.append("<h6>Paramètres</h6>")
            html.append("<ul>")
            for arg in node.args.args:
                html.append(f"<li>{arg.arg}</li>")
            html.append("</ul>")
            
        # Type de retour
        if node.returns:
            html.append("<h6>Retourne</h6>")
            html.append(f"<p>{self._get_type_name(node.returns)}</p>")
            
        html.append("</div>")
        return "\n".join(html)
        
    def _generate_function_html(self, node: ast.FunctionDef) -> str:
        """
        Génère le HTML pour une fonction.
        
        Args:
            node: Nœud AST de la fonction
            
        Returns:
            str: HTML généré
        """
        html = []
        
        # En-tête de la fonction
        html.append(f"<div class='function' id='{node.name}'>")
        html.append(f"<h3>{node.name}</h3>")
        
        # Description de la fonction
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            html.append("<div class='function-description'>")
            html.append(self._format_docstring(node.body[0].value.s))
            html.append("</div>")
            
        # Paramètres
        if node.args.args:
            html.append("<h4>Paramètres</h4>")
            html.append("<ul>")
            for arg in node.args.args:
                html.append(f"<li>{arg.arg}</li>")
            html.append("</ul>")
            
        # Type de retour
        if node.returns:
            html.append("<h4>Retourne</h4>")
            html.append(f"<p>{self._get_type_name(node.returns)}</p>")
            
        html.append("</div>")
        return "\n".join(html)
        
    def _format_docstring(self, docstring: str) -> str:
        """
        Formate une docstring en HTML.
        
        Args:
            docstring: Texte de la docstring
            
        Returns:
            str: HTML formaté
        """
        if not docstring:
            return ""
            
        # Convertir les sauts de ligne en <br>
        html = docstring.replace("\n", "<br>")
        
        # Formater les sections spéciales
        html = re.sub(r'Args:(.*?)(?=Returns:|Raises:|$)', 
                     r'<h6>Paramètres</h6>\1', 
                     html, 
                     flags=re.DOTALL)
                     
        html = re.sub(r'Returns:(.*?)(?=Raises:|$)',
                     r'<h6>Retourne</h6>\1',
                     html,
                     flags=re.DOTALL)
                     
        html = re.sub(r'Raises:(.*?)$',
                     r'<h6>Lève</h6>\1',
                     html,
                     flags=re.DOTALL)
                     
        return html
        
    def _get_type_name(self, node: ast.AST) -> str:
        """
        Obtient le nom d'un type à partir d'un nœud AST.
        
        Args:
            node: Nœud AST du type
            
        Returns:
            str: Nom du type
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_type_name(node.value)}[{self._get_type_name(node.slice)}]"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_type_name(node.value)}.{node.attr}"
        return "Unknown"
        
    def _generate_navigation(self) -> str:
        """
        Génère la barre de navigation HTML.
        
        Returns:
            str: HTML de la navigation
        """
        html = []
        html.append("<nav class='navigation'>")
        html.append("    <div class='nav-header'>")
        html.append("        <h2>Navigation</h2>")
        html.append("    </div>")
        html.append("    <div class='nav-content'>")
        html.append("        <ul>")
        html.append(f"            <li><a href='../index.html'>Accueil</a></li>")
        html.append(f"            <li><a href='index.html'>{self.current_module}</a></li>")
        if self.current_class:
            html.append(f"            <li><a href='#{self.current_class}'>{self.current_class}</a></li>")
        html.append("        </ul>")
        html.append("    </div>")
        html.append("</nav>")
        return "\n".join(html)
        
    def _generate_index(self, source_path: Path) -> None:
        """
        Génère la page d'index principale.
        
        Args:
            source_path: Chemin du répertoire source
        """
        try:
            html = []
            html.append("<!DOCTYPE html>")
            html.append("<html lang='fr'>")
            html.append("<head>")
            html.append("    <meta charset='UTF-8'>")
            html.append("    <title>Documentation - Index</title>")
            html.append("    <link rel='stylesheet' href='style.css'>")
            html.append("</head>")
            html.append("<body>")
            
            # En-tête
            html.append("<header>")
            html.append("    <h1>Documentation du projet</h1>")
            html.append("    <p>Générée le " + datetime.now().strftime("%d/%m/%Y %H:%M") + "</p>")
            html.append("</header>")
            
            # Liste des modules
            html.append("<div class='content'>")
            html.append("<h2>Modules</h2>")
            html.append("<ul>")
            
            for python_file in source_path.rglob("*.py"):
                module_name = python_file.stem
                html.append(f"    <li><a href='{module_name}/index.html'>{module_name}</a></li>")
                
            html.append("</ul>")
            html.append("</div>")
            
            html.append("</body>")
            html.append("</html>")
            
            # Écrire l'index
            with open(self.output_dir / "index.html", 'w', encoding='utf-8') as f:
                f.write("\n".join(html))
                
        except Exception as e:
            logging.error(f"Erreur lors de la génération de l'index: {e}")
            
    def _copy_resources(self) -> None:
        """Copie les ressources (CSS, JS, images) dans le répertoire de documentation."""
        try:
            # Copier le CSS
            css_content = """
            /* Style de base */
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
            }
            
            /* Navigation */
            .navigation {
                width: 250px;
                background-color: #f5f5f5;
                padding: 20px;
                height: 100vh;
                position: fixed;
            }
            
            /* Contenu principal */
            .content {
                margin-left: 290px;
                padding: 20px;
            }
            
            /* Classes et méthodes */
            .class, .method, .function {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            
            .function {
                background-color: #f8f9fa;
            }
            
            .function-description {
                margin: 10px 0;
                padding: 10px;
                background-color: #fff;
                border-radius: 3px;
            }
            
            /* Titres */
            h1, h2, h3, h4, h5, h6 {
                color: #333;
            }
            
            /* Liens */
            a {
                color: #0066cc;
                text-decoration: none;
            }
            
            a:hover {
                text-decoration: underline;
            }
            """
            
            with open(self.output_dir / "style.css", 'w', encoding='utf-8') as f:
                f.write(css_content)
                
        except Exception as e:
            logging.error(f"Erreur lors de la copie des ressources: {e}")
            
    def generate_all(self, source_dir: str) -> bool:
        """
        Génère toute la documentation.
        
        Args:
            source_dir: Répertoire source
            
        Returns:
            bool: True si la génération a réussi
        """
        try:
            # Vérifier le répertoire source
            if not os.path.exists(source_dir):
                logging.error(f"Le répertoire source n'existe pas: {source_dir}")
                return False
                
            # Générer la documentation
            success = self.generate_docs(source_dir)
            
            if success:
                logging.info(f"Documentation générée avec succès dans {self.output_dir}")
            else:
                logging.error("Erreur lors de la génération de la documentation")
                
            return success
            
        except Exception as e:
            logging.error(f"Erreur lors de la génération de la documentation: {e}")
            return False 