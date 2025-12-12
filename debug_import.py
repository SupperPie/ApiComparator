import json
import uuid

json_content = """
{
  "openapi": "3.0.1",
  "info": {
    "title": "Ase Client",
    "description": "",
    "version": "1.0.0"
  },
  "tags": [],
  "paths": {
    "/tc/list": {
      "post": {
        "summary": "Web端调用",
        "deprecated": false,
        "description": "获取隐私条款以及Term of use列表",
        "tags": [],
        "parameters": [],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/JSONObject",
                "description": "可包含 channel, programId"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ApiResult",
                  "description": ""
                },
                "example": {
                  "state": "",
                  "msg": "",
                  "errorCode": "",
                  "result": {}
                }
              }
            },
            "headers": {}
          }
        },
        "security": []
      }
    },
    "/faq/list": {
      "post": {
        "summary": "FAQ列表",
        "deprecated": false,
        "description": "",
        "tags": [],
        "parameters": [],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "title": "empty object",
                "properties": {}
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/ApiResult",
                  "description": ""
                },
                "example": {
                  "state": "",
                  "msg": "",
                  "errorCode": "",
                  "result": {}
                }
              }
            },
            "headers": {}
          }
        },
        "security": []
      }
    }
  }
}
"""

def test_parsing():
    imported_data = json.loads(json_content)
    new_apis = []
    
    if isinstance(imported_data, dict) and ('openapi' in imported_data or 'swagger' in imported_data):
        print("Detected OpenAPI/Swagger format. Parsing...")
        for path, methods in imported_data.get('paths', {}).items():
            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                print(f"Found method: {method} for path: {path}")
                
                api_item = {
                    "id": str(uuid.uuid4()),
                    "name": details.get('summary', f"{method.upper()} {path}"),
                    "relative_path": path,
                    "method": method.upper(),
                    "headers": {},
                    "params": {},
                    "json_body": {}
                }
                
                # Extract Parameters (Headers & Query)
                if 'parameters' in details:
                    for param in details['parameters']:
                        if param.get('in') == 'header':
                            val = param.get('example', param.get('default', ''))
                            api_item['headers'][param['name']] = str(val)
                        elif param.get('in') == 'query':
                            val = param.get('example', param.get('default', ''))
                            api_item['params'][param['name']] = str(val)
                
                # Extract Body Example
                try:
                    body_content = details.get('requestBody', {}).get('content', {}).get('application/json', {})
                    if 'example' in body_content:
                        api_item['json_body'] = body_content['example']
                    elif 'examples' in body_content:
                        first_ex = next(iter(body_content['examples'].values()))
                        if isinstance(first_ex, dict) and 'value' in first_ex:
                            api_item['json_body'] = first_ex['value']
                except Exception as e:
                    print(f"Error extracting body: {e}")
                    pass
                    
                new_apis.append(api_item)
    
    print(f"Parsed {len(new_apis)} APIs")
    for api in new_apis:
        print(f"- {api['name']} ({api['method']} {api['relative_path']})")

if __name__ == "__main__":
    test_parsing()
