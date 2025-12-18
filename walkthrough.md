# ApiComparator V2.0 Walkthrough

This update introduces Multi-Project support, Environment Variables, and API Chaining.

## 1. Project Management
You will now see a **Project Switcher** at the top of the sidebar.
*   **Default Project**: Your existing data has been migrated here.
*   **Manage Projects**: Click "➕ Manage Projects" to create new workspaces. Each project has its own isolate APIs and Environments.

## 2. Environment Variables
In the **Configuration -> Environments** tab, there is a new column: **Variables (JSON)**.
Define variables like:
```json
{
  "token": "my-secret-token",
  "base_path": "/api/v1"
}
```

## 3. API Chaining & Logic
You can now define dynamic values using `{{variable}}` syntax in:
*   URL (e.g., `{{base_url}}/users`)
*   Headers
*   Params
*   Body

### Execution Order & Extraction
In the **API Templates** editor, you will see two new columns:
1.  **Order**: Define the sequence (1, 2, 3...).
2.  **Extract (JSON)**: Extract data from a response to use in the next API.

**Example Sequence:**

**API #1: Login (Order: 1)**
*   **Extract**: `[{"source": "data.token", "target_var": "auth_token"}]`
*   (This grabs `token` from the response and saves it as `{{auth_token}}`)

**API #2: Get User Profile (Order: 2)**
*   **Headers**: `{"Authorization": "Bearer {{auth_token}}"}`
*   (This uses the token extracted from step 1)

## Deployment
Requires `requirements.txt` update (no new packages, just logic).
Restart the server with `./run.sh`.
