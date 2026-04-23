# 🔍 Sentinel — Guía de Aprendizaje

> **Objetivo**: Aprender Clean Architecture, Docker, Python, SQL, Terraform y CI/CD construyendo un monitor de disponibilidad con pipeline ETL.
> **Modelo sugerido en Cursor**: `claude-sonnet-4-6`
> **Filosofía**: Entender cada decisión antes de escribir código. No hay apuro.

---

## Stack

| Tecnología | Rol |
|---|---|
| Python 3.12 + FastAPI | API REST y workers |
| PostgreSQL 16 | Base de datos principal |
| Docker + Docker Compose | Entorno de desarrollo local |
| Terraform | IaC sobre AWS Free Tier |
| GitHub Actions | CI/CD |

## AWS Free Tier utilizado

| Servicio | Uso |
|---|---|
| EC2 t2.micro | Servidor de la aplicación |
| RDS db.t3.micro | PostgreSQL managed |
| S3 | Terraform state |
| DynamoDB | Lock del state |
| ECR | Imagen Docker |

---

## ¿Qué construiremos?

Un sistema que:
1. **Monitorea** URLs cada X minutos y registra si están caídas y cuánto tardan en responder
2. **Procesa** esos datos crudos con un pipeline ETL para calcular uptime, percentiles y detectar incidentes
3. **Expone** una API para consultar el historial y estadísticas
4. **Alerta** por email cuando un servicio cae

---

## Estructura del proyecto

```
monitor/
├── src/
│   ├── domain/              # Entidades puras, sin dependencias externas
│   │   ├── entities.py      # URL, Check, Incident
│   │   └── repositories.py  # Interfaces (contratos abstractos)
│   │
│   ├── application/         # Casos de uso / lógica de negocio
│   │   ├── monitor_url.py   # Caso de uso: chequear una URL
│   │   ├── run_etl.py       # Caso de uso: correr el pipeline ETL
│   │   └── get_report.py    # Caso de uso: obtener reporte de una URL
│   │
│   ├── infrastructure/      # Implementaciones concretas
│   │   ├── db/
│   │   │   ├── models.py    # SQLAlchemy models
│   │   │   ├── migrations/  # Alembic migrations
│   │   │   └── repos.py     # Implementaciones de los repositorios
│   │   ├── http_client.py   # Cliente HTTP real
│   │   └── email_sender.py  # Envío de alertas
│   │
│   └── api/                 # Capa de entrega (FastAPI)
│       ├── main.py
│       ├── routers/
│       └── schemas.py       # Pydantic schemas
│
├── workers/
│   ├── checker.py           # Worker que ejecuta los chequeos
│   └── etl.py               # Worker que corre el ETL periódicamente
│
├── terraform/               # Infraestructura como código
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── .github/
│   └── workflows/
│       └── deploy.yml       # Pipeline CI/CD
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

---

## Por qué esta estructura (Clean Architecture)

La regla más importante: **las capas internas no conocen a las externas**.

```
domain → no importa nada del proyecto
application → solo importa domain
infrastructure → implementa los contratos de domain
api → usa application
```

Esto significa que podés cambiar PostgreSQL por MongoDB, o FastAPI por Flask, sin tocar la lógica de negocio. Es la diferencia entre código que dura y código que se vuelve deuda técnica.

**Pregunta para hacerle a Claude en Cursor**: *"¿Por qué en Clean Architecture el dominio no puede importar SQLAlchemy directamente?"*

---

## Modelo de datos

```sql
-- Tabla principal: URLs a monitorear
CREATE TABLE monitored_urls (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    interval_minutes INT NOT NULL DEFAULT 5,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Datos crudos: cada chequeo que hace el worker
CREATE TABLE raw_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id          UUID NOT NULL REFERENCES monitored_urls(id),
    checked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    status_code     INT,
    response_time_ms INT,
    is_up           BOOLEAN NOT NULL,
    error_msg       TEXT
);

