# AARKA — Solar Operations, Simplified.
> **Enterprise Rooftop Solar Installation & Lifecycle Management Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-Proprietary-0C2318)](LICENSE)

---

## ☀️ 1. Executive Summary

**AARKA** is a centralized digital operating system engineered specifically for high-velocity rooftop solar installation businesses. Operating companies manage approximately **40 monthly installations, 15 field technicians, high-value serialized inventory, complex roof surveys, quotations, warehouse dispatching, long-term warranties, customer maintenance complaints, and government DISCOM subsidies**.

Before AARKA, solar operations suffered from severe operational fragmentation: customer inquiries were lost in WhatsApp threads, quotations forgot critical balance-of-system hardware, site survey measurements sat in physical paper registers, equipment serial numbers were unreliably tracked, and project profitability was opaque.

AARKA solves these problems through a unified architecture connecting the complete business lifecycle into **25 relational PostgreSQL tables, 90+ REST API endpoints, and 22 responsive enterprise SaaS modules**.

---

## 🔄 2. End-to-End Business Lifecycle

The entire lifecycle is connected through enforced database relationships and transaction boundaries:

```mermaid
flowchart TD
    A["1. Customer Inquiry (Public / WhatsApp / Phone)"] --> B["2. Lead CRM & Qualification"]
    B --> C["3. Technical Site Survey (Roof, Tilt, Shadow-Free Area)"]
    C -->|Rule #1: Must be Approved| D["4. Automated BOM & Quotation (Rule #2 & #3)"]
    D -->|Rule #4: Customer Accept| E["5. Sales Order & Material Reservation"]
    E --> F["6. Milestone Payments & Invoicing (Rule #16)"]
    F --> G["7. Warehouse Picklist & Barcode Serial Allocation (Rule #5)"]
    G -->|Rule #7: 100% Serial Allocation| H["8. Dispatch Gate Pass & Logistics Tracking"]
    H -->|Rule #8 & #9: Delivery Confirmed| I["9. Automatic Warranty Activation"]
    I --> J["10. Field Installation & 9-Point Commissioning (Rule #13)"]
    J -->|Rule #14: Customer Touch E-Signature| K["11. Customer Acceptance & Grid Synchronization"]
    K --> L["12. Government PM Surya Ghar Subsidy DBT Tracking"]
    K --> M["13. After-Sales Maintenance & Warranty Claims (Rule #10, #11, #12)"]
    K --> N["14. Project Financial Ledger & Profitability Analysis (Rule #15)"]
```

### Detailed Lifecycle Stages:
1. **Customer Inquiry**: Captured via Public Portal (`/enquiry`), WhatsApp, phone, or referral. Deduplicated against existing client records.
2. **Lead CRM**: Tracked across pipeline stages (`NEW` $\to$ `CONTACTED` $\to$ `QUALIFIED` $\to$ `SURVEY_SCHEDULED` $\to$ `WON`). Opportunity sizing and follow-up logging.
3. **Technical Site Survey**: Field surveyor records roof area, shadow-free area, azimuth orientation, tilt angle, cable run distance, and DISCOM sanctioned load.
4. **BOM & Quotations**: Automated BOM engine sizes panels ($\lceil \text{kW} \times 1000 / 550 \rceil$), inverters, structures, and cables. Computes 20% mandatory advance. Survey approval strictly enforced before quote finalization.
5. **Sales Orders & Reservations**: Customer quotation acceptance automatically instantiates a `SalesOrder` and reserves BOM equipment in warehouse inventory.
6. **Milestone Payments**: Tracks advance, intermediate delivery, and final commissioning payments with overpayment rejection logic.
7. **Serialized Inventory**: Barcode unit tracking for high-value components (modules, inverters, batteries) preventing duplicate serials.
8. **Warehouse Dispatch**: Strict gate pass verification requiring 100% serial number assignment before warehouse release.
9. **Delivery & Warranty**: Delivery confirmation automatically activates warranties for all serialized units with manufacturer-defined durations.
10. **Field Installation**: Mobile-friendly 9-point checklist completion verified on-site.
11. **Handover & E-Signature**: Customer electronic signature captured on HTML5 canvas before job sign-off.
12. **Government Subsidies**: National portal file tracking, DISCOM net metering inspection scheduling, and DBT disbursement verification.
13. **After-Sales Service**: Automatic warranty coverage check (₹0 for active units, estimates for expired units) and serialized equipment replacement workflow.
14. **Finance & Profitability**: Live calculation of recognized revenue minus BOM costs, technician labor, and recorded expenses.

