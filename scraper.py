import os
import openai
from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from flask_cors import CORS
from cachetools import LRUCache, cached

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Cache setup (limit to 10 most recent pages)
cache = LRUCache(maxsize=10)

# Fetch predefined pages dynamically from the API
def fetch_predefined_pages():
    try:
        # Make a GET request to your API endpoint to get predefined pages
        response = requests.get("https://wallingford.devstage24x7.com/wp-json/chatbox/v1/selected-pages")
        response.raise_for_status()
        # Return the list of page URLs from the response
        return response.json()  # Example: { "home": "https://isigmasolutions.com/", ... }
    except Exception as e:
        return f"Error fetching predefined pages: {str(e)}"

# Fetch content with caching
@cached(cache)
def fetch_website_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return ' '.join(soup.stripped_strings)  # Extract visible text
    except Exception as e:
        return f"Error fetching content: {str(e)}"

# Summarize content
def summarize_content(content):
    try:
        prompt = f"Summarize the following content to focus on the key points:\n{content}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": "You are a helpful summarization assistant."
            }, {
                "role": "user", "content": prompt
            }]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error summarizing content: {str(e)}"

# Decide the most relevant page based on the query
def decide_relevant_page(query, predefined_pages):
    try:
        prompt = f"Given the following predefined pages:\n{list(predefined_pages.keys())},\n" \
                 f"and their purpose (home: general info, about: company details, services: offerings, contact: contact info), " \
                 f"which page is most relevant for this query: {query}?\nProvide only the page name."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": "You are a helpful assistant that selects the most relevant page."
            }, {
                "role": "user", "content": prompt
            }]
        )
        return response['choices'][0]['message']['content'].strip().lower()
    except Exception as e:
        return "home"  # Default to home if there's an error

# ChatGPT interaction function to mimic human-like support responses
def ask_chatgpt(prompt):
    try:
        # Modify the system prompt to simulate a human-like wallingford Support team member
        prompt_with_human_tone = f"""
        You are a support agent for wallingford. Respond to the user's query in a friendly, professional, and helpful manner, 
        similar to how a support representative would respond. The tone should be clear, empathetic, and solution-oriented.

        Here is the information you have about our services and website:

        {prompt}

        Please respond in the style of an wallingford support representative.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{
                "role": "system", "content": prompt_with_human_tone
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

    # Fetch predefined pages dynamically from the API
    predefined_pages = fetch_predefined_pages()
    if isinstance(predefined_pages, str) and "Error" in predefined_pages:
        return jsonify({"error": predefined_pages}), 500

    # Determine the most relevant page based on the query
    relevant_page = decide_relevant_page(user_input, predefined_pages)
    page_url = predefined_pages.get(relevant_page, predefined_pages["home"])

    # Fetch content from the selected page
    page_content = fetch_website_content(page_url)
    if "Error" in page_content:
        return jsonify({"error": page_content}), 500

    # Summarize the content
    summarized_content = summarize_content(page_content)

    # Combine the summarized content with user query and send it to ChatGPT
    prompt = f"The following is summarized content from the {relevant_page} page:\n{summarized_content}\n\nUser query: {user_input}"
    response = ask_chatgpt(prompt)

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

    elif user_feedback == "thumbs_down":
        refined_response = refine_response(user_response)
        return jsonify({"response": "Thank you for your feedback. Here's a refined response:", "refined_response": refined_response})

    else:
        return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Function to refine response
def refine_response(original_response):
    try:
        prompt = f"Refine the following response to make it clearer and more helpful: {original_response}"
        refined_response = ask_chatgpt(prompt)
        return refined_response
    except Exception as e:
        return f"Error refining response: {str(e)}"

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
