# AARKA — Solar Operations, Simplified.
> **Unified Digital Operating Platform for Rooftop Solar Installation Companies**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-Proprietary-0C2318)](LICENSE)

---

## ☀️ Overview

**AARKA** is an enterprise-grade Solar Installation Management System designed to eliminate the operational chaos faced by rooftop solar engineering and installation companies managing ~40 installations monthly, 15 field technicians, residential/commercial projects, on-grid/off-grid systems, roof surveys, warehouse dispatch, long-term warranties, customer complaints, and DISCOM PM Surya Ghar subsidies.

AARKA connects the entire rooftop solar installation lifecycle across 25 relational tables and 90+ REST API endpoints:

```
CUSTOMER INQUIRY → LEAD CRM → SITE SURVEY → BOM & QUOTATION → SALES ORDER → PAYMENT 
  → INVENTORY RESERVATION → SERIAL NUMBER ALLOCATION → WAREHOUSE DISPATCH 
  → FIELD INSTALLATION → 9-POINT CHECKLIST & SIGNATURE → COMMISSIONING & WARRANTY 
  → AFTER-SALES SERVICE & EQUIPMENT SWAP → FINANCE & DIRECTOR INTELLIGENCE
```

---

## 🌟 Key Features & Business Workflows

- **Public Homeowner Inquiry Portal (`/enquiry`)**: Direct lead capture with solar bill analysis, capacity estimation, and PM Surya Ghar subsidy pre-check.
- **Director Executive Dashboard (`/dashboard`)**: Live revenue tracking, project funnel conversion, technician labor costs, gross profit margin %, and Recharts trends calculated directly from PostgreSQL.
- **Site Survey Operations (`/surveys`)**: Shadow-free area calculation, roof tilt, orientation, cable run distance, DISCOM service specs, and approval enforcement.
- **Automated BOM Engine (`/packages`, `/quotations`)**: Automatic component ratios for solar panels ($\lceil \text{capacity} \times 1000 / 550 \rceil$), inverters, structures, cables, and earthing devices.
- **Quotation & Commercials (`/quotations`, `/orders`)**: Survey-locked quote finalization, automatic 20% advance calculation, quotation acceptance triggering automatic sales order and inventory reservation.
- **Serial Number Traceability (`/serials`)**: Unique barcoded equipment tracking (Tier-1 modules, hybrid inverters, batteries) with complete lifecycle audit history.
- **Strict Dispatch Workflows (`/dispatch`)**: Gate pass generation enforcing 100% serial allocation before truck loading.
- **Delivery Confirmation & Automatic Warranty Activation (`/dispatch`, `/warranties`)**: Automatic calculation of 25-year module warranties and 5-year inverter warranties upon delivery confirmation.
- **Field Installation Operations (`/installations`, `/scheduling`)**: Technician dispatch, master field calendar, mandatory 9-point technical commissioning checklist, and HTML5 electronic touch signature canvas for customer handover.
- **Service & Equipment Replacement (`/service`)**: Automated warranty coverage evaluation (₹0 for in-warranty items, cost estimates for expired items) and equipment replacement workflow (Rule #12).
- **Government Subsidies (`/subsidies`)**: PM Surya Ghar Muft Bijli Yojana national portal integration tracking, DISCOM inspections, and DBT subsidy disbursements.
- **Finance & Profitability Ledger (`/finance`)**: Real-time project gross margin calculations ($\text{Recognized Revenue} - \text{BOM Cost} - \text{Labor} - \text{Expenses}$), expense posting, and tax invoices.
- **Executive CSV Data Exports (`/reports`)**: 1-click audit-grade CSV data downloads for profitability, warehouse stock, field installations, warranty registry, and accounts receivable.

---

## 🛠 Tech Stack

- **Backend**: Python 3.9+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PostgreSQL 16, PyJWT, bcrypt.
- **Frontend**: React 18, Vite, React Router v6, Axios, Lucide React, Recharts, HTML5 Canvas.
- **Database**: PostgreSQL 16 with 25 relational tables and strict integrity constraints.

---

## 🚀 Quick Start Guide

### 1. Clone Repository & Setup Environment
```bash
git clone https://github.com/sivamani-repo/aarka.git
cd aarka

# Configure Backend
cp backend/.env.example backend/.env
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Configure Frontend
cp frontend/.env.example frontend/.env
cd frontend && npm install && cd ..
```

### 2. Database Migration & Seeding
```bash
# Start PostgreSQL via Docker Compose
docker compose up -d db

# Run Alembic Migrations & Seed Sample Projects
alembic -c backend/alembic.ini upgrade head
python backend/seed_data.py
```

### 3. Run Development Servers
```bash
# Terminal 1: Start Backend API (Port 8000)
./.venv/bin/python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Start Frontend UI (Port 5173)
cd frontend && npm run dev
```

---

## 🔐 Demo Accounts & RBAC Roles

The login page (`http://localhost:5173/login`) provides **1-click quick-fill buttons** for each role:

| Role | Email | Password | Primary Workflow |
| :--- | :--- | :--- | :--- |
| **Director / Admin** | `admin@aarka.com` | `admin123` | Executive oversight, financial ledger, team administration, CSV exports |
| **Sales Representative** | `sales@aarka.com` | `sales123` | Leads CRM, qualification, quotation generation, payment receipts |
| **Site Surveyor** | `survey@aarka.com` | `survey123` | Assigned site surveys, roof dimensions, photo uploads |
| **Warehouse Manager** | `warehouse@aarka.com` | `warehouse123` | Inventory ledger, serial barcode scanning, picklists, dispatch gate passes |
| **Installation Engineer** | `install@aarka.com` | `install123` | Field installations, 9-point commissioning checklist, customer e-signature |
| **Service Coordinator** | `service@aarka.com` | `service123` | Defect complaints, automated warranty evaluation, equipment replacement |
| **Finance / Accounts** | `finance@aarka.com` | `finance123` | Project profitability, expense ledger, tax invoices, subsidy DBT |

---

## 🧪 Automated Testing

Execute the comprehensive automated test suite verifying all 16 business rules:

```bash
PYTHONPATH=backend ./.venv/bin/pytest backend/tests/test_aarka_business_flows.py -v
```

---

## 🏢 Business Rules (Rules 1–16)

1. **Rule 1**: Quotations cannot be finalized without an approved site survey.
2. **Rule 2**: Automatically calculate BOM with correct ratios for panels, inverters, cables, structures, and earthing.
3. **Rule 3**: Include mandatory 20% advance payment requirement in quotation.
4. **Rule 4**: Quotation acceptance automatically creates Sales Order and reserves inventory.
5. **Rule 5**: Duplicate serial numbers are strictly rejected at the database level.
6. **Rule 6**: Inventory balances cannot be adjusted to negative values.
7. **Rule 7**: Warehouse dispatch requires 100% of serialized equipment allocated to the order.
8. **Rule 8**: Delivery confirmation automatically activates warranties for all serialized units.
9. **Rule 9**: Warranty expiration dates dynamically match product warranty durations.
10. **Rule 10**: Service complaints for active warranties have ₹0 customer charges.
11. **Rule 11**: Service complaints for expired warranties generate formal customer cost estimates.
12. **Rule 12**: Defective component replacements update serial number status to `RETURNED_DEFECTIVE` and assign new serial to customer warranty.
13. **Rule 13**: Installation completion requires 100% completion of the 9-point technical checklist.
14. **Rule 14**: Installation handover requires customer digital touch signature.
15. **Rule 15**: Project profitability calculates: $\text{Recognized Revenue} - (\text{BOM Cost} + \text{Labor Cost} + \text{Expenses})$.
16. **Rule 16**: Milestone customer payments cannot exceed total sales order value.
