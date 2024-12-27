import os
import openai
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Fetch selected pages from the API
def get_selected_pages():
    try:
        # Make a GET request to the API that provides the selected pages
        api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/selected-pages"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            return response.json()  # Return the JSON response with selected pages
        else:
            return {"error": f"Failed to fetch selected pages: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error fetching selected pages: {str(e)}"}

# Function to fetch specific content from a URL
def fetch_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract headers (h1 to h6) and paragraphs (p)
        content = {
            "h1": [header.get_text(strip=True) for header in soup.find_all('h1')],
            "h2": [header.get_text(strip=True) for header in soup.find_all('h2')],
            "h3": [header.get_text(strip=True) for header in soup.find_all('h3')],
            "h4": [header.get_text(strip=True) for header in soup.find_all('h4')],
            "h5": [header.get_text(strip=True) for header in soup.find_all('h5')],
            "h6": [header.get_text(strip=True) for header in soup.find_all('h6')],
            "p": [para.get_text(strip=True) for para in soup.find_all('p')]
        }
        
        # Convert content to JSON format
        return json.dumps(content)
    except Exception as e:
        return json.dumps({"error": f"Error fetching content: {str(e)}"})

# Function to generate a refined prompt using JSON content
def generate_prompt(user_input, json_content):
    return (
        f"Here is some content from our website (structured in JSON format):\n{json_content}\n\n"
        f"User query: {user_input}\n\n"
        "Please respond as a knowledgeable support assistant for Wallingford Financial, based on the above content."
    )

# Function to interact with ChatGPT
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": "You are a knowledgeable support assistant for Wallingford Financial."
            }, {
                "role": "user", "content": prompt
            }]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with ChatGPT: {str(e)}"

# Flask route for chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # Fetch the selected pages dynamically from the API
    selected_pages = get_selected_pages()

    if "error" in selected_pages:
        return jsonify({"error": selected_pages["error"]}), 500

    # Fetch website content from selected pages
    content_from_pages = {}
    for page_name, page_url in selected_pages.items():
        json_content = fetch_website_content(page_url)
        
        if "error" in json.loads(json_content):
            return jsonify({"error": json.loads(json_content)["error"]}), 500

        # Store content from each page
        content_from_pages[page_name] = json.loads(json_content)
    
    # Convert content into a single JSON string (flattened if necessary)
    json_content = json.dumps(content_from_pages)

    # Create a refined prompt using user input and fetched JSON content
    prompt = generate_prompt(user_input, json_content)

    # Ask GPT for a response
    response = ask_chatgpt(prompt)
    return jsonify({"response": response})
    
@app.route('/feedback', methods=['POST'])
def feedback():
    user_feedback = request.json.get("feedback")
    user_response = request.json.get("response")

    if not user_feedback or not user_response:
        return jsonify({"error": "Feedback and response are required"}), 400

    if user_feedback == "thumbs_up":
        return jsonify({"response": "Thank you for your feedback! Glad you liked it!"})

    elif user_feedback == "thumbs_down":
        refined_response = refine_response(user_response)
        return jsonify({"response": "Thank you for your feedback. Here's a refined response:", "response": refined_response})

    else:
        return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Function to refine the response
def refine_response(original_response):
    try:
        prompt = f"Refine the following response to make it more clear and helpful: {original_response}"
        refined_response = ask_chatgpt(prompt)
        return refined_response
    except Exception as e:
        return f"Error refining response: {str(e)}"

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
