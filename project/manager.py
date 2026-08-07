from typing import List, Optional

from database.sqlite_manager import SQLiteManager
from project.models import Project


class ProjectManager:
    """
    Gestor de proyectos de trabajo para OmniLocal-Core (Bloque 14 --
    Project Workspace Foundation). Mismo patrón que GoalManager/MemoryManager:
    valida con Pydantic, delega el acceso a datos a SQLiteManager.
    """

    def __init__(self, db_manager: Optional[SQLiteManager] = None):
        if db_manager is None:
            self.db_manager = SQLiteManager()
            self.db_manager.connect()
            self.db_manager.create_tables()
        else:
            self.db_manager = db_manager

    def create_project(self, name: str, path: str, technologies: Optional[str] = None, structure_summary: Optional[str] = None) -> int:
        project_obj = Project(name=name, path=path, technologies=technologies, structure_summary=structure_summary)  # valida antes de insertar
        return self.db_manager.insert_project(
            project_obj.name, project_obj.path, technologies=project_obj.technologies, structure_summary=project_obj.structure_summary
        )

    def get_project(self, project_id: int) -> Optional[Project]:
        row = self.db_manager.get_project(project_id)
        return Project(**row) if row else None

    def get_project_by_path(self, path: str) -> Optional[Project]:
        row = self.db_manager.get_project_by_path(path)
        return Project(**row) if row else None

    def list_projects(self) -> List[Project]:
        rows = self.db_manager.get_projects()
        return [Project(**row) for row in rows]

    def update_project(
        self,
        project_id: int,
        objective: Optional[str] = None,
        technologies: Optional[str] = None,
        structure_summary: Optional[str] = None,
        status_summary: Optional[str] = None,
        reindex: bool = False,
    ) -> bool:
        return self.db_manager.update_project(
            project_id, objective=objective, technologies=technologies,
            structure_summary=structure_summary, status_summary=status_summary, reindex=reindex,
        )

    def delete_project(self, project_id: int) -> bool:
        return self.db_manager.delete_project(project_id)
