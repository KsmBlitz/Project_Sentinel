# Project Sentinel

Monitor de disponibilidad de URLs con pipeline ETL, API REST y alertas por email.

## Stack original (Fases 1–7)

| Tecnología | Rol |
|---|---|
| Python 3.12 + FastAPI | API REST y workers |
| PostgreSQL 16 | Base de datos principal |
| Docker + Docker Compose | Entorno de desarrollo local |
| Terraform | IaC sobre AWS Free Tier |
| GitHub Actions | CI/CD |

## Stack actual

| Tecnología | Rol |
|---|---|
| Python 3.12 + FastAPI | API REST y workers |
| Supabase | PostgreSQL managed |
| Railway | Hosting del backend |
| Vue 3 + Vercel | Frontend (dashboard y landing) |
| GitHub Actions | CI (tests automáticos) |

---

## Arquitectura — Clean Architecture

```
domain/          → Entidades puras y contratos abstractos. Sin dependencias externas.
application/     → Casos de uso. Orquesta el dominio.
infrastructure/  → Implementaciones concretas (PostgreSQL, HTTP, email).
api/             → Capa de entrega (FastAPI, routers, schemas).
workers/         → Procesos en background (checker, ETL).
```

Regla central: las capas internas no conocen a las externas.

```
api → application → domain
infrastructure → domain
```

---

## Modelo de datos

```sql
monitored_urls   → URLs a monitorear
raw_checks       → Cada chequeo puntual (datos crudos)
hourly_stats     → Agregaciones por hora calculadas por el ETL
incidents        → Períodos de caída detectados automáticamente
```

---

## Correr localmente

```bash
# Clonar y configurar entorno
git clone https://github.com/KsmBlitz/Project_Sentinel.git
cd Project_Sentinel
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Levantar base de datos y app
docker compose up --build

# Correr migraciones
alembic upgrade head

# Correr tests
pytest tests/ -v
```

---

## Workers

```bash
# Worker de chequeos (cada 5 minutos)
python -m workers.checker

# Worker ETL (cada 1 hora)
python -m workers.etl
```

---

## API — Endpoints principales

```
GET  /health                    → Estado de la aplicación
GET  /urls                      → Listar URLs monitoreadas
POST /urls                      → Agregar URL nueva
GET  /urls/{id}/status          → Estado actual (up/down)
GET  /urls/{id}/stats?days=7    → Estadísticas de los últimos N días
GET  /urls/{id}/incidents       → Historial de incidentes
```

Documentación interactiva disponible en `/docs` cuando la app está corriendo.

---

## Fases del proyecto

### Fase 1 — Dominio y estructura base
Definición de entidades (`MonitoredURL`, `Check`, `HourlyStats`, `Incident`) y contratos abstractos de repositorios. Tests unitarios sin base de datos ni red.

### Fase 2 — Docker Compose y base de datos local
`Dockerfile`, `docker-compose.yml` con healthcheck, configuración de Alembic y primera migración con las 4 tablas del modelo.

### Fase 3 — Worker de chequeos e infraestructura
Implementación de repositorios concretos con SQLAlchemy, cliente HTTP con httpx, caso de uso `MonitorURL` y worker `checker.py` con APScheduler.

### Fase 4 — Pipeline ETL
Caso de uso `RunETL` con SQL avanzado: `date_trunc`, `PERCENTILE_CONT`, `COUNT FILTER`. Detección automática de incidentes con `LAG()`.

### Fase 5 — API con FastAPI
Endpoints REST con schemas Pydantic, inyección de dependencias con `Depends()`, separación entre entidades de dominio y schemas de API.

### Fase 6 — Terraform en AWS
Infraestructura como código: VPC, subnets, security groups, EC2 t2.micro, RDS db.t3.micro, ECR. Remote backend en S3 con lock en DynamoDB.

### Fase 7 — CI/CD con GitHub Actions
Pipeline con tres jobs: tests → build y push a ECR → deploy en EC2 via SSH. Deploy solo en push a `main`.

---

## Lo que aprendiste construyendo esto

- **Clean Architecture**: separación de dominio, aplicación e infraestructura
- **Docker**: imágenes, contenedores, healthchecks, volúmenes, caché de capas
- **Alembic**: migraciones versionadas como el Git de la base de datos
- **SQL avanzado**: window functions, percentiles, `date_trunc`, `GROUP BY`
- **Inyección de dependencias**: contratos vs implementaciones
- **Terraform**: IaC, state remoto, plan vs apply
- **CI/CD**: fail fast, secrets, deploy automatizado
