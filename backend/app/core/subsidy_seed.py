import json
from datetime import date
from sqlalchemy.orm import Session
from app.models.subsidy import GovernmentScheme, SchemeRule


SPECIAL_CATEGORY_STATES = [
    "Sikkim", "Uttarakhand", "Himachal Pradesh", "Jammu and Kashmir",
    "Ladakh", "Assam", "Arunachal Pradesh", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Tripura", "Andaman and Nicobar Islands", "Lakshadweep"
]

SCHEMES_CATALOGUE = [
    {
        "code": "PM_SURYA_GHAR_RES",
        "name": "PM Surya Ghar: Muft Bijli Yojana (Residential)",
        "authority": "Ministry of New and Renewable Energy (MNRE), Govt. of India",
        "category": "RESIDENTIAL",
        "jurisdiction": "CENTRAL",
        "state": None,
        "description": "National rooftop solar scheme providing Direct Beneficiary Transfer (DBT) central financial assistance to individual residential households. Systems must be grid-connected with two-way DISCOM net-metering.",
        "source_url": "https://pmsuryaghar.gov.in/",
        "notification_reference": "MNRE Notification No. 318/331/2023-GCRT (13 Feb 2024)",
        "effective_from": date(2024, 2, 13),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "RESIDENTIAL",
                "state": "ALL",
                "capacity_min": 1.0,
                "capacity_max": 10.0,
                "rate_per_kw": 30000.0,
                "maximum_assistance": 78000.0,
                "calculation_type": "TIERED_PMSG",
                "rule_version": "2024.1-MNRE",
                "eligibility_configuration": json.dumps({
                    "min_capacity_kw": 1.0,
                    "max_subsidized_capacity_kw": 3.0,
                    "grid_connection_required": True,
                    "almm_compliance_required": True,
                    "prior_claim_disallowed": True,
                    "special_category_rates": {
                        "first_2kw_per_kw": 33000.0,
                        "third_kw": 19800.0,
                        "maximum_assistance": 85800.0
                    },
                    "general_category_rates": {
                        "first_2kw_per_kw": 30000.0,
                        "third_kw": 18000.0,
                        "maximum_assistance": 78000.0
                    }
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "ELECTRICITY_BILL", "name": "Latest Electricity Bill (Last 3 months)", "required": True},
                            {"type": "PROPERTY_TAX_OR_ROOF_CONSENT", "name": "Property Tax Receipt / Roof Ownership Proof", "required": True},
                            {"type": "AADHAAR_CARD", "name": "Aadhaar Card (Electricity Connection Holder)", "required": True}
                        ]
                    },
                    {
                        "stage": "COMMISSIONING_STAGE",
                        "documents": [
                            {"type": "INSTALLATION_PHOTO", "name": "Geo-tagged Plant & Inverter Installation Photos", "required": True},
                            {"type": "NET_METER_REPORT", "name": "DISCOM Net-Meter Installation & Test Report", "required": True},
                            {"type": "COMMISSIONING_CERTIFICATE", "name": "Joint Inspection & Commissioning Certificate (JCC)", "required": True}
                        ]
                    },
                    {
                        "stage": "SUBSIDY_CLAIM_STAGE",
                        "documents": [
                            {"type": "BANK_PASSBOOK_OR_CHEQUE", "name": "Cancelled Cheque / Passbook (Aadhaar-seeded bank account)", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "PM_SURYA_GHAR_GHS",
        "name": "PM Surya Ghar: Group Housing Societies / RWAs",
        "authority": "Ministry of New and Renewable Energy (MNRE), Govt. of India",
        "category": "GHS_RWA",
        "jurisdiction": "CENTRAL",
        "state": None,
        "description": "Central Financial Assistance (CFA) for Resident Welfare Associations (RWAs) and Group Housing Societies (GHS) for common facility solar power installations (including EV charging, common lighting, and water pumping) up to 500 kW.",
        "source_url": "https://pmsuryaghar.gov.in/",
        "notification_reference": "MNRE GHS/RWA Operational Guidelines 2024",
        "effective_from": date(2024, 2, 13),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "GHS_RWA",
                "state": "ALL",
                "capacity_min": 10.0,
                "capacity_max": 500.0,
                "rate_per_kw": 18000.0,
                "maximum_assistance": 9000000.0,  # 500 kW * 18,000 = 90 Lakhs
                "calculation_type": "FLAT_PER_KW",
                "rule_version": "2024.1-GHS-MNRE",
                "eligibility_configuration": json.dumps({
                    "rate_per_kw": 18000.0,
                    "max_capacity_kw": 500.0,
                    "max_per_household_kw": 3.0,
                    "common_meters_only": True
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "RWA_REGISTRATION", "name": "Society / RWA Registration Certificate", "required": True},
                            {"type": "RWA_RESOLUTION", "name": "Managing Committee Resolution for Solar Project", "required": True},
                            {"type": "ELECTRICITY_BILL", "name": "Common Meter Electricity Bill", "required": True}
                        ]
                    },
                    {
                        "stage": "COMMISSIONING_STAGE",
                        "documents": [
                            {"type": "COMMISSIONING_CERTIFICATE", "name": "DISCOM Joint Inspection Certificate", "required": True},
                            {"type": "NET_METER_REPORT", "name": "Bi-directional Net-Meter Test Certificate", "required": True}
                        ]
                    },
                    {
                        "stage": "SUBSIDY_CLAIM_STAGE",
                        "documents": [
                            {"type": "BANK_PASSBOOK_OR_CHEQUE", "name": "RWA Official Society Bank Passbook / Cheque", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "PM_KUSUM_COMP_A",
        "name": "PM-KUSUM: Component A (Decentralized Solar Power Plants)",
        "authority": "Ministry of New and Renewable Energy (MNRE)",
        "category": "AGRICULTURAL",
        "jurisdiction": "CENTRAL",
        "state": None,
        "description": "Setting up 500 kW to 2 MW decentralized grid-connected solar or renewable power plants on barren, fallow, or cultivable farmland by farmers/FPOs within 5 km radius of 33/11 kV sub-stations.",
        "source_url": "https://pmkusum.mnre.gov.in/",
        "notification_reference": "MNRE PM-KUSUM Scheme Guidelines (Comp-A)",
        "effective_from": date(2019, 3, 8),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "AGRICULTURAL",
                "state": "ALL",
                "capacity_min": 500.0,
                "capacity_max": 2000.0,
                "rate_per_kw": 0.0,  # Tariff based PPA
                "maximum_assistance": 0.0,
                "calculation_type": "CUSTOM_GBI",
                "rule_version": "2023.1-KUSUM-A",
                "eligibility_configuration": json.dumps({
                    "substation_proximity_km": 5.0,
                    "grid_injection_level_kv": 11.0,
                    "model": "PPA Tariff Feed-in"
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "FARMER_LAND_RECORD", "name": "Farmland Title / Lease Agreement (Pattadar Passbook)", "required": True},
                            {"type": "AADHAAR_CARD", "name": "Farmer Aadhaar Identity Proof", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "PM_KUSUM_COMP_B",
        "name": "PM-KUSUM: Component B (Standalone Solar Agri Pumps)",
        "authority": "Ministry of New and Renewable Energy (MNRE) & State Nodal Agencies",
        "category": "AGRICULTURAL",
        "jurisdiction": "CENTRAL",
        "state": None,
        "description": "Installation of standalone solar agriculture water pumps up to 7.5 HP in off-grid rural farming areas. Financial structure: 30% Central CFA + 30% State Subsidy + 40% Farmer Contribution.",
        "source_url": "https://pmkusum.mnre.gov.in/",
        "notification_reference": "MNRE PM-KUSUM Comp-B Guidelines",
        "effective_from": date(2019, 3, 8),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "AGRICULTURAL",
                "state": "ALL",
                "capacity_min": 3.0,
                "capacity_max": 7.5,
                "rate_per_kw": 0.0,
                "maximum_assistance": 110000.0,
                "calculation_type": "PERCENTAGE_BENCHMARK",
                "rule_version": "2023.1-KUSUM-B",
                "eligibility_configuration": json.dumps({
                    "central_cfa_percent": 30.0,
                    "state_subsidy_percent": 30.0,
                    "farmer_share_percent": 40.0,
                    "max_pump_hp": 7.5
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "FARMER_LAND_RECORD", "name": "Pattadar Passbook / Land Ownership Record", "required": True},
                            {"type": "BOREWELL_CERTIFICATE", "name": "Groundwater / Borewell Yield Certificate", "required": True},
                            {"type": "AADHAAR_CARD", "name": "Farmer Aadhaar Card", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "STATE_TELANGANA_TSREDCO",
        "name": "Telangana State Solar Regulatory Framework (TSREDCO / TSSPDCL)",
        "authority": "Telangana State Renewable Energy Development Corporation (TSREDCO) / TSERC",
        "category": "RESIDENTIAL",
        "jurisdiction": "STATE",
        "state": "Telangana",
        "description": "State-specific incentive requires confirmation. Telangana DISCOMs (TSSPDCL / TSNPDCL) offer streamlined bi-directional net-metering approvals under TSERC Solar Regulations, but no additional direct state-budget cash subsidy over the central PM Surya Ghar DBT is officially notified.",
        "source_url": "https://tsredco.telangana.gov.in/",
        "notification_reference": "TSERC Rooftop Solar PV Grid Interactive Systems Regulation",
        "effective_from": date(2024, 1, 1),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "REQUIRES_CONFIRMATION",
        "rules": [
            {
                "customer_category": "RESIDENTIAL",
                "state": "Telangana",
                "capacity_min": 1.0,
                "capacity_max": 10.0,
                "rate_per_kw": 0.0,
                "maximum_assistance": 0.0,
                "calculation_type": "FLAT_PER_KW",
                "rule_version": "2024.1-TS",
                "eligibility_configuration": json.dumps({
                    "state_cash_subsidy": 0.0,
                    "note": "State-specific incentive requires confirmation. Only central PM Surya Ghar DBT applies."
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "ELECTRICITY_BILL", "name": "TSSPDCL / TSNPDCL Electricity Bill with USCNO", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "STATE_UP_UPNEDA",
        "name": "Uttar Pradesh State Rooftop Solar Subsidy (UPNEDA)",
        "authority": "Uttar Pradesh New & Renewable Energy Development Agency (UPNEDA)",
        "category": "RESIDENTIAL",
        "jurisdiction": "STATE",
        "state": "Uttar Pradesh",
        "description": "Uttar Pradesh state government provides an additional state top-up subsidy of ₹15,000 per kW up to a maximum cap of ₹30,000 for residential consumers, disbursed over and above the central PM Surya Ghar CFA.",
        "source_url": "https://upneda.org.in/",
        "notification_reference": "UP Solar Energy Policy 2022 / UPNEDA Subsidies Notification 2024",
        "effective_from": date(2024, 2, 1),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "RESIDENTIAL",
                "state": "Uttar Pradesh",
                "capacity_min": 1.0,
                "capacity_max": 10.0,
                "rate_per_kw": 15000.0,
                "maximum_assistance": 30000.0,
                "calculation_type": "FLAT_PER_KW",
                "rule_version": "2024.1-UPNEDA",
                "eligibility_configuration": json.dumps({
                    "state_rate_per_kw": 15000.0,
                    "state_max_cap": 30000.0
                }),
                "document_checklist_configuration": json.dumps([
                    {
                        "stage": "INITIAL_APPLICATION",
                        "documents": [
                            {"type": "ELECTRICITY_BILL", "name": "UPPCL Electricity Bill", "required": True}
                        ]
                    }
                ])
            }
        ]
    },
    {
        "code": "STATE_DELHI_SOLAR",
        "name": "Delhi Solar Policy: Generation Based Incentive (GBI)",
        "authority": "Delhi Electricity Regulatory Commission (DERC) & Energy Dept, GNCTD",
        "category": "RESIDENTIAL",
        "jurisdiction": "STATE",
        "state": "Delhi",
        "description": "Delhi Solar Policy provides Generation-Based Incentive (GBI) credited directly to electricity bills at ₹3.00 per unit (kWh) generated for systems up to 3 kW, and ₹2.00 per unit for 3-10 kW for a period of 5 years.",
        "source_url": "https://delhisolarpolicy.delhi.gov.in/",
        "notification_reference": "Delhi Solar Energy Policy 2024 Gazette Notification",
        "effective_from": date(2024, 3, 1),
        "effective_until": None,
        "last_verified_at": date(2026, 10, 31),
        "verification_status": "OFFICIALLY_VERIFIED",
        "rules": [
            {
                "customer_category": "RESIDENTIAL",
                "state": "Delhi",
                "capacity_min": 1.0,
                "capacity_max": 10.0,
                "rate_per_kw": 0.0,
                "maximum_assistance": 0.0,
                "calculation_type": "CUSTOM_GBI",
                "rule_version": "2024.1-DELHI",
                "eligibility_configuration": json.dumps({
                    "gbi_rate_per_kwh_below_3kw": 3.0,
                    "gbi_rate_per_kwh_above_3kw": 2.0,
                    "duration_years": 5
                }),
                "document_checklist_configuration": json.dumps([])
            }
        ]
    }
]


def seed_government_schemes_and_rules(db: Session):
    """
    Seeds initial official government schemes and rules if not present.
    """
    for s_data in SCHEMES_CATALOGUE:
        existing = db.query(GovernmentScheme).filter(GovernmentScheme.code == s_data["code"]).first()
        if not existing:
            scheme = GovernmentScheme(
                code=s_data["code"],
                name=s_data["name"],
                authority=s_data["authority"],
                category=s_data["category"],
                jurisdiction=s_data["jurisdiction"],
                state=s_data["state"],
                description=s_data["description"],
                source_url=s_data["source_url"],
                notification_reference=s_data["notification_reference"],
                effective_from=s_data["effective_from"],
                effective_until=s_data["effective_until"],
                last_verified_at=s_data["last_verified_at"],
                verification_status=s_data["verification_status"],
                is_active=True
            )
            db.add(scheme)
            db.flush()

            for r_data in s_data.get("rules", []):
                rule = SchemeRule(
                    scheme_id=scheme.id,
                    customer_category=r_data["customer_category"],
                    state=r_data["state"],
                    capacity_min=r_data["capacity_min"],
                    capacity_max=r_data["capacity_max"],
                    rate_per_kw=r_data["rate_per_kw"],
                    maximum_assistance=r_data["maximum_assistance"],
                    calculation_type=r_data["calculation_type"],
                    rule_version=r_data["rule_version"],
                    eligibility_configuration=r_data["eligibility_configuration"],
                    document_checklist_configuration=r_data["document_checklist_configuration"],
                    effective_from=s_data["effective_from"],
                    effective_until=s_data["effective_until"]
                )
                db.add(rule)
            db.commit()
