from flask import Flask, jsonify, request, Response, stream_with_context, redirect, url_for
import pandas as pd
import time
from flask_cors import CORS
# Ensure automatedorderaction.py is in the same directory or appropriately referenced
from autotradewithfunction import perform_trade  # Adjust this if necessary
from updatedmodelclean import tradestrategy  # Adjust this if necessary
app = Flask(__name__)
CORS(app, resources={r"/stream": {"origins": "*"}}, supports_credentials=True)

api_key = 'PKBSMA05S2WDBRDKZVDX'
secret_key = 'SUcB01ge2dycnArTOJNPdAtimmcUKgU4txCeKbJ1'


tradestrategy()

@app.route('/')
def home():
    return redirect(url_for('static', filename='index_new.html'))

# @app.route('/set_keys', methods=['POST'])
# def set_keys():
#     data = request.json
#     api_key = data.get('apiKey')
#     secret_key = data.get('secretKey')
#     # Store these keys securely, use them for your trading functions
#     return jsonify({"status": "success", "message": "Keys set successfully"}), 200


def stream_data():
    data = pd.read_csv('signals.csv', chunksize=1)  # Stream one row at a time
    for chunk in data:
        json_data = chunk.to_json(orient='records')
        print(json_data)  # Add this line to debug
        chunk_dict = chunk.iloc[0].to_dict()  # Convert the first (and only) row of the chunk to a dictionary
        print(chunk_dict)  # Debug print to see the actual data structure
        perform_trade(chunk_dict)  # Pass the dictionary, not the JSON string
        yield f"data:{json_data}\n\n"
        time.sleep(1)  # Simulate real-time data with a delay

@app.route('/stream')
def stream_csv_data():
    response = Response(stream_with_context(stream_data()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)



# api_key = 'PKUZK57KPFZHJJMJJH3A'
# secret_key = 'rpu9svXtZtevOGP3CXjlgxRkhQHC1lABqfmB0QJC'
    #rpu9svXtZtevOGP3CXjlgxRkhQHC1lABqfmB0QJC