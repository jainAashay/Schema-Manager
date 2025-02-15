import logging
from flask import Blueprint,Flask, jsonify,request, redirect, url_for, send_file
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.config.config import *
from bson.objectid import ObjectId
from pymongo import MongoClient,ReplaceOne
from werkzeug.utils import secure_filename
from io import BytesIO
import pandas as pd

schema_manager_bp = Blueprint('schema_manager',__name__)

@schema_manager_bp.route('/schema/create', methods=['POST'])
@jwt_required()
def createCollection():

    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401
    
    try:
        request_schema=request.get_json()
        logging.log(logging.DEBUG,request_schema['name'])

        claims=get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        user_schemas=user['schemas']
        request_schema['name']=user['username']+'_'+request_schema['name']
        matching_schemas = [request_schema for schema in user_schemas if schema["name"] == request_schema["name"]]

        if matching_schemas:
            return jsonify({'message':'Schema Already exists.'}),409
                
        elif len(user_schemas)>10:
            return jsonify({'message':'Schema Creation Limit exceeded.'}),400
        
        session.start_transaction()
        db_schema_manager.create_collection(request_schema['name'])
        user_schemas.append(request_schema)
        schema_data.update_one({'username': claims.get('username')}, {'$set': {'schemas': user_schemas}})
        session.commit_transaction()
        return jsonify({"message": "Schema created"}), 200  

    except Exception as e:
        logging.error(str(e))
        session.abort_transaction()
        return jsonify({"message": "An error occured"}), 500
    
@schema_manager_bp.route('/schema/<schema>/delete', methods=['DELETE'])
@jwt_required()
def delete_collection(schema):
    
        if not checkLogin():
            return jsonify({"message" : "Unauthored. Please log in"}), 401

        try:
                
            claims=get_jwt()
            user = schema_data.find_one({'username': claims.get('username')})
            schema=user['username']+'_'+schema
            user_schemas=user['schemas']
            session.start_transaction()
            for user_schema in user_schemas:
                if user_schema['name']==schema:
                    user_schemas.remove(user_schema)
                    schema_data.update_one({'username': claims.get('username')}, {'$set': {'schemas': user_schemas}})
                    break

            db_schema_manager.get_collection(schema).drop()
            session.commit_transaction()
            return jsonify({"message": "Schema deleted"}), 200
            
        except Exception as e:
            logging.error(str(e))
            session.abort_transaction()
            return jsonify({"message": "An error occured"}), 500
            

@schema_manager_bp.route('/schema/<schema>/view', methods=['POST'])
@jwt_required()
def get_documents(schema):
    if not checkLogin():
        return jsonify({"message": "Unauthorized. Please log in"}), 401

    try:
        request_data = request.get_json()
        filter_params = request_data.get('filter_params', {})
        query_params = request_data.get('query_params', {})
        
        page_number = int(query_params.get('page_number', 1))
        page_size = int(query_params.get('page_size', 20))

        offset = (page_number-1) * page_size

        claims = get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        schema = user['username'] + '_' + schema

        # Get default filters if none are provided
        filters = next((s['filters'] for s in user['schemas'] if s['name'] == schema), None)

        # Apply filters to query
        collection = db_schema_manager.get_collection(schema)
        documents = collection.find(filter_params).skip(offset).limit(page_size)
        total_count=collection.count_documents(filter_params)

        # Process documents
        documents_list = list(documents)
        keys = set()
        for doc in documents_list:
            keys.update(doc.keys())
            doc['_id'] = str(doc['_id'])

        return jsonify({"total_count": total_count,"data": documents_list,"keys": list(keys),"filters": filters}), 200

    except Exception as e:
        logging.error(str(e))
        return jsonify({"message": "An error occurred"}), 500

@schema_manager_bp.route('/schema/<schema>/bulk-replace', methods=['POST'])
@jwt_required()
def bulk_replace(schema):

    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in" }), 401
    
    # Get the request JSON data
    data = request.get_json()
    
    if not isinstance(data, list):
        return jsonify({"error": "Request body must be a list of documents with '_id'."}), 400
    
    # Prepare bulk replace operations
    operations = []
    for doc in data:
        if '_id' not in doc:
            return jsonify({"error": "Each document must include '_id' field."}), 400
        
        # Handle ObjectId format in the document
        id_field = doc['_id']
        if isinstance(id_field, str):
            try:
                object_id = ObjectId(id_field)
            except Exception as e:
                return jsonify({"error": f"Invalid ObjectId format: {e}"}), 400
        else:
            return jsonify({"error": "Invalid '_id' format."}), 400
        
        # Remove _id from the update document
        update_doc = {k: v for k, v in doc.items() if k != '_id'}
        
        # Append ReplaceOne operation
        operations.append(ReplaceOne({'_id': object_id}, update_doc, upsert=False))
    
    # Execute bulk replace
    try:
        result = db_schema_manager.get_collection(schema).bulk_write(operations)
    except Exception as e:
        return jsonify({"error": f"Bulk write error: {e}"}), 500
    
    # Return response
    return jsonify({"matched_count": result.matched_count,"modified_count": result.modified_count,"upserted_count": result.upserted_count}), 200

