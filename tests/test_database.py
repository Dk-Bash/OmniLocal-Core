import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import DATABASE_PATH
from database.sqlite_manager import SQLiteManager


def test_database_creation_and_tables():
    """
    Prueba que la base de datos se crea correctamente
    y que existen las tablas users, memories y conversations.
    """
    # Usar un gestor de base de datos con la ruta configurada
    db = SQLiteManager()
    
    # 1. Probar conexión y creación de tablas
    db.connect()
    db.create_tables()

    # Verificar que el archivo de base de datos existe en disco
    assert os.path.exists(DATABASE_PATH), f"El archivo {DATABASE_PATH} no se ha creado."

    # 2. Consultar las tablas existentes en sqlite_master
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    db.close()

    # 3. Verificar que las tres tablas obligatorias están presentes
    assert "users" in tables, "La tabla 'users' no fue encontrada en la base de datos."
    assert "memories" in tables, "La tabla 'memories' no fue encontrada en la base de datos."
    assert "conversations" in tables, "La tabla 'conversations' no fue encontrada en la base de datos."


if __name__ == "__main__":
    test_database_creation_and_tables()
    print("✅ test_database_creation_and_tables: Todas las verificaciones pasaron correctamente.")
