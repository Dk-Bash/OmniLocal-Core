from typing import Optional, List
from database.sqlite_manager import SQLiteManager
from user.models import UserProfile, UserPreference
from app.logger import get_logger

logger = get_logger("user.manager")


class UserManager:
    """
    Gestor de perfiles y preferencias de usuario para OmniLocal-Core.
    Administra la persistencia de usuarios y sus preferencias sin escribir SQL directo,
    delegando todas las operaciones al SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        self.db_manager = db_manager or SQLiteManager()
        self.db_manager.create_tables()
        logger.info("UserManager inicializado correctamente.")

    def create_profile(self, username: str, display_name: str, language: str = "es") -> int:
        """
        Crea un nuevo perfil de usuario y devuelve su ID generado.
        """
        user_id = self.db_manager.insert_user_profile(
            username=username,
            display_name=display_name,
            language=language
        )
        logger.info(f"Perfil de usuario '{username}' creado con ID {user_id}.")
        return user_id

    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Obtiene el perfil de un usuario por su ID.
        """
        row = self.db_manager.get_user_profile(user_id)
        if not row:
            logger.warning(f"No se encontró perfil de usuario para ID {user_id}.")
            return None
        return UserProfile(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            language=row["language"],
            created_at=row["created_at"]
        )

    def update_profile(self, user_id: int, display_name: Optional[str] = None, language: Optional[str] = None) -> bool:
        """
        Actualiza la información visible (nombre visible, idioma) de un usuario.
        """
        success = self.db_manager.update_user_profile(
            user_id=user_id,
            display_name=display_name,
            language=language
        )
        if success:
            logger.info(f"Perfil de usuario ID {user_id} actualizado con éxito.")
        else:
            logger.warning(f"No se pudo actualizar el perfil de usuario ID {user_id}.")
        return success

    def set_preference(self, user_id: int, key: str, value: str) -> int:
        """
        Guarda o actualiza una preferencia de usuario y devuelve el ID de la preferencia.
        """
        pref_id = self.db_manager.set_user_preference(
            user_id=user_id,
            key=key,
            value=value
        )
        logger.info(f"Preferencia '{key}'='{value}' guardada para usuario ID {user_id} (ID pref: {pref_id}).")
        return pref_id

    def get_preferences(self, user_id: int) -> List[UserPreference]:
        """
        Obtiene todas las preferencias registradas para un usuario.
        """
        rows = self.db_manager.get_user_preferences(user_id)
        preferences = []
        for row in rows:
            preferences.append(
                UserPreference(
                    id=row["id"],
                    user_id=row["user_id"],
                    key=row["key"],
                    value=row["value"],
                    created_at=row["created_at"]
                )
            )
        return preferences
