
import os
import json
import shutil
import uuid
import streamlit as st

DATA_DIR = "data"
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

# Legacy File Paths (for migration)
LEGACY_ENV = "environments.json"
LEGACY_API = "api_templates_UAT.json" # As seen in app.py
LEGACY_HISTORY = "comparison_history.json"

class ProjectManager:
    def __init__(self):
        self._ensure_data_structure()

    def _ensure_data_structure(self):
        """Ensure data directory and projects registry exist. Handle migration."""
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        if not os.path.exists(PROJECTS_FILE):
            # Check for legacy migration
            if os.path.exists(LEGACY_ENV) or os.path.exists(LEGACY_API):
                self._migrate_legacy_data()
            else:
                # Fresh install
                self._create_default_project(fresh=True)

    def _migrate_legacy_data(self):
        """Migrate root JSON files to a Default Project."""
        project_id = str(uuid.uuid4())
        project_name = "Default Project"
        
        # 1. Register Project
        projects = [{
            "id": project_id,
            "name": project_name,
            "created_at": str(uuid.uuid1())
        }]
        
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
            
        # 2. Create Project Folder
        project_dir = os.path.join(DATA_DIR, project_id)
        os.makedirs(project_dir)
        
        # 3. Move Files
        # We rename them to standard names: environments.json, apis.json, history.json
        if os.path.exists(LEGACY_ENV):
            shutil.move(LEGACY_ENV, os.path.join(project_dir, "environments.json"))
        else:
            self._write_empty_json(os.path.join(project_dir, "environments.json"))
            
        if os.path.exists(LEGACY_API):
            shutil.move(LEGACY_API, os.path.join(project_dir, "apis.json"))
        else:
            self._write_empty_json(os.path.join(project_dir, "apis.json"))

        if os.path.exists(LEGACY_HISTORY):
            shutil.move(LEGACY_HISTORY, os.path.join(project_dir, "history.json"))
        else:
            self._write_empty_json(os.path.join(project_dir, "history.json"))
            
        print(f"Migrated legacy data to project: {project_id}")

    def _create_default_project(self, fresh=False):
        """Create a fresh default project."""
        project_id = str(uuid.uuid4())
        projects = [{
            "id": project_id,
            "name": "My First Project",
            "created_at": str(uuid.uuid1())
        }]
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
            
        project_dir = os.path.join(DATA_DIR, project_id)
        os.makedirs(project_dir)
        self._init_project_files(project_dir)

    def _init_project_files(self, project_dir):
        self._write_empty_json(os.path.join(project_dir, "environments.json"))
        self._write_empty_json(os.path.join(project_dir, "apis.json"))
        self._write_empty_json(os.path.join(project_dir, "history.json"))

    def _write_empty_json(self, path):
        with open(path, 'w') as f:
            json.dump([], f)

    def list_projects(self):
        """Return list of projects."""
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r') as f:
                return json.load(f)
        return []

    def create_project(self, name):
        """Create a new project."""
        projects = self.list_projects()
        new_id = str(uuid.uuid4())
        projects.append({
            "id": new_id,
            "name": name,
            "created_at": str(uuid.uuid1())
        })
        
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
            
        project_dir = os.path.join(DATA_DIR, new_id)
        os.makedirs(project_dir)
        self._init_project_files(project_dir)
        return new_id
    
    def delete_project(self, project_id):
        """Delete a project and its files."""
        # Remove from registry
        projects = self.list_projects()
        projects = [p for p in projects if p['id'] != project_id]
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)
            
        # Remove directory
        project_dir = os.path.join(DATA_DIR, project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            
    # Rename Project
    def rename_project(self, project_id, new_name):
        projects = self.list_projects()
        for p in projects:
            if p['id'] == project_id:
                p['name'] = new_name
                break
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(projects, f, indent=2)

    def get_project_paths(self, project_id):
        """Get file paths for a specific project."""
        project_dir = os.path.join(DATA_DIR, project_id)
        return {
            "env_file": os.path.join(project_dir, "environments.json"),
            "api_file": os.path.join(project_dir, "apis.json"),
            "history_file": os.path.join(project_dir, "history.json")
        }