-- ETL escribe aquí: agregaciones por hora
CREATE TABLE hourly_stats (
    url_id          UUID NOT NULL REFERENCES monitored_urls(id),
    hour            TIMESTAMPTZ NOT NULL,
    total_checks    INT NOT NULL,
    successful      INT NOT NULL,
    uptime_pct      NUMERIC(5,2) NOT NULL,
    avg_response_ms INT,
    p95_response_ms INT,       -- percentil 95 de latencia
    PRIMARY KEY (url_id, hour)
);

-- ETL detecta y escribe incidentes
CREATE TABLE incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url_id          UUID NOT NULL REFERENCES monitored_urls(id),
    started_at      TIMESTAMPTZ NOT NULL,
    resolved_at     TIMESTAMPTZ,
    duration_min    INT,        -- NULL si aún está caído
    checks_failed   INT NOT NULL DEFAULT 0
);
```

**Conceptos SQL que aprenderás aquí**:
- `TIMESTAMPTZ` vs `TIMESTAMP` (siempre usar con timezone)
- `gen_random_uuid()` vs UUIDs secuenciales
- Índices en `checked_at` y `url_id` para queries de series temporales
- Window functions en el ETL: `LAG()`, `PERCENTILE_CONT()`, `PARTITION BY`

**Pregunta para Cursor**: *"¿Qué es un índice parcial y cuándo conviene usarlo en la tabla raw_checks?"*

---

## Fase 1 — Dominio y estructura base

**Objetivo**: Definir las entidades y contratos sin escribir ninguna implementación concreta aún.

### Tareas

1. Crear el repositorio en GitHub
2. Configurar el entorno virtual de Python
3. Escribir `src/domain/entities.py` con dataclasses puras
4. Escribir `src/domain/repositories.py` con ABCs (clases abstractas)
5. Escribir los primeros tests unitarios del dominio

### Entidades a definir

```python
# Preguntar a Claude: ¿por qué usamos dataclasses y no clases normales aquí?
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class MonitoredURL:
    id: UUID
    url: str
    name: str
    interval_minutes: int
    is_active: bool

@dataclass
class Check:
    id: UUID
    url_id: UUID
    checked_at: datetime
    is_up: bool
    status_code: int | None
    response_time_ms: int | None
    error_msg: str | None
```

### Contratos (repositorios abstractos)

```python
from abc import ABC, abstractmethod

class URLRepository(ABC):
    @abstractmethod
    def get_active_urls(self) -> list[MonitoredURL]: ...

    @abstractmethod
    def save_check(self, check: Check) -> None: ...
```

**Pregunta para Cursor**: *"¿Cuál es la diferencia entre una interfaz en este contexto y herencia tradicional?"*

### Criterio de éxito de esta fase

- Podés correr `pytest` y los tests del dominio pasan
- El directorio `domain/` no tiene ningún `import` de SQLAlchemy, FastAPI, requests, ni nada externo

---

## Fase 2 — Docker Compose y base de datos local

**Objetivo**: Tener el entorno de desarrollo corriendo con un solo comando.

### Tareas

1. Escribir `docker-compose.yml` con los servicios: `app`, `db`, `worker`
2. Escribir el `Dockerfile` para la aplicación
3. Configurar Alembic para migraciones
4. Crear la primera migración con las tablas del modelo de datos

### docker-compose.yml inicial

```yaml
# Preguntar a Claude: ¿qué es un healthcheck y por qué es importante?
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: monitor
      POSTGRES_USER: monitor
      POSTGRES_PASSWORD: monitor
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U monitor"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://monitor:monitor@db:5432/monitor
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

**Conceptos Docker a explorar**:
- `healthcheck` y por qué `depends_on` solo no alcanza
- Diferencia entre `COPY` y `ADD` en el Dockerfile
- Multi-stage builds para reducir el tamaño de la imagen
- `.dockerignore`

**Pregunta para Cursor**: *"¿Por qué es importante que el Dockerfile tenga las dependencias de Python en una capa separada al código fuente?"*

