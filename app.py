import asyncio
from services import get_date, scrape_reviews, format_data
from flask import Flask, render_template
import requests

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/execute_script', methods=['POST'])
def execute_script():
    try:
        # get the locations ----------------------------------
        url = "https://2580958e531e4a5e908f116d9d2c2c00.m.pipedream.net"
        location_res = requests.get(url)
        if location_res.status_code == 200:
            result_json = location_res.json()
            locations_data = result_json.get("locations")

        baseURL = r"https://www.google.com/maps/search/"
        result = []
        not_accessible_location_ids = []
        for i in range(1):
            location_text = locations_data[i].get("query")
            location_id = locations_data[i].get("id")
            url = baseURL + location_text
            reviews = asyncio.new_event_loop().run_until_complete(scrape_reviews(url))
            if reviews[0]:
                data_list = format_data(
                    reviews_content_list=reviews[1])
                print(data_list)
                data_dict = {
                    'location': location_text,
                    'data': data_list
                }
                result.append(data_dict)
            else:
                not_accessible_location_ids.append(location_id)
                print(reviews[1])
        print(result)
        return render_template('index.html', result=result)

    except Exception as e:
        print(str(e))
        return render_template('error.html', item=str(e))


if __name__ == "__main__":
    app.run(debug=True)