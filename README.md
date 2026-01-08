# ⚡ API Comparator Pro

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.1.0-orange.svg)]()

**API Comparator Pro** is a high-performance, developer-friendly tool designed to validate API consistency across different environments (e.g., QA vs. UAT). It goes beyond simple diffing by supporting **Multi-Project Management**, **Dynamic Variable Chaining**, and **Deep JSON Analysis**.

---

## 🚀 Key Features

### 📂 Project-Centric Workflow
*   **Isolated Environments**: Manage multiple independent projects with their own set of APIs and environments.
*   **Easy Management**: Create, rename, and delete projects directly from the UI.

### ⚙️ Powerful Configuration
*   **Smart Import**: One-click import from **OpenAPI/Swagger** (JSON) or **Apifox** project exports.
*   **Environment Variables**: Define shared variables (auth tokens, base URLs) using a robust template system `{{variable_name}}`.
*   **Bulk Selection**: Manage large API collections easily with "Toggle All" and batch deletion.
*   **Auto-Save**: Seamless configuration experience where changes are persisted immediately on focus loss or Enter.

### 🔗 Variable Chaining & Extraction
*   **Dynamic Sequences**: Execute APIs in a specific order to satisfy dependencies.
*   **Post-Action Extraction**: Extract values (like `token` or `id`) from one API response and automatically inject them into subsequent requests in the chain.
*   **Context Awareness**: Transparently view which variables were utilized in each request for easier debugging.

### 📊 Professional Dashboard
*   **Metrics at a Glance**: Track total runs and pass/fail rates.
*   **Execution History**: Detailed logs of every comparison run with persistent user comments.
*   **Smart Rerun**: One-button re-execution of historical comparisons with identical configurations.
*   **Deep Diffing**: Visualize inconsistencies using granular difference reports, with options to ignore field order or specific paths.

### 🛠️ Developer Tools
*   **Playground**: A dedicated debugger to test individual APIs and verify variable substitution before running full comparisons.
*   **Export Reports**: Generate and download professional comparison reports in PDF or Word format.

---

## 🛠️ Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/SupperPie/ApiComparator.git
    cd ApiComparator
    ```

2.  **Environment Setup**:
    It is recommended to use a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    ```bash
    ./run.sh
    ```
    The app will be available at `http://localhost:8501`.

---

## 📖 Usage Guide

1.  **Create a Project**: Open the "Manage Projects" modal from the sidebar to initialize your first project.
2.  **Configure Environments**: In the **Configuration** tab, add your target environments (e.g., QA and UAT) and their base URLs.
3.  **Setup APIs**: Import or manually add API templates. Define the `Order` if you need to chain requests.
4.  **Variable Extraction**: In the "Post Action" column of an API, define rules (e.g., `[{"token": "$.result.data.token"}]`) to pass data forward.
5.  **Run Comparison**: Go to the **Comparator** tab, select your environments and APIs, and hit "Speed Run Comparison".
6.  **Analyze Results**: Review the results in the **Dashboard** or export a report for your team.

---

## 🏗️ Tech Stack

*   **Frontend**: Streamlit (Python-based Web Framework)
*   **Backend Logic**: Python 3.9+
*   **Diff Engine**: DeepDiff
*   **PDF/Word Export**: ReportLab / python-docx
*   **Request Handling**: Requests (with ThreadPoolExecutor for parallel environment execution)

---

## 📄 License & Credits

Developed with ❤️ by the API Compatibility Team. 
Version 2.1.0 - Focused on Stability, Scale, and User Experience.