### Criterio de éxito

- `docker compose up` levanta todo sin errores
- Podés conectarte a PostgreSQL desde tu máquina: `psql -h localhost -U monitor monitor`
- Alembic corre `alembic upgrade head` y crea las tablas

---

## Fase 3 — Worker de chequeos e infraestructura

**Objetivo**: Implementar los repositorios concretos y el worker que monitorea URLs.

### Tareas

1. Escribir `src/infrastructure/db/repos.py` implementando los contratos del dominio
2. Escribir `src/infrastructure/http_client.py` para hacer los chequeos HTTP
3. Escribir `workers/checker.py` con APScheduler
4. Escribir el caso de uso `src/application/monitor_url.py`

### Flujo del worker

```
APScheduler cada 5 min
    → get_active_urls() del repositorio
    → para cada URL:
        → HTTP GET con timeout de 10s
        → registrar status_code, tiempo, is_up
        → save_check() al repositorio
        → si is_up == False y anterior era True → crear incidente
```

**Conceptos a explorar**:
- `httpx` vs `requests` (async vs sync)
- Manejo de timeouts y excepciones de red
- APScheduler: `BackgroundScheduler` vs `AsyncIOScheduler`
- Dependency Injection: cómo el caso de uso recibe el repositorio sin conocer la implementación

**Pregunta para Cursor**: *"¿Cómo implementarías el patrón Repository para que el caso de uso pueda testearse con un repositorio en memoria, sin base de datos real?"*

### Test que deberías poder escribir

```python
def test_monitor_url_registra_check_cuando_esta_caida():
    # Arrange
    fake_repo = InMemoryURLRepository()
    fake_http = FakeHTTPClient(returns_error=True)
    use_case = MonitorURL(repo=fake_repo, http=fake_http)
    url = MonitoredURL(id=uuid4(), url="https://example.com", ...)

    # Act
    use_case.execute(url)

    # Assert
    checks = fake_repo.get_checks(url.id)
    assert len(checks) == 1
    assert checks[0].is_up == False
```

### Criterio de éxito

- El worker corre y guarda checks en la base de datos
- Los tests del caso de uso pasan **sin base de datos ni HTTP real**
- `SELECT COUNT(*) FROM raw_checks;` crece cada 5 minutos

---

## Fase 4 — Pipeline ETL

**Objetivo**: Procesar los datos crudos y generar agregaciones útiles.

### ¿Qué hace el ETL?

```
Extract  → Lee raw_checks de las últimas 2 horas que no fueron procesados
Transform → Calcula por (url_id, hora):
             - uptime % = checks exitosos / total checks
             - avg_response_ms
             - p95_response_ms (percentil 95 con window function)
             - detecta si hubo incidente (>3 checks fallidos consecutivos)
Load     → Escribe en hourly_stats e incidents
```

### Query ETL central (lo más importante de aprender)

```sql
-- Preguntar a Claude: ¿qué hace exactamente PERCENTILE_CONT?
-- ¿Y cuándo conviene usar window functions vs GROUP BY?

SELECT
    url_id,
    date_trunc('hour', checked_at) AS hour,
    COUNT(*) AS total_checks,
    COUNT(*) FILTER (WHERE is_up) AS successful,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_up) / COUNT(*),
        2
    ) AS uptime_pct,
    AVG(response_time_ms) FILTER (WHERE is_up) AS avg_response_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (
        ORDER BY response_time_ms
    ) FILTER (WHERE is_up) AS p95_response_ms
FROM raw_checks
WHERE checked_at >= now() - interval '2 hours'
GROUP BY url_id, date_trunc('hour', checked_at);
```

### Detección de incidentes con LAG()