---

## 🏛 3. System Architecture

AARKA utilizes a decoupled client-server architecture designed for reliability, sub-second responses, and mobile field utility:

```mermaid
graph TB
    subgraph Client["Presentation Tier (React 18 + Vite)"]
        UI["Enterprise SaaS Dashboard (Desktop / Tablet)"]
        MobileUI["Field Mobile Views (Technicians & Surveyors)"]
        PublicForm["Public Inquiry Landing Page (/enquiry)"]
    end

    subgraph API["Application Tier (FastAPI + Python 3.9)"]
        AuthModule["JWT Security & 7-Role RBAC Middleware"]
        RuleEngine["AARKA Business Rule Engine (Rules 1–16)"]
        BOMEngine["Dynamic Solar BOM Calculator"]
        REST["90+ Modular REST Endpoints (23 Routers)"]
    end

    subgraph Data["Persistence Tier (PostgreSQL 16)"]
        DB[("PostgreSQL 16 (25 Relational Tables)")]
        Alembic["Alembic Migration Engine"]
        Storage["Local File Store (backend/uploads/)"]
    end

    Client -->|HTTP / JSON (Vite /api Proxy)| REST
    REST --> AuthModule
    AuthModule --> RuleEngine
    RuleEngine --> BOMEngine
    REST -->|SQLAlchemy 2.0 ORM| DB
    REST --> Storage
```

---

## ⚖️ 4. Business Rules Implementation Matrix (Rules 1–16)

Every business constraint from the SunPower Solutions challenge is implemented with database and API-level enforcement:

| Rule # | Business Constraint | Technical Enforcement Mechanism | Source File |
| :--- | :--- | :--- | :--- |
| **Rule 1** | Quotes cannot be finalized without an approved site survey. | Checks `survey.approval_status == 'APPROVED'`; raises `HTTP 400` if pending or rejected. | `quotations.py` |
| **Rule 2** | Automatically calculate BOM with correct ratios for panels, inverters, structures, cables, and protection. | Dynamic calculation sizing panel count ($\lceil \text{capacity} \times 1000 / 550 \rceil$), matching inverter kW, structure sets, and 30m cable factor. | `bom.py` |
| **Rule 3** | Include 20% advance payment requirement in quotation. | Automatically sets `advance_amount = round(total_amount * 0.20, 2)` and `balance_amount = total_amount - advance_amount`. | `quotations.py` |
| **Rule 4** | Quotation acceptance automatically creates Sales Order and reserves inventory. | Transitions quote to `ACCEPTED`, instantiates `SalesOrder`, creates `order_items`, and increments `reserved_quantity` in `inventory_items`. | `quotations.py` |
| **Rule 5** | Duplicate serial numbers must be rejected. | Unique database index on `serialized_equipment.serial_number` + validation check in API. | `serials.py` |
| **Rule 6** | Inventory cannot be adjusted to negative quantity. | Database check constraint + `inventory.py` check `if new_quantity < 0: raise HTTPException(400)`. | `inventory.py` |
| **Rule 7** | Dispatch requires 100% of serialized items allocated to order. | Matches order BOM requirements against allocated `serialized_equipment`. Rejects gate pass if incomplete. | `dispatches.py` |
| **Rule 8** | Delivery confirmation automatically activates warranties for all serialized units. | `/confirm-delivery` auto-creates records in `warranty_records` with status `ACTIVE`. | `dispatches.py` |
| **Rule 9** | Warranty end dates must match product warranty duration. | Dynamically computes: $\text{Warranty End} = \text{Delivery Date} + \text{product.warranty\_months}$ (300 mos panels, 60 mos inverters). | `dispatches.py` |
| **Rule 10** | Service complaints for active warranties have ₹0 customer charges. | Evaluates complaint date against warranty validity; sets `is_under_warranty=True`, `estimated_cost=0.0`. | `service.py` |
| **Rule 11** | Service complaints for expired warranties generate customer estimate. | When warranty is expired, sets `is_under_warranty=False` and generates repair estimate. | `service.py` |
| **Rule 12** | Component replacement under warranty updates serial number records. | Marks old serial as `RETURNED_DEFECTIVE`, sets new serial as `ALLOCATED_CUSTOMER`, and updates warranty record. | `service.py` |
| **Rule 13** | Installation cannot be completed without 9-point checklist completion. | Verifies all 9 checklist booleans (`panels_mounted`, `voc_isc_verified`, etc.) are `True`. | `installations.py` |
| **Rule 14** | Installation completion requires customer acceptance signature. | Requires customer touch signature token / base64 data URL before completing handover. | `installations.py` |
| **Rule 15** | Project profitability must account for material costs, labor, and overheads. | Computes: $\text{Gross Profit} = \text{Recognized Revenue} - (\text{BOM Cost} + \text{Labor Cost} + \text{Expenses})$. | `finance.py` |
| **Rule 16** | Payments cannot exceed total order value. | Checks `amount + current_paid <= total_amount`, rejecting any overpayment attempts. | `payments.py` |

