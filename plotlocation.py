import folium
import os
from flask import Flask, request, jsonify
from flask_ngrok2 import run_with_ngrok

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


@app.route('/webhook', methods=['POST'])
def webhook():
    # Place the JSON of the POST data into a variable
    data = request.json
    # Instantiate an empty array
    coordinates = []

    for client in data['data']['observations']:
        # Fill the array with the coordinates of each of the detected clients
        coordinates.append((client['location']['lat'], client['location']['lng']))

    # Send the array of coordinates to the main function
    if coordinates is not None:
        main(coordinates)
        return jsonify({'message': 'Map created successfully.'}), 200
    else:
        return jsonify({'error': 'Latitude and longitude are required.'}), 400


def main(coordinates):  # This function could do anything you want with the set of clients.
    # Create a folium map centered around the first set of coordinates
    map_obj = folium.Map(location=coordinates[0], zoom_start=12)

    # Plot the blue dots on the map
    plot_blue_dots(coordinates, map_obj)

    # Save the map as an HTML file
    map_obj.save("map_with_blue_dots.html")


if __name__ == "__main__":
    app.run()