```sql
-- LAG() permite comparar cada fila con la anterior
-- Así detectamos el momento exacto en que algo cayó

SELECT
    url_id,
    checked_at,
    is_up,
    LAG(is_up) OVER (PARTITION BY url_id ORDER BY checked_at) AS prev_is_up
FROM raw_checks
ORDER BY url_id, checked_at;

-- Si is_up = FALSE y prev_is_up = TRUE → inicio de incidente
-- Si is_up = TRUE y prev_is_up = FALSE → fin de incidente
```

**Pregunta para Cursor**: *"¿Cuál es la diferencia entre PERCENTILE_CONT y PERCENTILE_DISC? ¿Cuándo usarías cada una?"*

### Criterio de éxito

- `hourly_stats` se pobla correctamente al correr el ETL
- Los incidentes se detectan automáticamente
- Podés correr el ETL manualmente: `python -m workers.etl`

---

## Fase 5 — API con FastAPI

**Objetivo**: Exponer los datos via REST con Clean Architecture completa.

### Endpoints a implementar

```
GET  /urls                    → listar URLs monitoreadas
POST /urls                    → agregar URL nueva
GET  /urls/{id}/status        → estado actual (up/down, última verificación)
GET  /urls/{id}/stats?days=7  → estadísticas de los últimos N días
GET  /urls/{id}/incidents     → historial de incidentes
```

### Estructura de un router en Clean Architecture

```python
# api/routers/urls.py
# El router solo conoce schemas y casos de uso, nunca repos directamente

from fastapi import APIRouter, Depends
from src.application.get_report import GetReport
from src.api.schemas import URLStatsResponse
from src.api.dependencies import get_report_use_case

router = APIRouter(prefix="/urls")

@router.get("/{url_id}/stats")
def get_stats(
    url_id: UUID,
    days: int = 7,
    use_case: GetReport = Depends(get_report_use_case)
) -> URLStatsResponse:
    result = use_case.execute(url_id, days)
    return URLStatsResponse.from_domain(result)
```

**Conceptos a explorar**:
- Dependency Injection en FastAPI con `Depends()`
- Pydantic v2: validators, `model_validator`, `from_domain()`
- Separación entre schemas de API y entidades de dominio
- Manejo de errores con `HTTPException` y handlers globales

**Pregunta para Cursor**: *"¿Por qué el schema de la API (Pydantic) es una clase distinta a la entidad del dominio? ¿No es duplicar código?"*

### Criterio de éxito

- `GET /urls/{id}/stats` devuelve datos reales de la base de datos
- Los errores devuelven JSON con formato consistente (no el default de FastAPI)
- Hay tests de integración para los endpoints principales

---

## Fase 6 — Terraform en AWS

**Objetivo**: Definir toda la infraestructura como código y poder reproducirla con un comando.

### Recursos a crear

```hcl
# terraform/main.tf

# Backend: guarda el state en S3 con lock en DynamoDB
terraform {
  backend "s3" {
    bucket         = "monitor-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
  }
}

# VPC, subnets, security groups
# EC2 t2.micro para la app
# RDS db.t3.micro PostgreSQL
# ECR para la imagen Docker
```

### Orden de aprendizaje en Terraform

1. **State**: ¿qué es el state y por qué no se commitea al repo?
2. **Plan vs Apply**: siempre revisar el plan antes de aplicar
3. **Variables y outputs**: separar configuración del código
4. **Módulos**: reutilizar bloques de infraestructura
5. **Remote backend**: por qué S3 + DynamoDB para trabajo en equipo

**Pregunta para Cursor**: *"¿Qué pasa si dos personas corren `terraform apply` al mismo tiempo sin el lock de DynamoDB?"*

### Comandos esenciales

```bash
terraform init      # inicializar, descargar providers
terraform plan      # ver qué va a cambiar (nunca saltear esto)
terraform apply     # aplicar cambios
terraform destroy   # destruir toda la infraestructura (cuidado)
terraform output    # ver outputs definidos
```

### Criterio de éxito

- `terraform plan` muestra los recursos a crear sin errores
- `terraform apply` crea la infraestructura en AWS Free Tier
- El state está guardado en S3, no en el repositorio

---

