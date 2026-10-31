# AARKA API Specification & Architecture Reference
> **Solar Operations, Simplified — Enterprise REST API v2.0**

This document provides a comprehensive technical reference for the AARKA Backend API. All endpoints are built with **FastAPI**, backed by **SQLAlchemy 2.0** and **PostgreSQL 16**, secured with **JWT Bearer Authentication**, and enforce strict solar operational business rules.

---

## 📑 Table of Contents

1. [Authentication & Security](#1-authentication--security)
2. [Public Customer Inquiries](#2-public-customer-inquiries)
3. [Lead Management CRM](#3-lead-management-crm)
4. [Customer Registry](#4-customer-registry)
5. [Site Surveys & Roof Inspection](#5-site-surveys--roof-inspection)
6. [Products & Solar Packages](#6-products--solar-packages)
7. [Bill of Materials (BOM) Calculation Engine](#7-bill-of-materials-bom-calculation-engine)
8. [Quotations & Commercial Proposals](#8-quotations--commercial-proposals)
9. [Sales Orders & Material Reservations](#9-sales-orders--material-reservations)
10. [Payments & Collections](#10-payments--collections)
11. [Inventory & Stock Ledgers](#11-inventory--stock-ledgers)
12. [Serialized Equipment & Barcodes](#12-serialized-equipment--barcodes)
13. [Warehouse Dispatch & Logistics](#13-warehouse-dispatch--logistics)
14. [Technicians & Capacity Roster](#14-technicians--capacity-roster)
15. [Installations & Commissioning](#15-installations--commissioning)
16. [Warranty Registry & Lifecycle](#16-warranty-registry--lifecycle)
17. [After-Sales Service & Equipment Replacement](#17-after-sales-service--equipment-replacement)
18. [Suppliers & Vendors](#18-suppliers--vendors)
19. [Project Finance & Profitability](#19-project-finance--profitability)
20. [Government Subsidies (PM Surya Ghar)](#20-government-subsidies-pm-surya-ghar)
21. [Executive Intelligence & CSV Exports](#21-executive-intelligence--csv-exports)
22. [Dashboard Metrics](#22-dashboard-metrics)

---

## 1. Authentication & Security

All authenticated endpoints require an `Authorization: Bearer <token>` header. Tokens are signed using **HS256** and expire in 24 hours. Passwords are encrypted with direct **bcrypt** hashing.

### `POST /api/auth/login`
Authenticate a staff member and obtain an access token.
- **Auth**: None
- **Request Body**:
  ```json
  {
    "email": "admin@aarka.com",
    "password": "admin123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "name": "Sivamani Dasari",
      "email": "admin@aarka.com",
      "role": "Director / Admin",
      "phone": "+91 98480 12345"
    }
  }
  ```
- **Errors**: `401 Unauthorized` (Invalid credentials), `400 Bad Request` (Account deactivated).

### `GET /api/auth/me`
Retrieve the authenticated user's profile and active permissions.
- **Auth**: Bearer Token
- **Response `200 OK`**: User profile object.

### `GET /api/auth/users`
List all registered staff members.
- **Auth**: Bearer Token
- **Response `200 OK`**: Array of staff user records.

### `POST /api/auth/users`
Register a new employee account.
- **Auth**: Bearer Token (`Director / Admin` only)
- **Request Body**:
  ```json
  {
    "name": "Anand Kumar",
    "email": "anand@aarka.com",
    "password": "Password@123",
    "role": "Sales Representative",
    "phone": "+91 98765 11223"
  }
  ```

---

## 2. Public Customer Inquiries

Public-facing portal for prospective homeowners and commercial customers to submit solar rooftop installation inquiries.

### `POST /api/public/enquiry`
Submits a solar inquiry, checks for existing customers, creates/updates the client profile, generates a new sales lead, and returns the unique lead tracking reference.
- **Auth**: None
- **Request Body**:
  ```json
  {
    "customer_name": "Rajesh Varma",
    "phone": "+91 98481 99221",
    "email": "rajesh.varma@gmail.com",
    "address": "Plot 88, Kavuri Hills, Phase 2",
    "city": "Hyderabad",
    "customer_category": "Residential",
    "preferred_contact_method": "WhatsApp",
    "lead_source": "Website",
    "required_capacity": 3.0,
    "solar_requirement": "On-Grid",
    "monthly_electricity_bill": 3500.0,
    "subsidy_requirement": true,
    "additional_requirements": "Interested in 3kW On-Grid solar rooftop with PM Surya Ghar subsidy."
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "success": true,
    "message": "Thank you! Your solar inquiry has been received...",
    "lead_reference": "LEAD-6362",
    "customer_id": 5,
    "customer_name": "Rajesh Varma",
    "required_capacity_kw": 3.0,
    "solar_requirement": "On-Grid"
  }
  ```

---

## 3. Lead Management CRM

### `GET /api/leads`
Retrieve filtered leads across the sales funnel.
- **Query Params**: `stage` (NEW, CONTACTED, QUALIFIED, SURVEY_SCHEDULED, SURVEY_APPROVED, WON, LOST), `search` (name, phone, lead_reference).
- **Auth**: Bearer Token

### `POST /api/leads`
Create a manual internal sales lead.
- **Auth**: Bearer Token

### `GET /api/leads/{id}`
Retrieve complete lead details with customer profile, survey references, and interaction logs.

### `PUT /api/leads/{id}`
Update lead parameters, assigned sales representative, or opportunity value.

### `POST /api/leads/{id}/qualify`
Moves lead stage from `NEW`/`CONTACTED` to `QUALIFIED` with qualification notes and estimated opportunity value.
- **Request Body**:
  ```json
  {
    "estimated_opportunity_value": 195000.0,
    "notes": "Verified roof ownership and sanctioned load with DISCOM bill."
  }
  ```

---

## 4. Customer Registry

### `GET /api/customers`
Retrieve searchable directory of residential and commercial clients.

### `GET /api/customers/{id}`
Get 360° customer timeline including inquiries, site surveys, quotations, sales orders, installed serial numbers, and service complaint tickets.

### `POST /api/customers`
Manually register a customer profile.

### `PUT /api/customers/{id}`
Update customer contact details, category, or billing address.

---

## 5. Site Surveys & Roof Inspection

Field technical site assessments required before quotations can be generated.

### `GET /api/surveys`
List all site surveys with status filters (`SCHEDULED`, `IN_PROGRESS`, `SUBMITTED`, `APPROVED`, `REJECTED`).

### `POST /api/surveys`
Schedule a site inspection for a qualified lead.
- **Request Body**:
  ```json
  {
    "lead_id": 1,
    "customer_id": 1,
    "technician_id": 3,
    "scheduled_date": "2026-11-05",
    "notes": "Inspect south-facing RCC terrace."
  }
  ```

### `PUT /api/surveys/{id}`
Technician submits technical survey findings:
- Roof Area (sq. ft.)
- Shadow-free Roof Area (sq. ft.)
- Roof Orientation (South, South-West, East)
- Roof Tilt Angle (degrees)
- AC / DC Cable Run Distance (meters)
- Structural Condition (Sound, Moderate, Needs Reinforcement)
- DISCOM Sanctioned Load (kW) & Service Phase (Single / Three Phase)

### `POST /api/surveys/{id}/approve`
**Enforces Rule #1**: Quotations cannot be created without an approved survey. Approves or rejects the survey with documented reasons.
- **Request Body**:
  ```json
  {
    "action": "APPROVE",
    "rejection_reason": null,
    "recommended_capacity_kw": 3.0
  }
  ```

---

## 6. Products & Solar Packages

### `GET /api/products`
Master catalog of Tier-1 solar modules, inverters, mounting structures, and electrical accessories with unit costs, SKUs, and warranty months.

### `POST /api/products`
Create new SKU in master product catalog.

### `GET /api/products/packages`
Standardized turnkey package bundles (e.g. 3kW On-Grid, 5kW On-Grid, 10kW Commercial, 3kW Hybrid Battery).

---

## 7. Bill of Materials (BOM) Calculation Engine

### `GET /api/bom/calculate`
**Enforces Rule #2**: Automatically computes exact component quantities based on system capacity and package type.
- **Query Params**:
  - `package_type`: `"On-Grid System"` | `"Off-Grid System"` | `"Hybrid System"`
  - `capacity_kw`: `3.0`
  - `include_installation`: `true`
- **Calculation Logic**:
  - Panel Count: $\lceil \text{capacity\_kw} \times 1000 / 550 \rceil$ (550W Mono PERC Tier-1 modules)
  - Inverters: Sized to match $\text{capacity\_kw}$
  - Mounting Structures: Sets sized to panel count
  - DC Cables: Calculated based on string distance factor
  - Protection: ACDB/DCDB boxes, SPD Class II surge arrestors, chemical earthing electrodes, lightning arrestor.
- **Response `200 OK`**:
  ```json
  {
    "package_type": "On-Grid System",
    "capacity_kw": 3.0,
    "items": [...],
    "hardware_cost": 154730.0,
    "installation_cost": 13500.0,
    "subtotal": 168230.0,
    "tax_amount": 30281.4,
    "total_amount": 198511.4
  }
  ```

---

## 8. Quotations & Commercial Proposals

### `POST /api/quotations`
**Enforces Rule #1 & Rule #3**:
1. Checks that the referenced `survey_id` has `approval_status == 'APPROVED'`. Rejects with `400 Bad Request` if pending or unapproved.
2. Automatically generates BOM items from the BOM engine.
3. Automatically sets `advance_amount = round(total_amount * 0.20, 2)` (20% mandatory advance).
4. Sets `balance_amount = total_amount - advance_amount`.

### `POST /api/quotations/{id}/send`
Marks quotation as sent to client via email/WhatsApp.

### `POST /api/quotations/{id}/accept`
**Enforces Rule #4**:
Customer acceptance transitions quote to `ACCEPTED`, automatically creates a `SalesOrder`, generates `order_items`, and increments `reserved_quantity` across `inventory_items` in the warehouse.

---

## 9. Sales Orders & Material Reservations

### `GET /api/orders`
List confirmed customer contracts with delivery and installation statuses.

### `GET /api/orders/{id}/picklist`
Generates the warehouse picklist detailing SKUs, reserved quantities, and location bins for assembly.

### `POST /api/orders/{id}/reserve-materials`
Confirms reservation of BOM equipment in warehouse inventory.

---

## 10. Payments & Collections

### `POST /api/payments`
**Enforces Rule #16**: Payments cannot exceed total order value.
- Rejects if `amount + current_paid > total_amount`.
- Records transaction mode (`UPI`, `NEFT`, `CHEQUE`, `CASH`), UTR reference, and generates printable receipt.
- Updates `advance_paid`, `balance_due`, and sales order payment status (`PARTIAL`, `PAID`).

---

## 11. Inventory & Stock Ledgers

### `GET /api/inventory`
Real-time stock ledger across all warehouses: on-hand quantity, reserved quantity, available quantity ($\text{on\_hand} - \text{reserved}$), and low-stock alerts.

### `POST /api/inventory/receive`
Inward stock arrival from Tier-1 suppliers. Updates inventory counts and creates immutable `stock_movements` audit record.

### `POST /api/inventory/adjust`
**Enforces Rule #6**: Prevents negative inventory adjustments (`quantity < 0`).

---

## 12. Serialized Equipment & Barcodes

### `GET /api/serials`
Searchable registry of barcoded equipment (PV panels, inverters, batteries).

### `POST /api/serials`
**Enforces Rule #5**: Rejects duplicate serial numbers. Validates format and checks uniqueness in `serialized_equipment`.

### `POST /api/serials/scan`
Simulates hardware barcode scanning at warehouse inward or dispatch dock.

### `GET /api/serials/history/{serial_number}`
Returns full lifecycle journey of a specific unit (Supplier Inward $\to$ Warehouse Stock $\to$ Order Allocation $\to$ Field Dispatch $\to$ Warranty Activation $\to$ Service Replacement).

---

## 13. Warehouse Dispatch & Logistics

### `POST /api/dispatches`
**Enforces Rule #7**: Dispatch requires 100% of serialized equipment allocated to the sales order.
- Validates that every panel and inverter in the order BOM has a matching serial number assigned.
- Decrements warehouse inventory `quantity` and `reserved_quantity`.
- Generates outbound Gate Pass.

### `POST /api/dispatches/{id}/confirm-delivery`
**Enforces Rule #8 & Rule #9**:
- Marks dispatch as `DELIVERED`.
- Automatically activates warranties in `warranty_records` for all dispatched serial numbers.
- Computes: $\text{Warranty End Date} = \text{Delivery Date} + \text{product.warranty\_months}$ (e.g. 300 months for modules, 60 months for inverters).

---

## 14. Technicians & Capacity Roster

### `GET /api/technicians`
Roster of 15 certified technicians, skill levels (`Lead Electrician`, `Mounting Specialist`, `Survey Engineer`), active job counts, and contact numbers.

### `GET /api/technicians/{id}/schedule`
Retrieves daily schedule of surveys and installations assigned to a specific technician.

---

## 15. Installations & Commissioning

### `POST /api/installations`
Schedules field installation, assigns technician team, and sets milestone date.

### `PUT /api/installations/{id}/checklist`
Updates the mandatory 9-point technical commissioning checklist:
1. `structure_aligned_and_torqued`
2. `panels_mounted_and_clamped`
3. `inverter_installed_and_grounded`
4. `dc_cables_routed_in_conduit`
5. `ac_cables_connected_to_breaker`
6. `earth_resistance_below_5_ohms`
7. `voc_and_isc_verified`
8. `inverter_grid_sync_successful`
9. `generation_verified_on_app`

### `POST /api/installations/{id}/complete`
**Enforces Rule #13 & Rule #14**:
1. Checks that all 9 checklist points are verified `True`.
2. Checks that customer digital signature token/data URL is provided.
3. Transitions job to `COMPLETED` and updates sales order status.

---

## 16. Warranty Registry & Lifecycle

### `GET /api/warranties`
Registry of all active, expiring, and defective warranties.

### `GET /api/warranties/search`
Instant lookup tool by Serial Number, Customer Name, or Phone. Returns active validity status (`COVERED` vs `EXPIRED`), remaining days, and OEM terms.

---

## 17. After-Sales Service & Equipment Replacement

### `POST /api/service/tickets`
**Enforces Rule #10 & Rule #11**:
- Evaluates serial number warranty status as of complaint date.
- If warranty is active: sets `is_under_warranty = True`, estimated customer cost = ₹0.00.
- If warranty is expired: sets `is_under_warranty = False`, generates standard repair estimate.

### `POST /api/service/tickets/{id}/replacement`
**Enforces Rule #12**:
- Marks old serial number as `RETURNED_DEFECTIVE`.
- Assigns new serial number from stock as `ALLOCATED_CUSTOMER`.
- Updates the customer's warranty record to track the new serial number with remaining validity.

### `POST /api/service/tickets/{id}/resolve`
Logs technician labor/parts costs and customer digital acceptance signature.

---

## 18. Suppliers & Vendors

### `GET /api/suppliers`
Directory of Tier-1 OEMs (Panels, Inverters, Structures, Cables) with GSTIN, payment terms (Net-30), and contact details.

### `POST /api/suppliers`
Register new verified equipment vendor.

---

## 19. Project Finance & Profitability

### `GET /api/finance/profitability`
**Enforces Rule #15**:
Computes project-level financial ledger:
$$\text{Gross Profit} = \text{Recognized Revenue} - (\text{BOM Cost} + \text{Labor Cost} + \text{Expenses})$$
$$\text{Margin \%} = \frac{\text{Gross Profit}}{\text{Recognized Revenue}} \times 100$$

### `GET /api/finance/expenses` & `POST /api/finance/expenses`
Track real job expenses (crane rental, transport, permits, extra cabling) tied to sales orders.

### `GET /api/finance/invoices`
Tax invoice ledger with composite solar GST (13.8%).

---

## 20. Government Subsidies (PM Surya Ghar)

### `GET /api/subsidies`
Track subsidy files through official stages:
`DRAFT` $\to$ `SUBMITTED` $\to$ `DOCS_VERIFIED` $\to$ `INSPECTION_SCHEDULED` $\to$ `INSPECTION_PASSED` $\to$ `APPROVED` $\to$ `DISBURSED`.

### `PUT /api/subsidies/{id}/status`
Update DISCOM inspection dates, sanctioned subsidy amounts (e.g. ₹78,000 for 3kW), and Direct Benefit Transfer (DBT) UTR numbers.

---

## 21. Executive Intelligence & CSV Exports

Live database CSV export streaming endpoints:
- `GET /api/reports/export/profitability` (Audit-grade project cost ledger)
- `GET /api/reports/export/inventory` (Stock levels and valuation)
- `GET /api/reports/export/installations` (Field operations and checklists)
- `GET /api/reports/export/warranties` (Active serial numbers registry)
- `GET /api/reports/export/receivables` (Outstanding customer collections)
- `GET /api/reports/director-summary` (Executive KPI totals)

---

## 22. Dashboard Metrics

### `GET /api/dashboard/summary`
Calculates live metrics from PostgreSQL for director dashboard:
- Total Customers, Total Enquiries, Conversion Funnel
- Confirmed Orders, Active Installations, Inventory Valuation
- Revenue vs Expenses, Outstanding Receivables, Low-stock Alerts
- Upcoming Surveys, Today's Field Assignments, Open Defect Tickets
