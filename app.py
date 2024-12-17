from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from zeep import Client
import grpc
import os

# gRPC Protobuf Imports (Assuming generated files are in the same directory)
# from your_service_pb2 import YourRequest, YourResponse
# from your_service_pb2_grpc import YourServiceStub

# Initialize Flask app
app = Flask(__name__)

# Configurations for SQLAlchemy
# Connection string for Aiven-hosted MySQL database with credentials from environment variables
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database_name = os.getenv('DB_NAME')

# Debug: Print environment variables (for verification)
print(f"DB_USERNAME={os.getenv('DB_USERNAME')}")
print(f"DB_PASSWORD={os.getenv('DB_PASSWORD')}")
print(f"DB_HOST={os.getenv('DB_HOST')}")
print(f"DB_PORT={os.getenv('DB_PORT')}")
print(f"DB_NAME={os.getenv('DB_NAME')}")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

# Create tables (ensure this is within an app context)
with app.app_context():
    db.create_all()

# Function to populate dummy data
def populate_dummy_data():
    dummy_items = [
        {"name": f"Item {i}", "description": f"Description for Item {i}"} for i in range(1, 11)
    ]
    for item in dummy_items:
        if not Item.query.filter_by(name=item['name']).first():
            new_item = Item(name=item['name'], description=item['description'])
            db.session.add(new_item)
    db.session.commit()

# Populate dummy data (ensure this is within an app context)
with app.app_context():
    populate_dummy_data()

# REST API Implementation
@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([{'id': item.id, 'name': item.name, 'description': item.description} for item in items])

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@app.route('/items', methods=['POST'])
def create_item():
    data = request.json
    try:
        new_item = Item(name=data['name'], description=data.get('description'))
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'id': new_item.id, 'name': new_item.name, 'description': new_item.description}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Item with this name already exists'}), 400

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    item.name = data.get('name', item.name)
    item.description = data.get('description', item.description)
    db.session.commit()
    return jsonify({'id': item.id, 'name': item.name, 'description': item.description})

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted'})

# SOAP API Implementation
@app.route('/soap/items', methods=['POST'])
def soap_items():
    wsdl_url = "http://example.com/your_service?wsdl"
    client = Client(wsdl_url)
    # Example SOAP request (adjust for your service)
    response = client.service.GetItems()
    return jsonify({'soap_response': response})

# gRPC API Implementation
@app.route('/grpc/items', methods=['POST'])
def grpc_items():
    # Adjust host and port to your gRPC server
    grpc_host = "localhost"
    grpc_port = "50051"
    with grpc.insecure_channel(f"{grpc_host}:{grpc_port}") as channel:
        # Example gRPC stub and request (adjust for your service)
        # stub = YourServiceStub(channel)
        # request = YourRequest(param="value")
        # response = stub.YourMethod(request)
        return jsonify({'grpc_response': "gRPC response placeholder"})

if __name__ == '__main__':
    app.run(debug=True)
