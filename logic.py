import json
import os
import uuid
import datetime
import requests
from deepdiff import DeepDiff
from urllib.parse import urljoin

def make_serializable(obj):
    """Recursively convert objects (like sets) to JSON-serializable types (lists)."""
    if isinstance(obj, (set, list, tuple)):
        return [make_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    # Handle DeepDiff's custom types if any
    if type(obj).__name__ == 'SetOrdered':
        return list(obj)
    return obj

# --- File I/O ---
def load_json_file(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- API Interaction ---
def fetch_api_data(env, api_template, global_auth_token):
    base_url = env['base_url'].rstrip('/') + '/'
    relative_path = api_template['relative_path'].lstrip('/')
    full_url = urljoin(base_url, relative_path)
    
    # Get token from environment config
    auth_token = env.get('auth_token', '')
    
    env_headers = env.get('headers', {})
    if isinstance(env_headers, str):
        try:
            env_headers = json.loads(env_headers)
        except Exception:
            env_headers = {}
            
    # Ensure it is a dict
    if not isinstance(env_headers, dict):
        env_headers = {}

    # Get API specific headers
    api_headers = api_template.get('headers', {})
    if isinstance(api_headers, str):
        try:
            api_headers = json.loads(api_headers)
        except Exception:
            api_headers = {}
    if not isinstance(api_headers, dict):
        api_headers = {}

    headers = {
        'Authorization': auth_token,
        'Content-Type': 'application/json',
        **env_headers,
        **api_headers # API headers override Env headers
    }
    
    # Debug Info
    # Ensure params and json_body are parsed if they are strings
    params = api_template.get('params')
    if isinstance(params, str):
        try:
            params = json.loads(params) if params.strip() else None
        except Exception:
            params = None
            
    json_body = api_template.get('json_body')
    if isinstance(json_body, str):
        try:
            json_body = json.loads(json_body) if json_body.strip() else None
        except Exception:
            # If it's not valid JSON but is a string, maybe it's meant to be raw data? 
            # But we use json=... parameter which expects dict. 
            # Let's assume if it fails parsing, we shouldn't send it as JSON object.
            # But to be safe for this user's case (where they likely have JSON string), we try to parse.
            json_body = None
            
    # Default to empty dict if None, as requested by user
    if json_body is None:
        json_body = {}

    # Update request_info to use the PARSED values
    request_info = {
        "url": full_url,
        "method": api_template['method'],
        "headers": headers,
        "params": params,
        "body": json_body
    }
    print(f"DEBUG REQUEST: {json.dumps(request_info, default=str)}") # Print to console for immediate debugging
    
    try:
        response = requests.request(
            method=api_template['method'],
            url=full_url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict):
            result["_debug_request"] = request_info
        return result
    except Exception as e:
        return {"error": str(e), "status": "failed", "_debug_request": request_info}

# --- Comparison Logic ---
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Comparison Logic ---
def execute_comparison_run(selected_api_ids, selected_env_ids, environments, api_templates, progress_callback=None):
    """
    Executes the comparison logic.
    progress_callback: function(current_step, total_steps, message)
    """
    selected_envs = [e for e in environments if e['id'] in selected_env_ids]
    selected_api_templates = [t for t in api_templates if t['id'] in selected_api_ids]
    
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    api_results = {}
    total_steps = len(selected_api_templates) * len(selected_envs)
    step_count = 0
    
    # Helper for parallel execution
    def fetch_single(env, api_tpl):
        try:
            # fetch_api_data already handles header merging (Auth + Env + API)
            data = fetch_api_data(env, api_tpl, None)
            return env['id'], api_tpl['id'], data, env['name']
        except Exception as e:
            return env['id'], api_tpl['id'], {"error": str(e), "status": "failed"}, env['name']

    # Initialize structure
    for api_tpl in selected_api_templates:
        api_results[api_tpl['id']] = {
            "id": api_tpl['id'],
            "name": api_tpl['name'],
            "data_by_env": {},
            "comparisons": {},
            "overall_status": "Consistent"
        }

    # 1. Fetch Data in Parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for api_tpl in selected_api_templates:
            for env in selected_envs:
                futures.append(executor.submit(fetch_single, env, api_tpl))
        
        for future in as_completed(futures):
            env_id, api_id, data, env_name = future.result()
            api_results[api_id]["data_by_env"][env_id] = {
                "env_name": env_name,
                "data": data
            }
            step_count += 1
            if progress_callback:
                progress_callback(step_count, total_steps, f"Fetched {step_count}/{total_steps} requests")

    # 2. Compare (All vs First)
    for api_tpl in selected_api_templates:
        api_id = api_tpl['id']
        # Ensure we have data for all envs (in case of catastrophic failure, though fetch returns error dict)
        if len(api_results[api_id]["data_by_env"]) < len(selected_envs):
             api_results[api_id]["overall_status"] = "Error"
             continue

        ref_env = selected_envs[0]
        ref_entry = api_results[api_id]["data_by_env"][ref_env['id']]
        ref_data = ref_entry['data']
        
        # Prepare clean data for comparison (remove debug info)
        clean_ref_data = ref_data.copy() if isinstance(ref_data, dict) else ref_data
        if isinstance(clean_ref_data, dict) and "_debug_request" in clean_ref_data:
            del clean_ref_data["_debug_request"]

        diff_options = {
            'ignore_order': api_tpl.get('ignore_order', False),
            'exclude_paths': api_tpl.get('ignore_paths', [])
        }
        
        for i in range(1, len(selected_envs)):
            target_env = selected_envs[i]
            target_entry = api_results[api_id]["data_by_env"][target_env['id']]
            target_data = target_entry['data']
            
            # Prepare clean target data
            clean_target_data = target_data.copy() if isinstance(target_data, dict) else target_data
            if isinstance(clean_target_data, dict) and "_debug_request" in clean_target_data:
                del clean_target_data["_debug_request"]
            
            comp_key = f"{ref_env['name']} vs {target_env['name']}"
            
            if "error" in clean_ref_data or "error" in clean_target_data:
                status = "Error"
                diff_output = "API Request Failed"
            else:
                ddiff = DeepDiff(clean_ref_data, clean_target_data, **diff_options)
                if ddiff:
                    status = "Inconsistent"
                    # Convert DeepDiff object to a serializable dict and handle SetOrdered
                    diff_output = make_serializable(ddiff.to_dict())
                else:
                    status = "Consistent"
                    diff_output = None
            
            api_results[api_id]["comparisons"][comp_key] = {"status": status, "diff": diff_output}
            if status != "Consistent":
                api_results[api_id]["overall_status"] = status

    run_summary = {
        "run_id": run_id,
        "timestamp": run_timestamp,
        "envs": [e['name'] for e in selected_envs],
        "api_count": len(selected_api_templates),
        "consistent_count": sum(1 for r in api_results.values() if r["overall_status"] == "Consistent"),
        "inconsistent_count": sum(1 for r in api_results.values() if r["overall_status"] == "Inconsistent"),
        "error_count": sum(1 for r in api_results.values() if r["overall_status"] == "Error"),
        "api_results": api_results
    }
    
    return run_summary

# --- OpenAPI Parsing ---
def generate_example_from_schema(schema, definitions=None):
    """
    Generates a dummy example from a JSON schema.
    Handles nested objects, arrays, and basic types.
    definitions: dict of global definitions (components/schemas) for $ref resolution.
    """
    if not schema:
        return {}
    
    if definitions is None:
        definitions = {}

    # Handle $ref
    if '$ref' in schema:
        ref_path = schema['$ref']
        # Simple ref resolution (e.g., "#/definitions/User" or "#/components/schemas/User")
        ref_name = ref_path.split('/')[-1]
        if ref_name in definitions:
            return generate_example_from_schema(definitions[ref_name], definitions)
        return {}

    type_ = schema.get('type')
    
    if type_ == 'object':
        properties = schema.get('properties', {})
        example = {}
        for prop_name, prop_schema in properties.items():
            example[prop_name] = generate_example_from_schema(prop_schema, definitions)
        return example
    
    elif type_ == 'array':
        items_schema = schema.get('items', {})
        return [generate_example_from_schema(items_schema, definitions)]
    
    elif type_ == 'string':
        return schema.get('example', "string_value")
    elif type_ == 'integer':
        return schema.get('example', 0)
    elif type_ == 'number':
        return schema.get('example', 0.0)
    elif type_ == 'boolean':
        return schema.get('example', True)
    
    return {}

def parse_openapi_spec(imported_data):
    """
    Parses OpenAPI/Swagger data into a list of API templates.
    """
    new_apis = []
    
    # 1. Identify Definitions/Components for Ref Resolution
    definitions = {}
    if 'definitions' in imported_data:
        definitions = imported_data['definitions']
    elif 'components' in imported_data and 'schemas' in imported_data['components']:
        definitions = imported_data['components']['schemas']

    paths = imported_data.get('paths', {})
    
    for path, path_item in paths.items():
        # Path-level parameters (shared by all methods)
        path_params = path_item.get('parameters', [])
        
        for method, details in path_item.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            api_item = {
                "id": str(uuid.uuid4()),
                "name": details.get('summary', f"{method.upper()} {path}"),
                "relative_path": path,
                "method": method.upper(),
                "headers": {},
                "params": {},
                "json_body": {}
            }
            
            # Merge Parameters
            all_params = path_params + details.get('parameters', [])
            
            for param in all_params:
                # Resolve $ref if present in param? (Less common but possible)
                # For now assume inline
                
                name = param.get('name')
                in_ = param.get('in')
                
                # Value extraction: example -> default -> schema example -> type default
                val = param.get('example', param.get('default', ''))
                if not val and 'schema' in param:
                     val = generate_example_from_schema(param['schema'], definitions)
                     # If it returns a complex object/list, we might need to stringify it for params/headers?
                     # Headers/Query are usually strings.
                     if isinstance(val, (dict, list)):
                         val = json.dumps(val)
                
                if in_ == 'header':
                    api_item['headers'][name] = str(val)
                elif in_ == 'query':
                    api_item['params'][name] = str(val)
            
            # Request Body Extraction
            # 1. OpenAPI 3.x 'requestBody'
            if 'requestBody' in details:
                content = details['requestBody'].get('content', {})
                json_content = content.get('application/json', {})
                
                if 'example' in json_content:
                    api_item['json_body'] = json_content['example']
                elif 'examples' in json_content and json_content['examples']:
                    # Safely get first example
                    first_ex_key = next(iter(json_content['examples']))
                    first_ex = json_content['examples'][first_ex_key]
                    if isinstance(first_ex, dict) and 'value' in first_ex:
                        api_item['json_body'] = first_ex['value']
                elif 'schema' in json_content:
                    # Generate from Schema
                    api_item['json_body'] = generate_example_from_schema(json_content['schema'], definitions)
            
            # 2. Swagger 2.0 'body' parameter
            # Look for a parameter with in: body
            for param in all_params:
                if param.get('in') == 'body':
                    if 'schema' in param:
                        api_item['json_body'] = generate_example_from_schema(param['schema'], definitions)
                    break

            new_apis.append(api_item)
            
    return new_apis

def parse_apifox_project(imported_data):
    """
    Parses Apifox project export (new format) to extract cases.
    Traverses apiCollection -> items -> ... -> api -> cases.
    """
    new_apis = []

    def extract_cases(node):
        # 1. Recursive Traversal for folders
        if 'items' in node and isinstance(node['items'], list):
            for item in node['items']:
                extract_cases(item)
        
        # 2. Extract specific API node
        if 'api' in node:
            api_info = node['api']
            method = api_info.get('method', '').upper()
            path = api_info.get('path', '')
            
            cases = api_info.get('cases', [])
            for case in cases:
                # Basic info
                case_name = case.get('name', f"{method} {path} Case")
                
                # Headers: Convert list of dicts to dict
                headers_list = case.get('parameters', {}).get('header', [])
                headers = {}
                for h in headers_list:
                    if h.get('enable', True) and h.get('name'):
                        headers[h['name']] = h.get('value', '')
                        
                # Params: Combine Query and Path params?
                # Apifox separates them. We mostly put them in 'params' (requests kwargs)
                # But 'params' usually means Query Params. Path params are in URL.
                # If we want to support path param replacement, we might need logic.
                # For now, let's map 'query' to params.
                query_list = case.get('parameters', {}).get('query', [])
                params = {}
                for q in query_list:
                    if q.get('enable', True) and q.get('name'):
                        params[q['name']] = q.get('value', '')
                        
                # Body
                json_body = {}
                req_body = case.get('requestBody', {})
                data_str = req_body.get('data', '')
                if data_str:
                    try:
                        json_body = json.loads(data_str)
                    except:
                        # If not valid JSON, maybe just keep as empty or try to handle?
                        # User wants case content.
                        json_body = {}
                
                api_item = {
                    "id": str(uuid.uuid4()),
                    "name": case_name,
                    "relative_path": path,
                    "method": method,
                    "headers": headers,
                    "params": params,
                    "json_body": json_body
                }
                new_apis.append(api_item)

    # Entry point: apiCollection
    api_collection = imported_data.get('apiCollection', [])
    for module in api_collection:
        extract_cases(module)
        
    return new_apis
