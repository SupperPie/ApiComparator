
import streamlit as st
import json
from logic import fetch_api_data

# Mock Environment and Template
env = {
    "id": "env1",
    "name": "Test Env",
    "variables": [
        {"key": "auth_token", "value": "Bearer migrated_token"},
        {"key": "headers", "value": "{\"X-Test\": \"true\"}"},
        {"key": "base_url", "value": "https://httpbin.org"}
    ],
    # Old fields cleared
    "auth_token": "",
    "headers": {}
}

api_template = {
    "id": "api1",
    "name": "Test API",
    "relative_path": "/get", # httpbin endpoint
    "method": "GET",
    "headers": {},
    "params": {},
    "json_body": {}
}

print("Running manual verification for Auth/Header variable logic...")

# Mock Context
context = {}

# Run Fetch
result = fetch_api_data(env, api_template, context)

if "_debug_request" in result:
    req = result["_debug_request"]
    headers = req.get("headers", {})
    
    print("\n[DEBUG HEADERS]:", json.dumps(headers, indent=2))
    
    # Check Auth
    if headers.get("Authorization") == "Bearer migrated_token":
        print("✅ Auth Token correctly fetched from variables.")
    else:
        print(f"❌ Auth Token mismatch. Got: {headers.get('Authorization')}")
        
    # Check Extra Header
    if headers.get("X-Test") == "true":
        print("✅ Custom Header correctly fetched from variables.")
    else:
        print(f"❌ Custom Header mismatch. Got: {headers.get('X-Test')}")
else:
    print("❌ API Call failed or no debug info returned.")
    print(result)