---

## 🗄 5. Database Schema Architecture (25 Tables)

The database schema is managed via **Alembic** migrations and partitioned into clear domain models:

```
backend/app/models/
├── user.py            -> users, audit_logs
├── customer.py        -> customers
├── survey.py          -> site_surveys, survey_photos, technicians
├── product.py         -> products, solar_packages, bom_templates
├── commercial.py      -> quotations, quotation_items, sales_orders, order_items, payments
├── inventory.py       -> inventory_items, stock_movements, serialized_equipment, warehouse_dispatches
├── installation.py   -> installation_jobs, installation_photos
├── service.py         -> warranty_records, service_tickets
├── finance.py         -> project_expenses, commercial_invoices
└── subsidy.py         -> subsidy_applications
```

---

## 💻 6. Frontend Architecture & Design System

The frontend is built using **React 18** and **Vite** following an enterprise SaaS design philosophy:

- **Branding**: Forest green primary palette (`#0c2318`, `#1b4d36`, `#2e8b60`), warm background tones (`#f9f9f6`), and muted amber accents.
- **Typography**: Clean, professional typography (`Plus Jakarta Sans` for body, `Space Grotesk` for data/numbers).
- **Reusable Components**: `ApplicationLayout`, `Sidebar` (all 22 modules), `Topbar`, `DataTable` (sorting, search, pagination), `StatCard`, `StatusBadge`, `Modal`, and `SignatureCanvas`.
- **Visualization**: Interactive operational charts via **Recharts** (monthly revenue trends, conversion funnel, project status distributions).
- **Mobile Field Utility**: Responsive touch-friendly layout for site surveys and installation checklists.

---

## 👥 7. Role-Based Access Control (7 Roles)

| Role | Demo Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Director / Admin** | `admin@aarka.com` | `admin123` | Full unrestricted access across all 22 modules and executive CSV reports |
| **Sales Representative** | `sales@aarka.com` | `sales123` | Leads CRM, qualification, quotation builder, customer orders |
| **Site Surveyor** | `survey@aarka.com` | `survey123` | Site surveys, mobile roof observations, survey approval submissions |
| **Warehouse Manager** | `warehouse@aarka.com` | `warehouse123` | Inventory balances, barcode scanning, order picklists, dispatch gate passes |
| **Installation Engineer** | `install@aarka.com` | `install123` | Field installations schedule, 9-point checklist execution, customer signature |
| **Service Coordinator** | `service@aarka.com` | `service123` | Maintenance complaints, warranty evaluations, equipment swap workflows |
| **Finance / Accounts** | `finance@aarka.com` | `finance123` | Project profitability, expense logging, tax invoices, subsidy tracking |

*The login page (`/login`) includes **1-click quick-fill buttons** for each role.*

---

## ⚡️ 8. Local Setup & Execution Guide

### Prerequisites
- Python 3.9+
- Node.js 18+ & npm
- PostgreSQL 16 (Local instance or Docker)

### 1. Environment Files
```bash
# Backend environment (backend/.env)
DATABASE_URL=postgresql+psycopg://sivamani_user:Dsm_5885@127.0.0.1:5432/aarka_db
SECRET_KEY=aarka_super_secret_jwt_key_2026_solar_operations_simplified
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend environment (frontend/.env)
VITE_API_URL=http://127.0.0.1:8000
```

