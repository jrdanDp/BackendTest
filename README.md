# Backend FastAPI - Arquitectura N Capas (Proyecto de Pruebas / Migración)

Este backend está estructurado siguiendo **buenas prácticas de ingeniería de software** y el patrón de **Arquitectura N Capas (N-Tier)** para desacoplar completamente la lógica de negocio de los controladores HTTP y las dependencias de infraestructura. Esto facilita probar nuevas funciones de forma aislada y migrarlas sin esfuerzo al proyecto principal.

---

## 🏛 Estructura de Capas

```text
app/
├── core/                        # CAPA CORE: Configuración, BD y Excepciones
│   ├── config.py                # Settings centralizados (.env y DATABASE_URL)
│   ├── database.py              # Motor AsyncPG, AsyncSession y DeclarativeBase
│   └── exceptions.py            # Excepciones de negocio y handlers globales HTTP
│
├── models/                      # CAPA DE MODELOS ORM (SQLAlchemy 2.0)
│   └── orden.py                 # Entidades Orden y AsignacionOrden
│
├── schemas/                     # CAPA DOMINIO / DTO (Data Transfer Objects)
│   ├── common.py                # Esquemas genéricos estandarizados (ApiResponse[T])
│   └── automation.py            # Modelos de validación de entrada/salida (Pydantic v2)
│
├── repositories/                # CAPA DE ACCESO A DATOS (Patrón Repositorio)
│   ├── base.py                  # BaseRepository asíncrono para operaciones CRUD
│   └── orden_repository.py      # OrdenRepository (upsert ordenes, asignaciones y técnicos)
│
├── infrastructure/              # CAPA DE INFRAESTRUCTURA (Adaptadores externos)
│   └── scrapper_client.py       # Wrapper desacoplado para Scrapper, Sesiones y Archivos
│
├── services/                    # CAPA DE NEGOCIO / CASOS DE USO
│   └── automation_service.py    # Orquestación de lógica pura (independiente de HTTP/FastAPI)
│
├── api/                         # CAPA DE PRESENTACIÓN (Routers & Controladores)
│   ├── deps.py                  # Inyección de dependencias (get_db, get_service)
│   └── v1/
│       ├── api.py               # Agregador de rutas API v1
│       └── endpoints/
│           ├── health.py        # Health check y estado del sistema / ping a PostgreSQL
│           └── automation.py    # Endpoints HTTP REST (Cobros, Normalización, Órdenes)
│
└── main.py                      # ENTRYPOINT de FastAPI (CORS, Middlewares, Handlers)
```

---

## 🚀 Cómo ejecutar el servidor

### 1. Activar entorno virtual
En Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Iniciar servidor FastAPI con recarga en vivo (hot reload)
```powershell
uvicorn app.main:app --reload --port 8000
```
O directamente:
```powershell
python -m app.main
```

### 3. Documentación interactiva
Una vez corriendo, abre en el navegador:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Pruebas Automatizadas

Se incluyen pruebas con `pytest` que verifican validaciones y flujo completo usando *mocks* (sin depender de credenciales o red externa):

```powershell
pytest -v
```

---

## 📦 Guía de migración al proyecto principal

Cuando estés listo para migrar:
1. **Lógica de negocio:** Copia la carpeta `app/services/` y `app/schemas/`. No dependen de FastAPI directamente, por lo que son portables a cualquier framework o worker (Celery, scripts CLI, etc.).
2. **Endpoints:** Copia `app/api/` y agrégalo a tu router principal con `app.include_router(...)`.
3. **Adaptadores:** Adapta o reutiliza `app/infrastructure/` según el almacenamiento o base de datos de tu proyecto definitivo.
