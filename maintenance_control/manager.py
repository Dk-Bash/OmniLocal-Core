from typing import List, Optional
from database.sqlite_manager import SQLiteManager
from maintenance_compliance.manager import MaintenanceComplianceManager
from maintenance_control.models import ControlOptimizationReport


class AutonomousControlManager:
    """Módulo 51: Capa de Optimización de Control Autónomo de Mantenimiento."""

    def __init__(
        self,
        db_manager: Optional[SQLiteManager] = None,
        compliance_manager: Optional[MaintenanceComplianceManager] = None,
    ):
        self.db_manager = db_manager or SQLiteManager()
        self.compliance_manager = (
            compliance_manager or MaintenanceComplianceManager(db_manager=self.db_manager)
        )

    def optimize_control(
        self,
        compliance_id: Optional[int] = None,
    ) -> List[ControlOptimizationReport]:
        """
        Analiza los controles existentes y propone optimizaciones autónomas futuras.
        Trabaja sobre información existente de forma no destructiva ni invasiva.
        """
        reports_to_process = []

        if compliance_id is not None:
            comp = self.db_manager.get_compliance_report(compliance_id)
            if comp:
                reports_to_process.append(comp)
        else:
            compliance_reports = self.db_manager.get_compliance_reports()
            if not compliance_reports:
                # Si no existen reportes de cumplimiento, generarlos vía compliance_manager
                generated_comp = self.compliance_manager.validate_compliance()
                compliance_reports = [
                    self.db_manager.get_compliance_report(c.id) for c in generated_comp if c.id
                ]
            reports_to_process.extend(compliance_reports)

        optimizations: List[ControlOptimizationReport] = []

        for comp in reports_to_process:
            if not comp:
                continue
            c_id = comp["id"]
            score = comp.get("compliance_score", 1.0)

            if score >= 0.9:
                optimization_status = "optimized"
                confidence = 0.95
                improvement_area = "Eficiencia y automatización en ejecución autónoma"
                recommendation = (
                    f"Optimización Excelente: El informe de cumplimiento #{c_id} alcanza {score*100:.0f}%. "
                    f"Se recomienda mantener las políticas actuales e incrementar la aceleración de ciclos."
                )
            elif 0.5 <= score < 0.9:
                optimization_status = "stable"
                confidence = 0.80
                improvement_area = "Ajuste fino de tiempos de respuesta y supervisión"
                recommendation = (
                    f"Optimización Estabilidad: El informe de cumplimiento #{c_id} registra {score*100:.0f}%. "
                    f"Se recomienda ajustar las políticas de advertencia para elevar el nivel de cumplimiento."
                )
            else:
                optimization_status = "needs_improvement"
                confidence = 0.60
                improvement_area = "Remediación urgente de controles y reconfiguración de reglas"
                recommendation = (
                    f"Optimización Requerida: El informe de cumplimiento #{c_id} registra {score*100:.0f}%. "
                    f"Se requiere reconfigurar los parámetros de detención previa para prevenir fallos recurrentes."
                )

            opt_id = self.db_manager.insert_control_optimization(
                compliance_id=c_id,
                optimization_status=optimization_status,
                improvement_area=improvement_area,
                confidence=confidence,
                recommendation=recommendation,
            )

            optimizations.append(
                ControlOptimizationReport(
                    id=opt_id,
                    compliance_id=c_id,
                    optimization_status=optimization_status,
                    improvement_area=improvement_area,
                    confidence=confidence,
                    recommendation=recommendation,
                )
            )

        return optimizations

    def get_control_optimization(self, optimization_id: int) -> Optional[dict]:
        """Obtiene un reporte de optimización de control por ID."""
        return self.db_manager.get_control_optimization(optimization_id)

    def get_control_optimizations(self) -> List[dict]:
        """Obtiene todos los reportes de optimización de control."""
        return self.db_manager.get_control_optimizations()
