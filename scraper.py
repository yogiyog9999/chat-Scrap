import os
import openai
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()  # Ensure to load environment variables from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)

# Enable CORS with specific configuration
CORS(app, resources={r"/chat/*": {"origins": "*"}, r"/feedback/*": {"origins": "*"}})

# Function to scrape website content
def fetch_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract visible text from the website
        return ' '.join(soup.stripped_strings)
    except Exception as e:
        return f"Error fetching content: {str(e)}"

# ChatGPT interaction function
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Replace with "gpt-3.5-turbo" if using that model
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
@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        return '', 200  # Return an empty response with status 200 for OPTIONS requests

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

# Flask route for feedback mechanism
@app.route('/feedback', methods=['POST', 'OPTIONS'])
def feedback():
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        return '', 200  # Return an empty response with status 200 for OPTIONS requests

    # Get feedback data from user
    user_feedback = request.json.get("feedback")  # thumbs_up or thumbs_down
    user_response = request.json.get("response")  # the response to be refined

    if not user_feedback or not user_response:
        return jsonify({"error": "Feedback and response are required"}), 400

    if user_feedback == "thumbs_up":
        # Optionally, save or log positive feedback
        return jsonify({"message": "Thank you for your feedback! Glad you liked it!"})

    elif user_feedback == "thumbs_down":
        # Optionally, trigger a refinement based on negative feedback
        refined_response = refine_response(user_response)
        return jsonify({"message": "Thank you for your feedback. Here's a refined response:", "response": refined_response})

    else:
        return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Function to refine the response (you can create your own logic here)
def refine_response(original_response):
    try:
        # Modify the response based on some logic, or request the AI to rephrase the response
        prompt = f"Refine the following response to make it more clear and helpful: {original_response}"
        refined_response = ask_chatgpt(prompt)
        return refined_response
    except Exception as e:
        return f"Error refining response: {str(e)}"

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Change port if needed
