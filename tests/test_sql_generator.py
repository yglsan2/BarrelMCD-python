import unittest
from models.sql_generator import SQLGenerator, SQLDialect, SQLStatementType
from models.entity import Entity
from models.data_types import DataTypeManager

class TestSQLGenerator(unittest.TestCase):
    def setUp(self):
        """Initialisation avant chaque test"""
        self.sql_generator = SQLGenerator()
        self.data_type_manager = DataTypeManager()
        
        # Création d'une entité de test
        self.entity = Entity(0, 0, "TestEntity")
        
        # Ajout d'attributs de test
        self.entity.add_attribute("id", "INT")
        self.entity.add_attribute("nom", "VARCHAR(100)")
        self.entity.add_attribute("prix", "DECIMAL(10,2)")
        
    def test_type_conversion(self):
        """Test de la conversion des types de données"""
        # Test pour MySQL
        mysql_type = self.sql_generator.convert_type("VARCHAR", SQLDialect.MYSQL, length=100)
        self.assertEqual(mysql_type, "VARCHAR(100)")
        
        # Test pour PostgreSQL
        postgres_type = self.sql_generator.convert_type("VARCHAR", SQLDialect.POSTGRESQL, length=100)
        self.assertEqual(postgres_type, "VARCHAR(100)")
        
        # Test pour SQL Server
        sqlserver_type = self.sql_generator.convert_type("VARCHAR", SQLDialect.SQLSERVER, length=100)
        self.assertEqual(sqlserver_type, "NVARCHAR(100)")
        
        # Test pour Oracle
        oracle_type = self.sql_generator.convert_type("VARCHAR", SQLDialect.ORACLE, length=100)
        self.assertEqual(oracle_type, "VARCHAR2(100)")
        
        # Test pour SQLite
        sqlite_type = self.sql_generator.convert_type("VARCHAR", SQLDialect.SQLITE, length=100)
        self.assertEqual(sqlite_type, "TEXT")
        
    def test_create_table(self):
        """Test de la génération de CREATE TABLE"""
        # Test pour MySQL
        mysql_sql = self.sql_generator.generate_create_table(self.entity, SQLDialect.MYSQL)
        self.assertIn("CREATE TABLE TestEntity", mysql_sql)
        self.assertIn("id INT", mysql_sql)
        self.assertIn("nom VARCHAR(100)", mysql_sql)
        self.assertIn("prix DECIMAL(10,2)", mysql_sql)
        
        # Test pour PostgreSQL
        postgres_sql = self.sql_generator.generate_create_table(self.entity, SQLDialect.POSTGRESQL)
        self.assertIn("CREATE TABLE TestEntity", postgres_sql)
        self.assertIn("id INTEGER", postgres_sql)
        self.assertIn("nom VARCHAR(100)", postgres_sql)
        self.assertIn("prix NUMERIC(10,2)", postgres_sql)
        
    def test_alter_table(self):
        """Test de la génération de ALTER TABLE"""
        # Création d'un nouvel attribut
        new_attr = {"name": "date_creation", "type": "DATETIME"}
        
        # Test pour MySQL
        mysql_sql = self.sql_generator.generate_alter_table(
            self.entity,
            new_attr,
            SQLDialect.MYSQL
        )
        self.assertIn("ALTER TABLE TestEntity", mysql_sql)
        self.assertIn("ADD COLUMN date_creation DATETIME", mysql_sql)
        
    def test_create_index(self):
        """Test de la génération de CREATE INDEX"""
        # Test pour MySQL
        mysql_sql = self.sql_generator.generate_create_index(
            self.entity,
            "idx_nom",
            ["nom"],
            SQLDialect.MYSQL
        )
        self.assertIn("CREATE INDEX idx_nom", mysql_sql)
        self.assertIn("ON TestEntity (nom)", mysql_sql)
        
        # Test pour PostgreSQL
        postgres_sql = self.sql_generator.generate_create_index(
            self.entity,
            "idx_nom",
            ["nom"],
            SQLDialect.POSTGRESQL
        )
        self.assertIn("CREATE INDEX idx_nom", postgres_sql)
        self.assertIn("ON TestEntity (nom)", postgres_sql)
        
    def test_drop_index(self):
        """Test de la génération de DROP INDEX"""
        # Test pour MySQL
        mysql_sql = self.sql_generator.generate_drop_index(
            self.entity,
            "idx_nom",
            SQLDialect.MYSQL
        )
        self.assertIn("DROP INDEX idx_nom", mysql_sql)
        self.assertIn("ON TestEntity", mysql_sql)
        
        # Test pour PostgreSQL
        postgres_sql = self.sql_generator.generate_drop_index(
            self.entity,
            "idx_nom",
            SQLDialect.POSTGRESQL
        )
        self.assertIn("DROP INDEX idx_nom", postgres_sql)
        
    def test_sql_analysis(self):
        """Test de l'analyse SQL"""
        # Test d'analyse CREATE TABLE
        create_sql = "CREATE TABLE TestTable (id INT PRIMARY KEY)"
        analysis = self.sql_generator.analyze_sql(create_sql)
        self.assertEqual(analysis[0], SQLStatementType.CREATE_TABLE)
        
        # Test d'analyse ALTER TABLE
        alter_sql = "ALTER TABLE TestTable ADD COLUMN name VARCHAR(100)"
        analysis = self.sql_generator.analyze_sql(alter_sql)
        self.assertEqual(analysis[0], SQLStatementType.ALTER_TABLE)
        
    def test_sql_conversion(self):
        """Test de la conversion SQL entre dialectes"""
        # SQL source en MySQL
        source_sql = """
        CREATE TABLE Users (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        )
        """
        
        # Conversion vers PostgreSQL
        postgres_sql = self.sql_generator.convert_sql(
            source_sql,
            SQLDialect.MYSQL,
            SQLDialect.POSTGRESQL
        )
        self.assertIn("CREATE TABLE Users", postgres_sql)
        self.assertIn("id INTEGER", postgres_sql)
        self.assertIn("name VARCHAR(100)", postgres_sql)
        self.assertIn("email VARCHAR(255)", postgres_sql)
        
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Test avec un type de données invalide
        with self.assertRaises(ValueError):
            self.sql_generator.convert_type("INVALID_TYPE", SQLDialect.MYSQL)
            
        # Test avec un dialecte invalide
        with self.assertRaises(ValueError):
            self.sql_generator.convert_type("VARCHAR", "INVALID_DIALECT")
            
        # Test avec un SQL invalide
        with self.assertRaises(ValueError):
            self.sql_generator.analyze_sql("INVALID SQL")
            
if __name__ == '__main__':
    unittest.main() 