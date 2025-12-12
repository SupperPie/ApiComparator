
import json
import uuid

# Provided JSON Data
json_data = """
{
  "apifoxProject": "1.0.0",
  "$schema": {
    "app": "apifox",
    "type": "project",
    "version": "1.2.0"
  },
  "info": {
    "name": "Ase Client",
    "description": "",
    "mockRule": {
      "rules": [],
      "enableSystemRule": true
    }
  },
  "apiCollection": [
    {
      "name": "Root",
      "id": 348661,
      "auth": {},
      "securityScheme": {},
      "parentId": 0,
      "serverId": "",
      "description": "",
      "identityPattern": {
        "httpApi": {
          "type": "methodAndPath",
          "bodyType": "",
          "fields": []
        }
      },
      "shareSettings": {},
      "visibility": "SHARED",
      "moduleId": 300479,
      "preProcessors": [
        {
          "id": "inheritProcessors",
          "type": "inheritProcessors",
          "data": {}
        }
      ],
      "postProcessors": [
        {
          "id": "inheritProcessors",
          "type": "inheritProcessors",
          "data": {}
        }
      ],
      "inheritPostProcessors": {},
      "inheritPreProcessors": {},
      "items": [
        {
          "name": "【FAQ/T&C】",
          "id": 348908,
          "auth": {},
          "securityScheme": {},
          "parentId": 0,
          "serverId": "",
          "description": "",
          "identityPattern": {
            "httpApi": {
              "type": "inherit",
              "bodyType": "",
              "fields": []
            }
          },
          "shareSettings": {},
          "visibility": "INHERITED",
          "moduleId": 300479,
          "preProcessors": [
            {
              "id": "inheritProcessors",
              "type": "inheritProcessors",
              "data": {}
            }
          ],
          "postProcessors": [
            {
              "id": "inheritProcessors",
              "type": "inheritProcessors",
              "data": {}
            }
          ],
          "inheritPostProcessors": {},
          "inheritPreProcessors": {},
          "items": [
            {
              "name": "Web端调用 T&C List",
              "api": {
                "id": "3473862",
                "method": "post",
                "path": "/tc/list",
                "parameters": {
                  "path": [],
                  "query": [],
                  "cookie": [],
                  "header": []
                },
                "auth": {},
                "securityScheme": {},
                "commonParameters": {},
                "responses": [
                  {
                    "id": "42403",
                    "code": 200,
                    "name": "Success",
                    "headers": [],
                    "jsonSchema": {
                      "$ref": "#/definitions/349612",
                      "description": ""
                    },
                    "description": "",
                    "contentType": "json",
                    "mediaType": "",
                    "oasExtensions": ""
                  }
                ],
                "responseExamples": [
                  {
                    "name": "成功示例",
                    "data": "{\\n  \\"state\\": \\"\\",\\n  \\"msg\\": \\"\\",\\n  \\"errorCode\\": \\"\\",\\n  \\"result\\": {}\\n}",
                    "responseId": 42403,
                    "ordering": 1,
                    "description": "",
                    "oasKey": "",
                    "oasExtensions": ""
                  }
                ],
                "requestBody": {
                  "type": "application/json",
                  "parameters": [],
                  "jsonSchema": {
                    "$ref": "#/definitions/393748",
                    "description": "可包含 channel, programId"
                  },
                  "oasExtensions": ""
                },
                "description": "获取隐私条款以及Term of use列表",
                "tags": [],
                "status": "released",
                "serverId": "",
                "operationId": "",
                "sourceUrl": "",
                "ordering": 0,
                "cases": [
                  {
                    "id": 3476145,
                    "type": "http",
                    "path": null,
                    "name": "T&C barclays",
                    "responseId": 42403,
                    "parameters": {
                      "query": [],
                      "path": [],
                      "cookie": [],
                      "header": [
                        {
                          "id": "go8d4aPpL8",
                          "relatedName": "channel",
                          "name": "channel",
                          "value": "ASE",
                          "type": "string",
                          "description": "",
                          "enable": true,
                          "isDelete": false
                        }
                      ]
                    },
                    "commonParameters": {
                      "query": [],
                      "body": [],
                      "header": [],
                      "cookie": []
                    },
                    "requestBody": {
                      "parameters": [],
                      "data": "{\\r\\n    \\"channel\\": \\"barclays\\"\\r\\n}",
                      "generateMode": "normal"
                    },
                    "auth": {},
                    "securityScheme": {},
                    "advancedSettings": {
                      "disabledSystemHeaders": {}
                    },
                    "requestResult": "",
                    "visibility": "INHERITED",
                    "moduleId": 300479,
                    "categoryId": 0,
                    "tagIds": [],
                    "preProcessors": [],
                    "postProcessors": [],
                    "inheritPostProcessors": {},
                    "inheritPreProcessors": {}
                  }
                ],
                "mocks": [],
                "customApiFields": "{}",
                "advancedSettings": {
                  "disabledSystemHeaders": {}
                },
                "mockScript": {},
                "codeSamples": [],
                "commonResponseStatus": {},
                "responseChildren": [],
                "visibility": "INHERITED",
                "moduleId": 300479,
                "oasExtensions": null,
                "type": "http",
                "preProcessors": [],
                "postProcessors": [],
                "inheritPostProcessors": {},
                "inheritPreProcessors": {}
              }
            }
          ]
        }
      ]
    }
  ]
}
"""

from logic import parse_apifox_project

if __name__ == "__main__":
    try:
        data = json.loads(json_data)
        print("Parsing Apifox project...")
        # Call the actual implementation
        apis = parse_apifox_project(data)
        
        print(f"Extracted {len(apis)} API cases.")
        for api in apis:
            print(f"- {api['name']} [{api['method']} {api['relative_path']}]")
            # print(f"  Headers: {api['headers']}")
            # print(f"  Body: {api['json_body']}")
        
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
