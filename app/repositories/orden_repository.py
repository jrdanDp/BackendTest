import re
from datetime import date
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.orden import Orden, AsignacionOrden
from app.repositories.base import BaseRepository


def slugify_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", ".", name.strip().lower())
    return cleaned.strip(".")


class OrdenRepository(BaseRepository[Orden]):
    """
    Repositorio especializado en operaciones de base de datos para
    las tablas 'ordenes', 'asignacion_ordenes' y vinculación con 'personal' y 'clientes'.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Orden, session)

    async def get_valid_client_ids(self) -> Set[int]:
        """Obtiene el conjunto de id_ab existentes en la tabla clientes."""
        result = await self.session.execute(text("SELECT id_ab FROM public.clientes"))
        return set(row[0] for row in result.fetchall())

    async def get_technicians_map(self) -> Dict[str, int]:
        """Retorna un mapeo {NOMBRE_MAYUSCULAS: id_personal} para el personal."""
        result = await self.session.execute(text("SELECT id_personal, UPPER(TRIM(nombre)) FROM public.personal"))
        return {row[1]: row[0] for row in result.fetchall()}

    async def get_or_create_technician(self, nombre_tecnico: str, tech_map: Dict[str, int]) -> Tuple[int, bool]:
        """
        Retorna el id_personal del técnico. Si no existe, lo crea automáticamente
        con rol Técnico (rol_id = 3) y estado ACTIVO.
        """
        nombre_clean = nombre_tecnico.strip()
        nombre_upper = nombre_clean.upper()

        if nombre_upper in tech_map:
            return tech_map[nombre_upper], False

        # Registrar técnico nuevo
        email = f"tecnico.{slugify_name(nombre_clean)}@chiclin.net"
        query = text("""
            INSERT INTO public.personal (nombre, email, password_hash, rol_id, estado)
            VALUES (:nombre, :email, :pwd, 3, 'ACTIVO')
            ON CONFLICT (email) DO UPDATE SET nombre = EXCLUDED.nombre
            RETURNING id_personal;
        """)
        result = await self.session.execute(
            query,
            {"nombre": nombre_clean, "email": email, "pwd": "$2b$12$default_hash_for_technician"}
        )
        new_id = result.scalar_one()
        tech_map[nombre_upper] = new_id
        return new_id, True

    async def sync_ordenes_and_asignaciones(self, df_normalizado: pd.DataFrame) -> Dict[str, int]:
        """
        Inserta o actualiza las órdenes en la tabla 'ordenes' y genera
        las correspondientes asignaciones en 'asignacion_ordenes'.
        """
        valid_clients = await self.get_valid_client_ids()
        tech_map = await self.get_technicians_map()

        ordenes_procesadas = 0
        ordenes_insertadas = 0
        asignaciones_creadas = 0
        tecnicos_creados = 0

        # 1. Asegurar registro de todos los técnicos del DataFrame
        tecnicos_unicos = [
            str(t).strip() for t in df_normalizado["tecnico"].dropna().unique() if str(t).strip()
        ]
        for t_name in tecnicos_unicos:
            _, created = await self.get_or_create_technician(t_name, tech_map)
            if created:
                tecnicos_creados += 1

        # 2. Procesar cada orden
        for _, row in df_normalizado.iterrows():
            id_orden = int(row["id_orden"])
            ab_raw = int(row["id_cliente"]) if pd.notna(row["id_cliente"]) else None

            # Si el cliente existe en clientes, se asigna; de lo contrario NULL
            id_cliente = ab_raw if ab_raw in valid_clients else None
            estado_orden = str(row["estado_orden"]).strip().upper()

            # Upsert Orden
            stmt_orden = pg_insert(Orden).values(
                id_orden=id_orden,
                id_cliente=id_cliente,
                estado_orden=estado_orden,
                f_recepcion=row["f_recepcion"],
                hora_recep=row["hora_recep"],
                f_atencion=row["f_atencion"],
                hora_inicio=row["hora_inicio"],
                hora_fin=row["hora_fin"],
                obs_recepcion=row["obs_recepcion"],
                obs_descargo=row["obs_descargo"],
                usuario_ing=row["usuario_ing"],
                fecha_ing=row["fecha_ing"]
            ).on_conflict_do_update(
                index_elements=["id_orden"],
                set_={
                    "id_cliente": id_cliente,
                    "estado_orden": estado_orden,
                    "f_recepcion": row["f_recepcion"],
                    "hora_recep": row["hora_recep"],
                    "f_atencion": row["f_atencion"],
                    "hora_inicio": row["hora_inicio"],
                    "hora_fin": row["hora_fin"],
                    "obs_recepcion": row["obs_recepcion"],
                    "obs_descargo": row["obs_descargo"],
                    "usuario_ing": row["usuario_ing"],
                    "fecha_ing": row["fecha_ing"]
                }
            )
            await self.session.execute(stmt_orden)
            ordenes_insertadas += 1

            # 3. Determinar asignación de la orden
            t_name = str(row["tecnico"]).strip().upper() if pd.notna(row["tecnico"]) else None
            id_personal = tech_map.get(t_name) if t_name else None

            # Reglas de estado de asignación:
            # DESCARGADA -> ATENDIDA, REGISTRADA -> PENDIENTE, ANULADA -> RECHAZADA
            if estado_orden == "DESCARGADA":
                estado_asig = "ATENDIDA"
            elif estado_orden == "REGISTRADA":
                estado_asig = "PENDIENTE"
            elif estado_orden == "ANULADA":
                estado_asig = "RECHAZADA"
            else:
                estado_asig = "PENDIENTE"

            f_asig = row["f_recepcion"] or date.today()

            # Revisar si ya existe asignación para esta orden
            existing_asig = await self.session.execute(
                select(AsignacionOrden).where(AsignacionOrden.id_orden == id_orden)
            )
            asig_obj = existing_asig.scalar_one_or_none()

            if asig_obj:
                asig_obj.id_personal = id_personal
                asig_obj.estado_asignacion = estado_asig
                asig_obj.hora_i = row["hora_inicio"]
                asig_obj.hora_f = row["hora_fin"]
            else:
                nueva_asig = AsignacionOrden(
                    id_personal=id_personal,
                    id_orden=id_orden,
                    f_asignacion=f_asig,
                    hora_i=row["hora_inicio"],
                    hora_f=row["hora_fin"],
                    estado_asignacion=estado_asig
                )
                self.session.add(nueva_asig)
                asignaciones_creadas += 1

            ordenes_procesadas += 1

        await self.session.commit()

        return {
            "ordenes_procesadas": ordenes_procesadas,
            "ordenes_sincronizadas": ordenes_insertadas,
            "asignaciones_creadas": asignaciones_creadas,
            "tecnicos_nuevos": tecnicos_creados
        }
