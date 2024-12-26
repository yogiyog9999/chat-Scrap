from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    urls = data.get("urls", [])
    scraped_content = {}

    for url in urls:
        try:
            # Fetch the page content
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the text of the page (you can customize this to extract specific data)
            scraped_content[url] = soup.get_text(strip=True)
        except Exception as e:
            # If any error occurs, return the error message
            scraped_content[url] = f"Error: {str(e)}"
    
    # Return the scraped data as a JSON response
    return jsonify(scraped_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
