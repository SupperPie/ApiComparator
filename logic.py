import json
import os
import uuid
import datetime
import requests
import re
from deepdiff import DeepDiff
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Helpers ---

def make_serializable(obj):
    """Recursively convert objects (like sets) to JSON-serializable types (lists)."""
    if isinstance(obj, (set, list, tuple)):
        return [make_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if type(obj).__name__ == 'SetOrdered':
        return list(obj)
    return obj

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

# --- Variable Logic ---

def render_template_string(template_str, context):
    """
    Replace {{variable}} in template_str using values from context dict.
    """
    if not isinstance(template_str, str):
        return template_str
    
    # Simple regex for {{var}}
    pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
    
    def replace_match(match):
        var_name = match.group(1)
        return str(context.get(var_name, match.group(0))) # Default to raw string if missing
    
    return pattern.sub(replace_match, template_str)

def render_template_obj(obj, context):
    """
    Recursively render templates in a dict/list structure.
    """
    if isinstance(obj, str):
        return render_template_string(obj, context)
    elif isinstance(obj, list):
        return [render_template_obj(item, context) for item in obj]
    elif isinstance(obj, dict):
        return {k: render_template_obj(v, context) for k, v in obj.items()}
    return obj

def extract_value_from_response(response_data, extraction_rules):
    """
    Extract values from JSON response based on rules.
    rules: [{"source": "path.to.key", "target_var": "var_name"}]
    Simple dot notation support for now.
    """
    extracted = {}
    if not extraction_rules or not isinstance(extraction_rules, list):
        return extracted
        
    for rule in extraction_rules:
        # Determine format
        # 1. Legacy: {"source": "a", "target_var": "b"}
        if 'source' in rule and 'target_var' in rule:
            items = [(rule['target_var'], rule['source'])]
        else:
            # 2. Key-Value: {"token": "$.result.token"}
            items = list(rule.items())
            
        for target_var, source_path in items:
            # Traverse
            val = response_data
            try:
                parts = source_path.replace("$.", "").split('.')
                for part in parts:
                    if isinstance(val, dict):
                        val = val.get(part)
                    elif isinstance(val, list) and part.isdigit():
                        val = val[int(part)]
                    else:
                        val = None
                        break
                
                if val is not None:
                    extracted[target_var] = val
            except Exception:
                pass # Extraction failed
            
    return extracted

# --- API Interaction ---

def fetch_api_data(env, api_template, runtime_context):
    """
    Execute API call using the Runtime Context for variable substitution.
    """
    # 0. Merge Context: Env Variables + API Runtime Variables
    # Env variables are defined in environment config
    # V2 Update: variables can be a dict OR a list of {key, value, description}
    env_vars_raw = env.get('variables', {})
    if isinstance(env_vars_raw, str):
        try: env_vars_raw = json.loads(env_vars_raw)
        except: env_vars_raw = {}
    
    env_vars = {}
    if isinstance(env_vars_raw, list):
        # Flatten list to dict
        for item in env_vars_raw:
            if isinstance(item, dict) and 'key' in item:
                env_vars[item['key']] = item.get('value', '')
    elif isinstance(env_vars_raw, dict):
        env_vars = env_vars_raw
            
    # Combine: Runtime overrides Env
    full_context = {**env_vars, **(runtime_context or {})}
    
    # 1. Render URL
    try:
        base_url_raw = env.get('base_url', '').rstrip('/') + '/'
        base_url = render_template_string(base_url_raw, full_context)
        
        rel_path_raw = api_template.get('relative_path', '').lstrip('/')
        relative_path = render_template_string(rel_path_raw, full_context)
        
        full_url = urljoin(base_url, relative_path)
    except Exception as e:
        return {"error": f"URL Construction Failed: {e}", "status": "failed"}
    
    # 2. Render Headers
    auth_token = full_context.get('auth_token', '')
    
    # Check if auth_token needs templating itself (unlikely if it comes from env vars directly, but good for robustness)
    auth_token = render_template_string(auth_token, full_context)
    
    env_headers = full_context.get('headers', {})
    if isinstance(env_headers, str):
        try: env_headers = json.loads(env_headers)
        except: env_headers = {}
    
    api_headers = api_template.get('headers', {})
    if isinstance(api_headers, str):
        try: api_headers = json.loads(api_headers)
        except: api_headers = {}
        
    # Render values in headers
    env_headers = render_template_obj(env_headers, full_context)
    api_headers = render_template_obj(api_headers, full_context)

    headers = {
        'Authorization': auth_token.strip() if isinstance(auth_token, str) else auth_token,
        'Content-Type': 'application/json',
        **({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in env_headers.items()} if isinstance(env_headers, dict) else {}),
        **({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in api_headers.items()} if isinstance(api_headers, dict) else {})
    }
    
    # 3. Render Params & Body
    params = api_template.get('params')
    if isinstance(params, str):
        try: params = json.loads(params) if params.strip() else None
        except: params = None
    params = render_template_obj(params, full_context)
            
    json_body = api_template.get('json_body')
    if isinstance(json_body, str):
        try: json_body = json.loads(json_body) if json_body.strip() else None
        except: json_body = None
    if json_body is None: json_body = {}
    json_body = render_template_obj(json_body, full_context)

    # Debug Info
    request_info = {
        "url": full_url,
        "method": api_template['method'],
        "headers": headers,
        "params": params,
        "body": json_body,
        "context_used": full_context
    }
    print(f"DEBUG REQUEST: {json.dumps(request_info, default=str)}")
    
    try:
        response = requests.request(
            method=api_template['method'],
            url=full_url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=10
        )
        # We don't raise for status immediately to allow inspection of 400s etc
        # response.raise_for_status() 
        try:
            result = response.json()
        except:
            result = {"raw_text": response.text}
            
        # Add metadata
        if isinstance(result, dict):
            result["_status_code"] = response.status_code
            result["_debug_request"] = request_info
            
        return result
    except Exception as e:
        return {"error": str(e), "status": "failed", "_debug_request": request_info}

# --- Comparison Logic ---

def execute_comparison_run(selected_api_ids, selected_env_ids, environments, api_templates, progress_callback=None):
    """
    Executes comparison with Chaining support.
    Logic:
    1. Sort APIs by Order.
    2. For each Environment:
       - Run APIs sequentially.
       - Update Context after each API if extraction rules exist.
    """
    selected_envs = [e for e in environments if e['id'] in selected_env_ids]
    
    # Filter and Sort Templates by Order
    selected_api_templates = [t for t in api_templates if t['id'] in selected_api_ids]
    selected_api_templates.sort(key=lambda x: int(x.get('order', 0) or 0))
    
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    api_results = {}
    # Init structure
    for api_tpl in selected_api_templates:
        api_results[api_tpl['id']] = {
            "id": api_tpl['id'],
            "name": api_tpl['name'],
            "relative_path": api_tpl.get('relative_path', ''),
            "order": api_tpl.get('order', 0),
            "data_by_env": {},
            "comparisons": {},
            "overall_status": "Consistent"
        }

    total_steps = len(selected_api_templates) * len(selected_envs)
    step_count = 0
    
    # Helper to run a whole sequence for ONE env
    def run_sequence_for_env(env):
        results = {} # api_id -> data
        runtime_context = {} 
        
        for api_tpl in selected_api_templates:
            # 1. Fetch
            data = fetch_api_data(env, api_tpl, runtime_context)
            results[api_tpl['id']] = data
            
            # 2. Extract Variables
            extract_rules = api_tpl.get('extract')
            if isinstance(extract_rules, str):
                try: extract_rules = json.loads(extract_rules)
                except: extract_rules = []
            
            if extract_rules and isinstance(data, dict):
                 new_vars = extract_value_from_response(data, extract_rules)
                 
                 # 2a. Update Runtime Context (For next API in chain)
                 runtime_context.update(new_vars)
                 
                 # 2b. Persist to Environment (Session State)
                 # New requirement: "Refresh if exists, Create if not"
                 # env['variables'] is a list of dicts: [{"key": "k", "value": "v", ...}]
                 if 'variables' not in env or not isinstance(env['variables'], list):
                     env['variables'] = []
                 
                 for key, value in new_vars.items():
                     str_val = str(value)
                     # Find existing
                     found = False
                     for var_item in env['variables']:
                         if var_item.get('key') == key:
                             var_item['value'] = str_val
                             found = True
                             break
                     if not found:
                         env['variables'].append({
                             "key": key,
                             "value": str_val,
                             "description": "Auto-extracted"
                         })
                 
        return env['id'], results

    # Run Environments in Parallel (Each Env runs its own chain sequentially)
    environment_results = {} # env_id -> {api_id: data}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(run_sequence_for_env, env): env for env in selected_envs}
        
        for future in as_completed(futures):
            env = futures[future]
            try:
                env_id, seq_results = future.result()
                environment_results[env_id] = seq_results
            except Exception as e:
                print(f"Error running sequence for {env['name']}: {e}")
            
            # Rough progress (completed 1 env = N steps)
            step_count += len(selected_api_templates)
            if progress_callback:
                 progress_callback(min(step_count, total_steps), total_steps, f"Processed {env['name']}")

    # Re-structure for Comparison View (Pivot results)
    for env_id, seq_results in environment_results.items():
        env_name = next(e['name'] for e in selected_envs if e['id'] == env_id)
        for api_id, data in seq_results.items():
            api_results[api_id]["data_by_env"][env_id] = {
                "env_name": env_name,
                "data": data
            }

    # Compare (All vs Ref)
    for api_tpl in selected_api_templates:
        api_id = api_tpl['id']
        
        # Check if we have data (might be missing if env run failed)
        if not api_results[api_id]["data_by_env"]:
            api_results[api_id]["overall_status"] = "Error"
            continue

        ref_env = selected_envs[0]
        if ref_env['id'] not in api_results[api_id]["data_by_env"]:
             api_results[api_id]["overall_status"] = "Error"
             continue
             
        ref_entry = api_results[api_id]["data_by_env"][ref_env['id']]
        ref_data = ref_entry['data']
        
        # Clean data keys starting with _ (debug/status)
        clean_ref = {k:v for k,v in ref_data.items() if not k.startswith('_')} if isinstance(ref_data, dict) else ref_data

        diff_options = {
            'ignore_order': api_tpl.get('ignore_order', False),
            'exclude_paths': api_tpl.get('ignore_paths', [])
        }
        for i in range(1, len(selected_envs)):
            target_env = selected_envs[i]
            if target_env['id'] not in api_results[api_id]["data_by_env"]:
                continue
                
            target_entry = api_results[api_id]["data_by_env"][target_env['id']]
            target_data = target_entry['data']
            
            # Clean data keys starting with _ (debug/status)
            clean_target = {k:v for k,v in target_data.items() if not k.startswith('_')} if isinstance(target_data, dict) else target_data
            
            comp_key = f"{ref_env['name']} vs {target_env['name']}"
            
            # Use DeepDiff to check for consistency
            ddiff = DeepDiff(clean_ref, clean_target, **diff_options)
            
            if ddiff:
                # If they are different, check if it's because of an error
                if (isinstance(clean_ref, dict) and "error" in clean_ref) or (isinstance(clean_target, dict) and "error" in clean_target):
                    status = "Error"
                else:
                    status = "Inconsistent"
                diff_output = make_serializable(ddiff.to_dict())
            else:
                # Both are identical (even if they both failed with the same error)
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

# --- OpenAPI Parsing Stub (Kept simple) ---
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
