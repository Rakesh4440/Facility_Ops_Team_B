# 🏭 FacilityOps AI Platform — Project Documentation & Technical Report

**Project Name:** FacilityOps AI Dashboard  
**Domain:** Industrial Internet of Things (IIoT), Predictive Maintenance & Facility Management  
**Architecture:** Role-Based Access Control (RBAC), Streamlit Multi-Page Web Application  
**Generated PDF Document:** `FacilityOps_Project_Documentation_Final.pdf`

---

## 1. Executive Summary

**FacilityOps AI Platform** is an enterprise-grade predictive maintenance dashboard designed to monitor industrial machine health, predict component failures, automate preventive maintenance scheduling, manage technician work orders, and leverage local Artificial Intelligence (Ollama LLM) for automated diagnostic briefings.

By analyzing sensor streams—including air/process temperatures, rotational speeds, tool torque, and cumulative tool wear—the system empowers facility engineers and maintenance technicians to transition from reactive repairs to data-driven proactive maintenance.

---

## 2. Role-Based Authentication & Access Control (RBAC)

The application implements a secure, unified authentication gateway with cryptographic **SHA-256 password hashing**, user database persistence (`data/users.json`), password recovery, and role-based page protection.

```
                    ┌────────────────────────────────────────┐
                    │      Authentication Portal (app.py)    │
                    │   Admin & Technician Login Gateway     │
                    └───────────────────┬────────────────────┘
                                        │
                    ┌───────────────────┴────────────────────┐
                    │       Role Verification & RBAC         │
                    └─────────┬────────────────────┬─────────┘
                              │                    │
             ┌────────────────┴──────┐      ┌──────┴─────────────────┐
             │ 👑 ADMIN ROLE         │      │ 🔧 TECHNICIAN ROLE     │
             │ (Full Unrestricted)   │      │ (4 Operational Pages)  │
             └────────┬──────────────┘      └──────┬─────────────────┘
                      │                            │
   ├── Home Overview (app.py)                   ├── Home Overview (app.py)
   ├── 1. Maintenance Status Dashboard         ├── 1. Maintenance Status Dashboard
   ├── 2. Exploratory Data Analysis (EDA)       ├── 4. Machine Explorer
   ├── 3. Executive BI Dashboard                ├── 5. Work Orders
   ├── 4. Machine Explorer                      └── 6. Maintenance Schedules
   ├── 5. Work Orders
   ├── 6. Maintenance Schedules
   └── 7. AI Maintenance Recommendations
```

### Access Permission Matrix

| Page File | Page Title | Admin Access | Technician Access |
| :--- | :--- | :---: | :---: |
| `app.py` | Home / Platform Overview | ✅ Granted | ✅ Granted |
| `1_Maintenance_Status_Dashboard.py` | Maintenance Status Dashboard | ✅ Granted | ✅ Granted |
| `2_EDA.py` | Exploratory Data Analysis | ✅ Granted | 🔒 Restricted |
| `3_Dashboard.py` | Executive BI Dashboard | ✅ Granted | 🔒 Restricted |
| `4_Machine_Explorer.py` | Machine Explorer & AI Diagnostics | ✅ Granted | ✅ Granted |
| `5_Work_Orders.py` | Work Order Management | ✅ Granted | ✅ Granted |
| `6_Maintenance_Schedules.py` | Preventive Maintenance Schedules | ✅ Granted | ✅ Granted |
| `7_AI_Maintenance_Recommendations.py` | AI Recommendations Engine | ✅ Granted | 🔒 Restricted |

### Pre-Configured Demo Credentials for Evaluation

- **👑 System Administrator**: Username: `admin` | Password: `admin123`
- **🔧 Lead Technician**: Username: `tech` | Password: `tech123`

---

## 3. Dataset Architecture (AI4I 2020)

The system processes the synthetic **AI4I 2020 Predictive Maintenance Dataset**, containing 10,000 synthetic machine observations representing real-world manufacturing line operations.

### Key Machine Features
1. **UDI & Product ID**: Unique machine identifiers with quality variants (`L` = Low 60%, `M` = Medium 30%, `H` = High 10%).
2. **Air Temperature [K]**: Ambient room operating temperature.
3. **Process Temperature [K]**: Internal machine operating temperature.
4. **Rotational Speed [rpm]**: Spindle rotation rate.
5. **Torque [Nm]**: Mechanical torque exerted on cutting tool.
6. **Tool Wear [min]**: Cumulative operation time of cutting tool.
7. **Failure Modes**:
   - **TWF (Tool Wear Failure)**: Triggered when tool wear reaches 200–240 minutes.
   - **HDF (Heat Dissipation Failure)**: Triggered when temp difference < 8.6 K and speed < 1380 rpm.
   - **PWF (Power Failure)**: Triggered when mechanical power (Torque × Speed) < 3500 W or > 90000 W.
   - **OSF (Overstrain Failure)**: Triggered when strain (Torque × Tool Wear) exceeds product threshold.
   - **RNF (Random Failures)**: 0.1% baseline random hardware failure rate.

---

## 4. Module Breakdown

### 1. Authentication Gateway (`components/auth_ui.py` & `utils/auth.py`)
- Glassmorphic modern dark design with tabbed navigation: **Sign In**, **Create Account (Sign Up)**, and **Forgot Password**.
- 1-Click Fast Demo Login buttons for fast teacher/evaluator testing.
- Session guards automatically halt unauthorized page access attempts with a custom alert UI.

### 2. Maintenance Status Dashboard (`1_Maintenance_Status_Dashboard.py`)
- Live facility view highlighting overdue tasks, 7-day upcoming preventive schedules, open work orders, and historical maintenance activity.

### 3. Exploratory Data Analysis - EDA (`2_EDA.py`) *[Admin Only]*
- Statistical data profiling, missing value matrix, property distributions, and machine failure breakdown graphs.

### 4. Executive BI Dashboard (`3_Dashboard.py`) *[Admin Only]*
- High-level executive charts analyzing operating ranges, thermal dissipation margins, and failure mode clustering.

### 5. Machine Explorer (`4_Machine_Explorer.py`)
- Searchable equipment catalog with real-time parameter gauges, machine inspection logs, automated PDF Work Order generation, and local AI (Ollama) diagnostic summary.

### 6. Work Orders (`5_Work_Orders.py`)
- Maintenance job board tracking jobs across `Open`, `In Progress`, and `Completed` stages with printable PDF export.

### 7. Maintenance Schedules (`6_Maintenance_Schedules.py`)
- Schedule manager for recurring preventive tasks (Daily, Weekly, Monthly, Operating Hours) with step-by-step procedure checklists.

### 8. AI Maintenance Recommendations (`7_AI_Maintenance_Recommendations.py`) *[Admin Only]*
- Intelligent decision-support module that synthesizes machine health signals and active work orders into automated maintenance briefings.

---

## 5. Setup & Launch Instructions

### Prerequisites
- Python 3.10 or higher installed.

### Execution Command
Open a terminal in the project directory (`FacilityOps_AI_Dashboard_FINAL`) and execute:

```bash
streamlit run app.py
```

Upon launching, the app will display the **Authentication Gateway**. Use the **Demo Login** buttons or enter `admin` / `admin123` to test as Administrator, or `tech` / `tech123` to test as Technician.

---

## 6. Generated Documentation Files

1. **PDF Documentation File**: `FacilityOps_Project_Documentation_Final.pdf` (Saved in project root)
2. **Markdown Documentation File**: `PROJECT_DOCUMENTATION.md` (Saved in project root)