### 2. Setup Database & Seed Data
```bash
# Start PostgreSQL (or run via Docker)
docker compose up -d db

# Apply migrations
alembic -c backend/alembic.ini upgrade head

# Seed 7 roles, 15 technicians, 14 products, 16 packages, BOM templates, orders, and warranties
python backend/seed_data.py
```

### 3. Launch Development Servers
```bash
# Terminal 1: Launch FastAPI Backend (Port 8000)
./.venv/bin/python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Launch Vite Frontend (Port 5173)
cd frontend && npm run dev
```

### 4. Active Endpoints
- **AARKA Web App**: `http://localhost:5173/`
- **Public Inquiry Portal**: `http://localhost:5173/enquiry`
- **Swagger API Docs**: `http://127.0.0.1:8000/docs`
- **Detailed API Documentation**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

---

## 🧪 9. Automated Testing & Verification

AARKA includes a full automated test suite verifying all 16 business rules under end-to-end integration conditions:

```bash
PYTHONPATH=backend ./.venv/bin/pytest backend/tests/test_aarka_business_flows.py -v
```

### Test Results:
```
backend/tests/test_aarka_business_flows.py::test_auth_and_profile PASSED             [  9%]
backend/tests/test_aarka_business_flows.py::test_public_enquiry_and_lead_creation PASSED [ 18%]
backend/tests/test_aarka_business_flows.py::test_lead_qualification PASSED          [ 27%]
backend/tests/test_aarka_business_flows.py::test_bom_calculation PASSED             [ 36%]
backend/tests/test_aarka_business_flows.py::test_survey_schedule_and_approval_enforcement PASSED [ 45%]
backend/tests/test_aarka_business_flows.py::test_order_creation_and_payment_validation PASSED [ 54%]
backend/tests/test_aarka_business_flows.py::test_duplicate_serial_prevention PASSED [ 63%]
backend/tests/test_aarka_business_flows.py::test_dispatch_and_automatic_warranty_activation PASSED [ 72%]
backend/tests/test_aarka_business_flows.py::test_service_ticket_and_warranty_coverage_evaluation PASSED [ 81%]
backend/tests/test_aarka_business_flows.py::test_project_profitability_and_finance PASSED [ 90%]
backend/tests/test_aarka_business_flows.py::test_dashboard_summary_metrics PASSED  [100%]

======================= 11 passed in 1.35s ========================
```

---

## 🎯 10. SunPower Solutions Challenge Problem Resolution Matrix

| SunPower Operational Problem | AARKA Engineered Solution |
| :--- | :--- |
| Customer enquiries lost in WhatsApp & calls | Centralized Public Inquiry Portal (`/enquiry`) & Leads CRM (`/leads`) with automated deduplication and follow-up tracking. |
| Quotations prepared manually with forgotten components | Automated BOM Calculation Engine (`/packages`, `/quotations`) computing exact panel counts, inverters, cables, and structure sets. |
| Site survey data stored in paper registers | Digital Site Surveys (`/surveys`) recording shadow-free area, tilt, orientation, and electrical service specs with photo uploads. |
| Serial numbers not reliably tracked | Barcode Serial Registry (`/serials`) with unique constraints and end-to-end lifecycle history. |
| Dispatch operations lack visibility | Strict Gate Pass Workflow (`/dispatch`) enforcing 100% allocation of serialized components before release. |
| Installation photos scattered on phones | Digital Commissioning Checklists (`/installations`) with 9 mandatory technical sign-offs and customer digital signature stored in the database. |
| Warranty dates maintained manually | Automatic Warranty Activation (`/warranties`) upon delivery confirmation with 25-year panel and 5-year inverter durations. |
| Technicians lack centralized assignments | Master Technician Roster (`/technicians`) and Operations Schedule Calendar (`/scheduling`). |
| Customer complaints difficult to trace | Intelligent Service Module (`/service`) with automated warranty coverage evaluation (₹0 for active warranties) and equipment replacement tracking. |
| Project profits & losses unclear | Real-time Project Profitability Ledger (`/finance`) subtracting BOM material costs, technician labor, and recorded expenses from recognized revenue. |
| Subsidy applications difficult to track | PM Surya Ghar National Portal Tracker (`/subsidies`) monitoring applications, DISCOM inspections, and DBT disbursements. |
