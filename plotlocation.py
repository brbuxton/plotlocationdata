import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from flask import Flask, request, jsonify
from flask_ngrok2 import run_with_ngrok
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json

app = Flask(__name__)
run_with_ngrok(app=app, auth_token=os.getenv('NGROK'))


def plot_blue_dots(coords, map_obj):
    for latitude, longitude in coords:
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=6,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7,
            popup=f"Latitude: {latitude}, Longitude: {longitude}"
        ).add_to(map_obj)


def webex_post_message(client):
    m = MultipartEncoder({'toPersonEmail': 'brbuxton@cisco.com',
                          'text': f'{client} disconnected and was last seen here',
                          'files': ('map.png',
                                    open('map.png', 'rb'),
                                    'image/png')})

    r = requests.post('https://webexapis.com/v1/messages', data=m,
                      headers={'Authorization': f'Bearer {os.getenv("WEBEXTOKEN")}',
                               'Content-Type': m.content_type})
    print(r.text)


def check_duplicate_webhook(client_mac, connected, file_path='alertsent.json'):
    try:
        with open(file_path, 'r') as json_file:
            alert_data = json.load(json_file)
    except FileNotFoundError:
        alert_data = []
    if client_mac in alert_data and connected == 'false':
        print('SKIP')
        print(alert_data)
        print(connected)
        return ('skip')
    elif client_mac in alert_data and connected == 'true':
        alert_data.remove(client_mac)
        print('REMOVED')
        print(alert_data)
        print(connected)
        with open(file_path, 'w') as json_file:
            json.dump(alert_data, json_file)
        return ('removed')
    elif client_mac not in alert_data and connected == 'false':
        alert_data.append(client_mac)
        print('ADDED/PASS')
        print(alert_data)
        print(connected)
        with open(file_path, 'w') as json_file:
            json.dump(alert_data, json_file)
        return ('pass')
    else:
        print('LAST ELSE SKIP')
        print(alert_data)
        print(connected)
        return ('skip')

def generate_map(coordinates):
    # Create a folium map centered around the first set of coordinates
    map_obj = folium.Map(location=coordinates[0], zoom_start=19)

    # Plot the blue dots on the map
    plot_blue_dots(coordinates, map_obj)

    # Save the map as a PDF
    save_folium_map_as_png(map_obj)


def save_folium_map_as_png(map_object, filename='map.png'):
    # Save the Folium map as an HTML
    map_object.save("map_with_blue_dots.html")

    # Configure Selenium webdriver options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode (without opening a browser window)

    # Create a webdriver instance
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Open the HTML file in the browser using webdriver
        driver.get('file://' + 'C:/Users/Brian/PycharmProjects/plotlocationdata/map_with_blue_dots.html')

        # Set the window size to a specific size (optional)
        driver.set_window_size(1920, 1080)  # Adjust as needed

        # Save a screenshot of the entire page
        driver.save_screenshot(filename)
    finally:
        # Close the webdriver
        driver.quit()


def record_coordinates(coordinates):
    # Load existing data from the JSON file
    file_path = 'coordinates.json'
    try:
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)
    except FileNotFoundError:
        existing_data = {}

    # Update the existing data with new data
    existing_data.update(coordinates)

    # Write the updated data back to the JSON file
    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=2)


def get_coordinates(client_mac):
    file_path = 'coordinates.json'
    with open(file_path, 'r') as json_file:
        existing_data = json.load(json_file)
    return existing_data[client_mac]


@app.route('/webhook', methods=['GET'])
def get_validator():
    return os.getenv('VALIDATOR')


@app.route('/webhook', methods=['POST'])
def webhook():
    # Place the JSON of the POST data into a variable
    data = request.json
    print(data)
    if data['version'] == '0.1' and data['alertType'] == 'Client connectivity changed' and data['sharedSecret'] == 'testpsk':
        test = check_duplicate_webhook(data['alertData']['mac'], data['alertData']['connected'])
        if data['alertData']['connected'] == 'false' and test == 'pass':
            mac = data['alertData']['mac'].lower()
            print(mac)
            coordinates = [tuple(get_coordinates(mac))]
            print(coordinates)
            generate_map(coordinates)
            webex_post_message(mac)
        return jsonify({'message': 'Webhook received successfully.'}), 200
    elif data['version'] == '2.0':
        coordinates = {entry['clientMac']: (entry['location']['lat'], entry['location']['lng'])
                       for entry in data['data']['observations']}
        record_coordinates(coordinates)
        return jsonify({'message': 'Location data received successfully.'}), 200
    else:
        return jsonify({'error': 'Latitude and longitude are required.'}), 400


if __name__ == "__main__":
    app.run()