@schema_manager_bp.route('/schemas/view', methods=['GET'])
@jwt_required()
def view_all_schemas():

    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401
    try:
        claims=get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        
        schemas=[]
        if not user:
            return jsonify({'schemas':schemas}),200
        
        for schema in user['schemas']:
            schema['name']=schema['name'].split('_')[1]
            schemas.append(schema)
        return jsonify({'schemas':schemas}),200

    except Exception as e:
        logging.error(str(e))
        return jsonify({'message':'An error occured.'}),500

@schema_manager_bp.route('/schema/<schema>/insert', methods=['POST'])
@jwt_required()
def insertData(schema):
    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401

    try:
        claims=get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        schema=user['username']+'_'+schema
        data=request.get_json()['data']

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if not isinstance(data, list):
            return jsonify({"error": "Data should be a list of documents"}), 400
        
        result = db_schema_manager.get_collection(schema).insert_many(data)
        
        return jsonify({ "message": "Data inserted successfully","inserted_ids": [str(id) for id in result.inserted_ids]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    except Exception as e:
        logging.error(str(e))
        return jsonify({'message':'An error occured.'}),500

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 

@schema_manager_bp.route('/schema/<schema>/data/upload', methods=['POST'])
@jwt_required()
def upload_file(schema):
    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401

    try:
        session.start_transaction()
        claims=get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        schema=user['username']+'_'+schema
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join("uploads", filename))  # Save file temporarily
            if filename.endswith('.csv'):
                data = pd.read_csv(os.path.join("uploads", filename))
            elif filename.endswith('.xlsx'):
                data = pd.read_excel(os.path.join("uploads", filename))

            records = data.to_dict(orient='records')
            if schema not in db_schema_manager.list_collection_names():
                return jsonify({"error": f"Collection '{schema}' does not exist."}), 400
    
            result = db_schema_manager.get_collection(schema).insert_many(records)
            session.commit_transaction()
            return jsonify({ "message": "Data inserted successfully",
                              "inserted_ids": [str(id) for id in result.inserted_ids]}), 200

        else:
            session.abort_transaction()
            return jsonify({"error": "Invalid file type. Only CSV and Excel are allowed"}), 400

    except Exception as e:
        session.abort_transaction()
        return jsonify({"error": str(e)}), 500

    finally:
        os.remove(os.path.join("uploads", filename))


@schema_manager_bp.route('/schema/<schema>/data/delete/<id>', methods=['DELETE'])
@jwt_required()
def deleteById(schema,id):
    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401
    
    try:
        claims=get_jwt()
        session.start_transaction()
        user = schema_data.find_one({'username': claims.get('username')})
        schema=user['username']+'_'+schema
        if schema not in db_schema_manager.list_collection_names():
            return jsonify({"error": f"Collection '{schema}' does not exist."}), 400
        db_schema_manager.get_collection(schema).delete_one({'_id': ObjectId(id)})
        session.commit_transaction()
        return jsonify({ "message": "Deleted Successfully" }), 200

    except Exception as e:
        session.abort_transaction()
        return jsonify({"error": str(e)}), 500

@schema_manager_bp.route('/schema/<schema>/data/update', methods=['PUT'])
@jwt_required()
def updateById(schema):
    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401

    try:
        claims=get_jwt()
        session.start_transaction()
        data=request.get_json()
        user = schema_data.find_one({'username': claims.get('username')})
        schema=user['username']+'_'+schema
        id=ObjectId(data['_id'])
        data.pop('_id',None)
        if schema not in db_schema_manager.list_collection_names():
            return jsonify({"error": f"Collection '{schema}' does not exist."}), 400
        result=db_schema_manager.get_collection(schema).replace_one({'_id': id},data )
        session.commit_transaction()

        if result.matched_count == 0:
            return jsonify({"message": "No document found to update"}), 404
        if result.modified_count == 0:
            return jsonify({"message": "No changes were made"}), 400

        return jsonify({"message": "Document updated successfully!"}), 200


    except Exception as e:
        session.abort_transaction()
        return jsonify({"error": str(e)}), 500

@schema_manager_bp.route('/schema/<schema>/data/download', methods=['GET'])
@jwt_required()
def download_xlsx(schema):
    if not checkLogin():
        return jsonify({ "message" : "Unauthored. Please log in"}), 401

    try:
        claims=get_jwt()
        user = schema_data.find_one({'username': claims.get('username')})
        schema=user['username']+'_'+schema
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            batch_start = 0
            while True:
                batch_data = list(db_schema_manager.get_collection(schema).find().skip(batch_start).limit(1000))
                if not batch_data:
                    break
                df_batch = pd.DataFrame(batch_data)
                df_batch.drop(columns=['_id'], inplace=True, errors='ignore')
                df_batch.to_excel(writer, index=False, header=not bool(batch_start), sheet_name='schema', startrow=batch_start % 1000)
                batch_start += 1000

        output.seek(0)
        return send_file(output, as_attachment=True, download_name=schema+".xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        logging.error(str(e))
        return jsonify({"error": str(e)}), 500


def checkLogin():
    user_id=get_jwt_identity()
    login_user=login_data.find_one({'_id': ObjectId(user_id)})

    if login_user is None:
        return False
    else:
        return True