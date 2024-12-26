import os
import openai
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)  # This will allow all domains to access your Flask app

# Function to scrape website content
def fetch_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract visible text from the website
        return ' '.join(soup.stripped_strings)
    except Exception as e:
        return f"Error fetching content: {str(e)}"

# ChatGPT interaction function (updated for new API and chat completions)
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Replace "gpt-4" with "gpt-3.5-turbo" if you are using that model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        # Extract and return the AI's response
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with ChatGPT: {str(e)}"

# Flask route for chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # Fetch website content
    website_content = fetch_website_content("https://isigmasolutions.com/")
    if "Error" in website_content:
        return jsonify({"error": website_content}), 500

    # Combine user input with website content
    prompt = f"The following content is from the website:\n{website_content}\n\nUser query: {user_input}"
    response = ask_chatgpt(prompt)
    return jsonify({"response": response})

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Change port if needed
