import folium
import os
from flask import Flask, request, jsonify
from flask_ngrok2 import run_with_ngrok
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

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


@app.route('/webhook', methods=['GET'])
def get_validator():
    return os.getenv('VALIDATOR')


def coordinate_list(response):
    coordinates = []
    for client in response['data']['observations']:
        # Fill the array with the coordinates of each of the detected clients
        coordinates.append((client['location']['lat'], client['location']['lng']))
    return coordinates


@app.route('/webhook', methods=['POST'])
def webhook():
    # Place the JSON of the POST data into a variable
    data = request.json
    # TODO: Determine if POST is Webhook or Scanning data
    # TODO: If statement to record current location of clients or trigger webhook
    print(data)


def client_list(response):
    coordinates = coordinate_list(response)
    # Send the array of coordinates to the main function
    if coordinates is not None:
        generate_map(coordinates)
        return jsonify({'message': 'Map created successfully.'}), 200
    else:
        return jsonify({'error': 'Latitude and longitude are required.'}), 400

# TODO: Add function for Webhook trigger


def webex_message(client):  # FIXME: Fix RoomID
    m = MultipartEncoder({'roomId': 'Y2lzY2.....',
                          'text': f'{client} disconnected and was last seen here',
                          'files': ('map_with_blue_dots.png',
                                    open('map_with_blue_dots.png', 'rb'),
                                    'image/png')})

    r = requests.post('https://webexapis.com/v1/messages', data=m,
                      headers={'Authorization': f'Bearer {os.getenv('WEBEXTOKEN')}',
                               'Content-Type': m.content_type})
    print(r.text)


def generate_map(coordinates):
    # Create a folium map centered around the first set of coordinates
    map_obj = folium.Map(location=coordinates[0], zoom_start=15)

    # Plot the blue dots on the map
    plot_blue_dots(coordinates, map_obj)

    # Save the map as an PNG file
    map_obj.save("map_with_blue_dots.png")


if __name__ == "__main__":
    app.run()
