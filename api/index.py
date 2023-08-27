from dotenv import dotenv_values
from flask import (Flask, jsonify, request)
from flask_cors import (CORS, cross_origin)
import requests as r
import json
import os

config = dotenv_values(".env")

app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)

NOTION_SECRET = config.get('NOTION_SECRET') or os.environ.get('NOTION_SECRET')
DATABASE_ID = config.get('DATABASE_ID') or os.environ.get('DATABASE_ID')
NOTION_VERSION = config.get('NOTION_VERSION') or os.environ.get('NOTION_VERSION')

url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {NOTION_SECRET}",
    "Notion-Version": NOTION_VERSION,
}

create_url = "https://api.notion.com/v1/pages"

archive_url = "https://api.notion.com/v1/pages"

@app.route('/api/tasks', methods=['GET', 'POST'])
@cross_origin()
def tasks():
    if request.method == 'POST':
        json_data = json.loads(request.get_data())

        name = json_data['name']

        res = r.post(create_url, headers=headers, data=json.dumps({
            "parent": { "type": "database_id", "database_id": DATABASE_ID },
            "properties": {
                "name": {
                    "title": [{ "text": { "content": name } }]
                }
            },
        }))

        created_task = res.json()
        
        return jsonify({ "status": True, "id": created_task['id'] })

    res = r.post(url, headers=headers)

    return jsonify({ "tasks": parse_results(res.json()['results']) })

@app.route('/api/tasks/<task_id>', methods=['PUT', 'DELETE'])
@cross_origin()
def task(task_id):
    if request.method == 'PUT':
        json_data = json.loads(request.get_data())

        name = json_data['name']
        is_completed = json_data['isCompleted']

        r.patch(f"{archive_url}/{task_id}", headers=headers, data=json.dumps({
            "properties": {
                "name": {
                    "title": [{
                        "text": {
                            "content": name
                        }
                    }]
                },
                "isCompleted": {
                    "checkbox": is_completed,
                }
            }
        }))

        return jsonify({ "status": True })

    r.patch(f"{archive_url}/{task_id}", headers=headers, data=json.dumps({
        "archived": True
    }))
    
    return jsonify({ "status": True })


def parse_results(results):
    result = []

    for res in results:
        task = TaskModel(res)

        result.append(task.value)

    return result 


class TaskModel:
    def __init__(self, raw_record) -> None:
        self.id = raw_record['id'] # raw_record['properties']['id']['unique_id']['number']
        self.name = raw_record['properties']['name']['title'][0]['text']['content']
        self.is_complete = raw_record['properties']['isCompleted']['checkbox']

    @property
    def value(self):
        return {
            "id": self.id,
            "name": self.name,
            "is_completed": self.is_complete
        }
