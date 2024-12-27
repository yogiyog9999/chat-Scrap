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
CORS(app)

# Predefined keyword responses
KEYWORD_RESPONSES = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help?",
    "hey": "Hey! How can I assist you?",
    "contact": "You can reach us via email at support@example.com or call us at +123456789.",
    "call": "Please call us at +123456789 for assistance.",
    "phone": "Our phone number is +123456789.",
    "email": "You can email us at support@example.com.",
    "address": "Our address is 1234 Example Street, Example City, EX 12345."
}

# Function to check for keyword matches
def check_keywords(user_input):
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword.lower() in user_input.lower():
            return response
    return None

# Function to fetch selected page URLs from the API
def fetch_selected_pages():
    try:
        response = requests.get("https://wallingford.devstage24x7.com/wp-json/chatbox/v1/selected-pages")
        return response.json() if response.status_code == 200 else {}
    except Exception as e:
        return {"error": f"Error fetching selected pages: {str(e)}"}

# Function to fetch content for a specific URL
def fetch_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return ' '.join(soup.stripped_strings)
    except Exception as e:
        return f"Error fetching content: {str(e)}"

# ChatGPT interaction function
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": "You are a helpful assistant."
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

    # Check for keyword matches
    keyword_response = check_keywords(user_input)
    if keyword_response:
        return jsonify({"response": keyword_response})

    # Fetch selected pages from the API
    selected_pages = fetch_selected_pages()
    if "error" in selected_pages:
        return jsonify({"error": selected_pages["error"]}), 500

    # Fetch content from selected pages and combine
    combined_content = ""
    for title, url in selected_pages.items():
        content = fetch_website_content(url)
        if "Error" in content:
            return jsonify({"error": content}), 500
        combined_content += f"{title}:\n{content}\n\n"

    # Create prompt using user input and combined website content
    prompt = (
        f"The following content is from the website and reply as a support team member:\n{combined_content}\n\n"
        f"User query: {user_input}"
    )
    response = ask_chatgpt(prompt)
    return jsonify({"response": response})

# Flask route for feedback mechanism
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
        return jsonify({"response": "Thank you for your feedback. Here's a refined response:", "refined_response": refined_response})

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
