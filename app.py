import os
import logging
from flask import Flask, request, jsonify
import requests  # Make sure to import requests if you're using it to call the API

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return "Welcome to the Pharmacy API!"

@app.route('/pharmacies', methods=['GET'])
def get_pharmacies():
    zipcode = request.args.get('zipcode')
    logging.debug(f"Received request for zipcode: {zipcode}")

    if not zipcode:
        return jsonify({'error': 'Zipcode is required'}), 400

    places_url = (
        f"https://maps.googleapis.com/maps/api/place/textsearch/json"
        f"?query=pharmacy+in+{zipcode}"
        f"&key={os.getenv('GOOGLE_PLACES_API_KEY')}"
    )
    
    try:
        response = requests.get(places_url)
        response.raise_for_status()  # Raise an error for bad responses
        response_json = response.json()
        logging.debug(f"API response: {response_json}")

        place_ids = [place['place_id'] for place in response_json.get('results', [])]
        pharmacies_info = {}

        for place_id in place_ids:
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={os.getenv('GOOGLE_PLACES_API_KEY')}"
            details_response = requests.get(details_url)
            details_response.raise_for_status()
            details_json = details_response.json()

            # Extract the relevant information
            result = details_json.get('result', {})
            pharmacy_info = {
                'address': result.get('formatted_address', 'N/A'),
                'phone_number': result.get('formatted_phone_number', 'N/A'),
                'opening_hours': result.get('opening_hours', {}).get('weekday_text', 'N/A')
            }
            pharmacy_name = result.get('name', 'N/A')
            pharmacies_info[pharmacy_name] = pharmacy_info

        if not pharmacies_info:
            logging.warning(f"No pharmacies found for zipcode: {zipcode}")
            return jsonify({"error": "No pharmacies found for the provided zipcode."}), 404

        logging.debug(f"Pharmacies found: {pharmacies_info}")
        return jsonify(pharmacies_info)

    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return jsonify({"error": "Failed to fetch data from the API."}), 500
        
def test_pharmacies():
    with app.test_client() as client:
        response = client.get('/pharmacies?zipcode=02163')
        print(response.get_json())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    print('running')
    test_pharmacies()