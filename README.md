# DataForge — Your Personal API-Accessible Database

> Define typed schemas, store structured data, and query it via REST API — all through a clean dashboard. No infrastructure setup required.

---

## What is DataForge?

DataForge is a full-stack data management platform that lets you create named, typed schemas and interact with them entirely through a UI or REST API. Think of it as a lightweight personal database — without the overhead of setting up Postgres, managing migrations, or writing backend code.

Unlike Google Sheets, every schema in DataForge is **API-accessible**, **type-enforced**, and **queryable server-side** — making it suitable for automation, programmatic ingestion, and structured data workflows.

---

## Practical Use Cases

- **IoT / Sensor Data** — Devices POST readings directly to a schema endpoint. Typed fields ensure `temperature` is always a float, never a string.
- **Prototype Backend** — Spin up a typed data store in 30 seconds for any frontend or mobile app without provisioning a database.
- **Webhook Sink** — Pipe events from third-party services (Zapier, GitHub, etc.) into a named schema via REST.
- **Structured Form Backend** — Replace Google Forms + Sheets with a schema that enforces types on submission and supports server-side filtering at scale.
- **Personal Data Store** — Track finances, habits, inventory — anything structured — with full CRUD and Excel export.

---

## High-Level Design

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│                                                      │
│  SchemaManagerHome   →   CreateSchemaModal           │
│       (list)              (strict toggle,            │
│                            typed field defs)         │
│                                                      │
│  SchemaDataView      →   FilterBar                   │
│   (ResizableTable)        (typed inputs:             │
│   column resize/reorder    range, bool, date,        │
│                            string-contains)          │
└────────────────────┬────────────────────────────────┘
                     │ REST API (JWT Auth)
                     ▼
┌─────────────────────────────────────────────────────┐
│                  Flask Backend                       │
│                                                      │
│  /schema/create     →  stores strict + field_defs   │
│  /schema/<s>/view   →  build_mongo_filter()         │
│                         returns field_definitions    │
│  /schema/<s>/insert →  coerce_document()            │
│                         validate_document()          │
│  /schema/<s>/upload →  pandas CSV/XLSX parse        │
│                         + strict validation          │
│  /schema/<s>/data/* →  update / delete / download   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                   MongoDB Atlas                      │
│                                                      │
│  Schema_Manager.User_Schema_Info                     │
│    { username, schemas: [                            │
│        { name, filters, strict,                      │
│          field_definitions: [{name, type,            │
│                               filterable}] }         │
│    ]}                                                │
│                                                      │
│  Dynamic collections — one per schema                │
│    {username}_{schema_name}                          │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| Per-schema MongoDB collection | Simple isolation; acceptable at current user scale |
| Strict mode stored at schema-create time | Field definitions are immutable post-creation — no migration complexity |
| `coerce_document` before `validate_document` | Form inputs are always strings; coercion converts `"25"` → `25` before type checking |
| `build_mongo_filter` on backend | Prevents full-collection downloads; all filtering happens server-side via MongoDB operators |
| JWT with `checkLogin` double-check | Token validity + live user existence check on every protected route |

---

## Features

- **Typed Schema Creation** — Define fields with types (`string`, `integer`, `float`, `boolean`, `date`) and mark them as filterable
- **Strict Mode** — Rejects inserts with unknown fields or type mismatches at the API layer
- **Type-Aware Filters** — Range inputs for numbers, date pickers, three-way boolean toggle, string contains
- **Bulk Ingestion** — Upload CSV / XLSX; strict schemas validate every row before any insert
- **Resizable & Reorderable Table** — Drag columns to reorder, drag edges to resize — no library dependency
- **Active Filter Count** — Badge on filter button shows how many filters are currently applied
- **Excel Download** — Export full schema data as `.xlsx`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Bootstrap 5, FontAwesome |
| Backend | Python, Flask, Flask-JWT-Extended |
| Database | MongoDB Atlas (PyMongo) |
| File Handling | Pandas, OpenPyXL |
| Auth | JWT-based with bcrypt password hashing |
| Deployment | Docker, Render |

---

## API Reference

All protected routes require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/signup` | Register with email verification |
| GET | `/schema_manager/schemas/view` | List all schemas |
| POST | `/schema_manager/schema/create` | Create schema (with optional strict + field_definitions) |
| DELETE | `/schema_manager/schema/<s>/delete` | Delete schema and its data |
| POST | `/schema_manager/schema/<s>/view` | Paginated + typed filtered document listing |
| POST | `/schema_manager/schema/<s>/insert` | Insert documents (strict validation applied) |
| PUT | `/schema_manager/schema/<s>/data/update` | Replace document by `_id` |
| DELETE | `/schema_manager/schema/<s>/data/delete/<id>` | Delete document by `_id` |
| POST | `/schema_manager/schema/<s>/data/upload` | Upload CSV/XLSX (strict validation applied row-by-row) |
| GET | `/schema_manager/schema/<s>/data/download` | Download all data as XLSX |

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY=your_secret
export JWT_SECRET_KEY=your_jwt_secret
export USERNAME=mongo_username
export PASSWORD=mongo_password

# Run
python run.py
# Server starts at http://0.0.0.0:5000
```

Frontend UI lives in the [Portfolio-Website repo](https://github.com/jainAashay/Portfolio-Website/tree/master/src/Components/SchemaManager).

---

## Demo

**Live:** https://aashay-jain.netlify.app/dataforge

```
Email:    demo@gmail.com
Password: demo
```

> **Note:** Every account has a strict limit of at most **10 active schemas** at any point in time.