## Fase 7 — CI/CD con GitHub Actions

**Objetivo**: Automatizar tests, build y deploy con cada push a `main`.

### Pipeline completo

```yaml
# .github/workflows/deploy.yml

name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: monitor_test
          POSTGRES_USER: monitor
          POSTGRES_PASSWORD: monitor
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest --cov=src tests/

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Build and push to ECR
        # construir imagen Docker y subirla a ECR

  deploy:
    needs: build-and-push
    steps:
      - name: Deploy to EC2
        # SSH a la instancia y hacer docker pull + restart
```

**Conceptos a explorar**:
- `needs`: dependencias entre jobs
- `if`: condiciones para correr un job
- Secrets en GitHub Actions: nunca hardcodear credenciales
- Service containers: levantar PostgreSQL para los tests de integración
- Environments: separar staging de production

**Pregunta para Cursor**: *"¿Qué es el principio de 'fail fast' en CI/CD y cómo se aplica en este pipeline?"*

### Criterio de éxito

- Un PR que rompe tests no puede hacer merge
- Un push a `main` despliega automáticamente en 5 minutos
- Las credenciales de AWS nunca aparecen en los logs

---

## Preguntas guía para usar con Cursor

Estas preguntas están diseñadas para entender el *por qué* de cada decisión, no solo el *cómo*. Úsalas cuando te quedes trabado o quieras profundizar:

### Clean Architecture
- *"¿Por qué el caso de uso no puede instanciar el repositorio directamente?"*
- *"¿Qué problema resuelve la Dependency Injection en este contexto?"*
- *"Si quisiera cambiar PostgreSQL por SQLite para los tests, ¿qué archivos tendría que tocar?"*

### SQL y ETL
- *"¿Qué es una window function y en qué se diferencia de GROUP BY?"*
- *"¿Por qué es importante usar TIMESTAMPTZ en lugar de TIMESTAMP?"*
- *"¿Cómo indexarías raw_checks para que las queries del ETL sean rápidas?"*
- *"¿Qué es el particionado de tablas y cuándo lo usaría en raw_checks?"*

### Docker
- *"¿Por qué separar la instalación de dependencias del COPY del código fuente en el Dockerfile?"*
- *"¿Qué es una imagen multi-stage y cuándo conviene usarla?"*
- *"¿Por qué los volúmenes de Docker persisten datos entre reinicios del contenedor?"*

### Terraform
- *"¿Qué es el state de Terraform y qué pasa si lo pierdo?"*
- *"¿Cuál es la diferencia entre `terraform plan` y `terraform apply`?"*
- *"¿Por qué se usa DynamoDB para el lock del state y no otro mecanismo?"*

### GitHub Actions
- *"¿Cuál es la diferencia entre un job y un step en GitHub Actions?"*
- *"¿Por qué usamos `needs` entre jobs en lugar de poner todo en un solo job?"*
- *"¿Cómo funciona el secreto de AWS en GitHub Actions sin que aparezca en los logs?"*

---

## Criterios de calidad del proyecto

Antes de considerar cada fase terminada, verificar:

- [ ] Los tests del dominio corren sin base de datos ni red
- [ ] `docker compose up` levanta todo con un comando
- [ ] No hay credenciales hardcodeadas en el código
- [ ] Cada función hace una sola cosa (Single Responsibility)
- [ ] Los errores de red y de base de datos están manejados explícitamente
- [ ] El pipeline de CI falla si los tests fallan

---

## Recursos recomendados

| Tema | Recurso |
|---|---|
| Clean Architecture | *Clean Architecture* — Robert C. Martin (conceptos, no el código) |
| SQL avanzado | Mode Analytics SQL Tutorial (window functions) |
| Terraform | documentación oficial + *Terraform: Up & Running* |
| Docker | Play with Docker (entorno online gratuito) |
| FastAPI | documentación oficial (es excelente) |
| GitHub Actions | GitHub Skills (cursos interactivos gratuitos) |
