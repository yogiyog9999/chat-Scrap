import requests

api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/selected-pages"
headers = {
    'Authorization': 'Bearer 4567890'
}
def fetch_selected_pages():
  
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        try:
            return response.json()  # Parse JSON if possible
        except ValueError:
            return {"error": "Invalid JSON response from server", "response_text": response.text}
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            return {"error": "Access denied. Please check your API permissions."}
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.RequestException as req_err:
        return {"error": f"Request failed: {req_err}"}

result = fetch_selected_pages()
print(result)
