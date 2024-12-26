from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    urls = data.get("urls", [])
    scraped_content = {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for url in urls:
        try:
            # Fetch the page content with headers
            response = requests.get(url, headers=headers)
            
            # If response status code is not 200, skip the scraping
            if response.status_code != 200:
                scraped_content[url] = f"Error: {response.status_code} - {response.reason}"
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the text of the page (you can customize this to extract specific data)
            scraped_content[url] = soup.get_text(strip=True)
            
            # Adding delay to avoid rate limiting
            time.sleep(1)
        except Exception as e:
            # If any error occurs, return the error message
            scraped_content[url] = f"Error: {str(e)}"
    
    # Return the scraped data as a JSON response
    return jsonify(scraped_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
