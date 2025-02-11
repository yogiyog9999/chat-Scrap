import os
import openai
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
from flask_cors import CORS
from fuzzywuzzy import process

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Predefined responses for specific keywords
KEYWORD_RESPONSES = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help you?",
    "hey": "Hey! What can I do for you?",
    "thank you": "You're welcome! Let me know if there's anything else I can help with.",
    "bye": "Goodbye! Have a great day!"
}

# AI Chatbot Instructions
PROMPT = """
You are a friendly and helpful customer support agent for Wallingford Financial. Keep responses short (under 300 characters), empathetic, and engaging.

- Greet users warmly and acknowledge their issue.
- Be conversational, casual, and natural (avoid robotic tone).
- Offer clear and step-by-step solutions only when necessary.
- Ask for more details if needed instead of assuming.
- If the user seems frustrated, express empathy before offering solutions.
- End responses with friendly, helpful next steps.
"""

# Fetch chatbox settings from API
def fetch_chatbox_settings():
    api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/settings"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching chatbox settings: {e}")
        return {"error": "Failed to load chatbox settings"}

# Fetch stored page content from API
def fetch_stored_page_content():
    api_url = "https://wallingford.devstage24x7.com/wp-json/chatbot/v1/pages"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stored pages: {e}")
        return {"error": "Failed to load stored page content"}

# Extract relevant structured data
def extract_relevant_data(json_content):
    return {
        "headings": json_content.get("h1", []) + json_content.get("h2", []) + json_content.get("h3", []),
        "paragraphs": json_content.get("p", []),
        "faqs": json_content.get("faq", []),
        "contact_info": json_content.get("contact_info", {})
    }

# Generate a refined prompt using structured JSON content
def generate_prompt(user_input, json_content):
    if "error" in json_content or not json_content:
        return f"User query: {user_input}\n\nI couldn't find specific information. Please check our contact page."

    structured_data = extract_relevant_data(json_content)
    relevant_info = structured_data.get("paragraphs", [])[:2]  # Get first 2 paragraphs only

    return (
        f"Relevant information from website:\n{relevant_info}\n\n"
        f"User query: {user_input}\n\n"
        "Respond as a friendly, knowledgeable assistant for Wallingford."
    )

# Interact with ChatGPT
def ask_chatgpt(user_message, conversation_history=[]):
    try:
        messages = [{"role": "system", "content": PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Sorry, I'm having trouble generating a response."

# Find the best keyword match using fuzzy logic
def find_best_match(user_input, keywords):
    best_match, score = process.extractOne(user_input.lower(), keywords)
    return best_match if score > 80 else None

# Chatbot API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # Handle predefined responses with fuzzy matching
    best_match = find_best_match(user_input, KEYWORD_RESPONSES.keys())
    if best_match:
        return jsonify({"response": KEYWORD_RESPONSES[best_match]})

    # Fetch stored page content
    stored_pages = fetch_stored_page_content()
    if "error" in stored_pages:
        return jsonify({"error": stored_pages["error"]}), 500

    # Generate prompt and get response from ChatGPT
    prompt = generate_prompt(user_input, stored_pages)
    conversation_history = [{"role": "user", "content": user_input}]
    response = ask_chatgpt(prompt, conversation_history)
    
    return jsonify({"response": response})

# Flask route for feedback
@app.route('/feedback', methods=['POST'])
def feedback():
    user_feedback = request.json.get("feedback")
    user_response = request.json.get("response")

    if not user_feedback or not user_response:
        return jsonify({"error": "Feedback and response are required"}), 400

    if user_feedback == "thumbs_up":
        return jsonify({"response": "Thank you for your feedback! Glad you liked it!"})

    if user_feedback == "thumbs_down":
        refined_response = refine_response(user_response)
        return jsonify({"response": refined_response})

    return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Function to refine the response
def refine_response(original_response):
    try:
        prompt = f"Refine the following response to make it more clear and helpful: {original_response}"
        return ask_chatgpt(prompt)
    except Exception as e:
        return f"Error refining response: {str(e)}"

# Run Flask app
if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
        app.run(debug=True)
