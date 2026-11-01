# Enterprise Identity Security Lab

Proyecto de aprendizaje orientado a DevSecOps: una API con Python,
FastAPI y pruebas automatizadas.

## Estado actual

- GET /health: comprueba que la aplicación responde.
- GET /resources/{resource_id}: consulta un recurso de ejemplo en memoria.
- Cinco pruebas automatizadas con Pytest.
- Autenticación, Docker y GitHub Actions pendientes.

La API todavía no implementa autenticación ni autorización.

## Requisitos

- Windows con PowerShell
- Python 3.15 (entorno utilizado: 3.15.2)
- Git

## Preparar el entorno

Desde la carpeta del proyecto:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Ejecutar la API localmente

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- API: http://127.0.0.1:8000/health
- Documentación interactiva: http://127.0.0.1:8000/docs
- Detener el servidor: Ctrl + C

## Ejecutar las pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Resultado esperado: cinco pruebas aprobadas.

## Comportamiento esperado

| Petición | Código HTTP |
|---|---|
| GET /health | 200 |
| GET /resources/1 | 200 |
| GET /resources/999 | 404 |
| GET /resources/abc | 422 |
| GET /no-existe | 404 |

Los recursos están definidos en memoria; no hay una base de datos.

## Troubleshooting

- No module named: comprueba que instalaste las dependencias en .venv.
- Error loading ASGI app: ejecuta el servidor desde la carpeta que contiene main.py.
- Puerto 8000 ocupado: detén el servidor anterior o utiliza --port 8001.