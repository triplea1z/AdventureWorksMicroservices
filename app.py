from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
from flasgger import Swagger, swag_from
from zeep import Client
import grpc
import os

# Initialize Flask app
app = Flask(__name__)
api = Api(app)

# Configuring Swagger
app.config['SWAGGER'] = {
    'title': 'My API',
    'uiversion': 3
}
swagger = Swagger(app)

# Configurations for SQLAlchemy
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database_name = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

# Create tables
with app.app_context():
    db.create_all()

# Populate dummy data
def populate_dummy_data():
    dummy_items = [
        {"name": f"Item {i}", "description": f"Description for Item {i}"} for i in range(1, 11)
    ]
    for item in dummy_items:
        if not Item.query.filter_by(name=item['name']).first():
            new_item = Item(name=item['name'], description=item['description'])
            db.session.add(new_item)
    db.session.commit()

with app.app_context():
    populate_dummy_data()

# REST API Endpoints
class GetItems(Resource):
    @swag_from({
        'responses': {
            200: {
                'description': 'Returns a list of items.',
                'content': {
                    'application/json': {
                        'examples': {
                            'example1': {
                                'summary': 'Successful response',
                                'value': [
                                    {"id": 1, "name": "Item 1", "description": "Description for Item 1"}
                                ]
                            }
                        }
                    }
                }
            }
        }
    })
    def get(self):
        """
        Retrieve all items from the database.
        """
        items = Item.query.all()
        return jsonify([{'id': item.id, 'name': item.name, 'description': item.description} for item in items])

class GetItem(Resource):
    @swag_from({
        'parameters': [
            {
                'name': 'item_id',
                'in': 'path',
                'type': 'integer',
                'required': True,
                'description': 'The ID of the item to retrieve'
            }
        ],
        'responses': {
            200: {
                'description': 'Returns a single item.',
                'content': {
                    'application/json': {
                        'examples': {
                            'example1': {
                                'summary': 'Successful response',
                                'value': {"id": 1, "name": "Item 1", "description": "Description for Item 1"}
                            }
                        }
                    }
                }
            },
            404: {
                'description': 'Item not found.'
            }
        }
    })
    def get(self, item_id):
        """
        Retrieve a specific item by ID.
        """
        item = Item.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

class CreateItem(Resource):
    @swag_from({
        'requestBody': {
            'required': True,
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'}
                        }
                    },
                    'examples': {
                        'example1': {
                            'summary': 'Create a new item',
                            'value': {"name": "New Item", "description": "New Description"}
                        }
                    }
                }
            }
        },
        'responses': {
            201: {
                'description': 'Item created successfully.',
                'content': {
                    'application/json': {
                        'examples': {
                            'example1': {
                                'summary': 'Successful creation',
                                'value': {"id": 11, "name": "New Item", "description": "New Description"}
                            }
                        }
                    }
                }
            },
            400: {
                'description': 'Item with this name already exists.'
            }
        }
    })
    def post(self):
        """
        Create a new item.
        """
        data = request.json
        try:
            new_item = Item(name=data['name'], description=data.get('description'))
            db.session.add(new_item)
            db.session.commit()
            return jsonify({'id': new_item.id, 'name': new_item.name, 'description': new_item.description}), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({'error': 'Item with this name already exists'}), 400

api.add_resource(GetItems, '/items')
api.add_resource(GetItem, '/items/<int:item_id>')
api.add_resource(CreateItem, '/items')

if __name__ == '__main__':
    app.run(debug=True)
