from unittest.mock import MagicMock, AsyncMock, patch
from starlette.testclient import TestClient

from app.main import app
from app.api.deps import get_automation_service
from app.services.automation_service import AutomationService

client = TestClient(app)


@patch("app.api.v1.endpoints.health.ping_database", new_callable=AsyncMock)
def test_health_endpoint(mock_ping):
    mock_ping.return_value = True
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert data["data"]["database"] == "connected"




def test_cobros_endpoint_invalid_date_format():
    response = client.post("/api/v1/automation/cobros", json={"fecha_inicial": "2026-10-01"})
    assert response.status_code == 422


def test_cobros_endpoint_date_range_inverted():
    response = client.post(
        "/api/v1/automation/cobros",
        json={"fecha_inicial": "15/10/2026", "fecha_final": "01/10/2026"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "no puede ser superior" in data["error"]["message"]


def test_cobros_endpoint_success_mocked():
    # Mocking the client and service
    mock_scrapper = MagicMock()
    mock_scrapper.autenticar.return_value = MagicMock()
    mock_scrapper.descargar_cobros.return_value = "Documentos/RegistroCobros/test.xlsx"
    mock_scrapper.normalizar_archivo.return_value = "Documentos/RegistroCobrosNormalizados/test_norm.xlsx"

    service_mock = AutomationService(scrapper_client=mock_scrapper)

    # Inyección de dependencia mockeada en FastAPI
    app.dependency_overrides[get_automation_service] = lambda: service_mock

    try:
        response = client.post(
            "/api/v1/automation/cobros",
            json={"fecha_inicial": "01/10/2026", "fecha_final": "05/10/2026"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["archivo_original"] == "Documentos/RegistroCobros/test.xlsx"
        assert data["data"]["archivo_normalizado"] == "Documentos/RegistroCobrosNormalizados/test_norm.xlsx"
    finally:
        app.dependency_overrides.clear()


def test_ordenes_endpoint_success_mocked():
    mock_scrapper = MagicMock()
    mock_scrapper.autenticar.return_value = MagicMock()
    mock_scrapper.descargar_ordenes.return_value = "Documentos/Ordenes/Cronograma_Ordenes_test.xlsx"

    service_mock = AutomationService(scrapper_client=mock_scrapper)
    app.dependency_overrides[get_automation_service] = lambda: service_mock

    try:
        response = client.post(
            "/api/v1/automation/ordenes",
            json={"fecha_inicial": "01/10/2026", "fecha_final": "07/10/2026"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["archivo_descargado"] == "Documentos/Ordenes/Cronograma_Ordenes_test.xlsx"
        assert data["data"]["fecha_inicial"] == "01/10/2026"
        assert data["data"]["fecha_final"] == "07/10/2026"
    finally:
        app.dependency_overrides.clear()


def test_ordenes_sincronizar_endpoint_mocked():
    from app.schemas.automation import OrdenesSyncResponseData
    from unittest.mock import AsyncMock

    service_mock = MagicMock()
    service_mock.ejecutar_flujo_completo_ordenes = AsyncMock(
        return_value=OrdenesSyncResponseData(
            archivo_original="Documentos/Ordenes/orig.xlsx",
            archivo_normalizado="Documentos/Ordenes/Normalizados/norm.xlsx",
            fecha_inicial="01/10/2026",
            fecha_final="07/10/2026",
            ordenes_procesadas=136,
            ordenes_sincronizadas=136,
            asignaciones_creadas=136,
            tecnicos_nuevos=0
        )
    )

    app.dependency_overrides[get_automation_service] = lambda: service_mock

    try:
        response = client.post(
            "/api/v1/automation/ordenes/sincronizar",
            json={"fecha_inicial": "01/10/2026", "fecha_final": "07/10/2026"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["ordenes_procesadas"] == 136
        assert data["data"]["asignaciones_creadas"] == 136
    finally:
        app.dependency_overrides.clear()


