from flask import Flask, request, jsonify
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import os

# API for generating a graph of cancer trend
app = Flask(__name__)
API_KEY = '326794b80b8b58850444e1f71007347d'

def get_uv_index(lat, lon):
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=hourly,daily&appid={API_KEY}"
    response = requests.get(url).json()
    return response.get("current", {}).get("uvi", "No Data")

@app.route('/api/skin_cancer_trends')
def plot_skin_cancer_trends():
    state = request.args.get("state", "Victoria")  # Set the default to Victoria
    postcode = request.args.get("postcode", 3000, type=int)  # Set the default postcode

    # Get the latitude and longitude of the designated postcode
    filtered_location = location[location['postcode'] == postcode]
    if not filtered_location.empty:
        lat, lon = filtered_location.iloc[0][['lat', 'long']]
    else:
        lat, lon = -33.8688, 151.2093  # Set the default to Sydney

    # Get UV index by using the defined function
    uv_index = get_uv_index(lat, lon)

    # Create a graph
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=incidence[incidence['State or Territory'] == state], x='Year', y='Count', hue='Cancer group/site', marker='o')
    sns.lineplot(data=mortality[mortality['State or Territory'] == state], x='Year', y='Count', hue='Cancer group/site', marker='o', linestyle='dashed')

    plt.title(f'Skin Cancer Trends in {state} (UV Index: {uv_index})')
    plt.xlabel('Year')
    plt.ylabel('Count')
    plt.legend(title='Cancer Type')
    plt.grid()

    # Return an encoded image by Base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.read()).decode('utf-8')
    return jsonify({
        'state': state,
        'postcode': postcode,
        'iv_index': uv_index,
        'chart': f"data:image/png;base64, {img_base64}"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) # Get the port from the environment variable on Render
    app.run(debug=True, host='0.0.0.0', port=5000) # Allow access from all IP addresses
