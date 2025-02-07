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
CORS(app)  # Enable CORS for all routes

# Predefined responses for specific keywords
KEYWORD_RESPONSES = {
    # Greetings
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help you?",
    "hey": "Hey! What can I do for you?",
    "good morning": "Good morning! How can I assist you?",
    "good afternoon": "Good afternoon! How can I help you?",
    "good evening": "Good evening! How can I assist you?",
    "how are you": "I'm just a bot, but I'm here to help! How can I assist you?",

    # Contact Information
    "address": "Our office address is 382 Winston Rd, Grimsby, ON L3M 0H2, Canada.",
    "location": "We are located at 382 Winston Rd, Grimsby, ON L3M 0H2, Canada.",
    "located": "We are located at 382 Winston Rd, Grimsby, ON L3M 0H2, Canada.",
    "contact": "You can contact us via email at contact@isigmasolutions.com or call us at 1-877-974-4744.",
    "connect": "Feel free to reach us at contact@isigmasolutions.com or call us at 1-877-974-4744.",
    "reach": "You can get in touch with us via email at contact@isigmasolutions.com or phone at 1-877-974-4744.",
    "email": "You can reach us at contact@isigmasolutions.com.",
    "phone": "Our toll-free number is 1-877-974-4744.",
    "call": "Please feel free to give us a call at 1-877-974-4744.",
    "mobile": "You can contact us at 1-877-974-4744.",
    "where are you located": "Our office is located at 382 Winston Rd, Grimsby, ON L3M 0H2, Canada.",
    "office address": "We are located at 382 Winston Rd, Grimsby, ON L3M 0H2, Canada.",

    # Services
    "services": "We offer a range of digital solutions, including Web Development, WordPress Development, Mobile Apps, SEO, and more. How can we assist you?",
    "web development": "We provide professional web development services, building dynamic and responsive websites. Learn more at https://isigmasolutions.com/",
    "wordpress development": "Our WordPress development services help you create custom, scalable WordPress solutions. Learn more at https://isigmasolutions.com/",
    "resource outsourcing": "We provide skilled professionals for hire to support your development needs. Learn more at https://isigmasolutions.com/",
    "mobile apps development": "We develop high-quality mobile applications for Android and iOS platforms. Learn more at https://isigmasolutions.com/",
    "website maintenance": "We offer website maintenance services to ensure your website remains up-to-date and secure. Learn more at https://isigmasolutions.com/",
    "search engine optimization": "Our SEO services help improve your website's visibility on search engines. Learn more at https://isigmasolutions.com/",
    "local seo services": "We specialize in local SEO strategies to help businesses attract customers nearby. Learn more at https://isigmasolutions.com/",
    "voice search optimization": "Our voice search optimization services ensure your content is discoverable via voice assistants. Learn more at https://isigmasolutions.com/",
    "social media": "We provide social media marketing and management services to grow your online presence. Learn more at https://isigmasolutions.com/",
    "ui ux designing": "Our UI/UX design services focus on creating engaging and user-friendly interfaces. Learn more at https://isigmasolutions.com/",
    "pay per click": "We offer PPC advertising services to drive traffic and increase conversions. Learn more at https://isigmasolutions.com/",

    # Common Questions
    "quote": "For a quote, please contact us at contact@isigmasolutions.com or call 1-877-974-4744.",
    "pricing": "For pricing details, please reach out to us via email at contact@isigmasolutions.com.",
    "help": "Of course! How can I help you today?",
    "support": "Our support team is here to help. Email us at contact@isigmasolutions.com or call 1-877-974-4744.",
    "assist": "I’m here to assist you! Please let me know how I can help.",
    "information": "What information are you looking for? I'd be happy to help.",
    "details": "Could you specify what details you need? I'll do my best to assist you.",
    "products": "We offer various digital solutions, including web development, mobile apps, SEO, and more. Could you specify what you're looking for?",
    "solutions": "We provide tailored digital solutions. Please let me know what you need assistance with.",
    "hours": "Our office hours are 9:00 AM to 5:00 PM, Monday to Friday.",
    "timing": "We’re available from 9:00 AM to 5:00 PM, Monday to Friday.",
    "open": "Our office is open from 9:00 AM to 5:00 PM, Monday to Friday.",
    "closed": "We are closed outside of 9:00 AM to 5:00 PM, Monday to Friday.",
    "business hours": "Our business hours are 9:00 AM to 5:00 PM, Monday to Friday.",
    "availability": "We’re available during our business hours, 9:00 AM to 5:00 PM, Monday to Friday.",
    "how can I": "Could you tell me more about what you’re looking for? I’d be happy to assist!",
    "what do you do": "We offer various digital services including Web Development, SEO, Mobile App Development, and more. How can we assist you?",

    # Miscellaneous
    "thank you": "You're welcome! Let me know if there's anything else I can help with.",
    "thanks": "Glad I could help! Let me know if there’s more I can assist you with.",
    "bye": "Goodbye! Have a great day!",
    "goodbye": "Take care! Feel free to reach out anytime.",
    "see you": "See you! Have a wonderful day!",
    "something else": "Sure! What else can I assist you with?",
    "not sure": "No problem! Let me know how I can assist you.",
    "help me": "I’d be happy to help! Could you tell me more about what you need?",
}


# Function to fetch chatbox settings from API
def fetch_chatbox_settings():
    try:
        api_url = "https://isigmasolutions.com/wp-json/chatbox/v1/settings"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch chatbox settings: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error fetching chatbox settings: {str(e)}"}

# Update the predefined responses with dynamic values
def update_keyword_responses(settings):
    global KEYWORD_RESPONSES
    if "chatbox_address" in settings:
        KEYWORD_RESPONSES["address"] = f"Our office address is {settings['chatbox_address']}."
    if "chatbox_contact" in settings:
        KEYWORD_RESPONSES["contact"] = f"You can contact us via {settings['chatbox_contact']}."
    if "chatbox_email" in settings:
        KEYWORD_RESPONSES["email"] = f"You can reach us at {settings['chatbox_email']}."
    if "chatbox_hours" in settings:
        KEYWORD_RESPONSES["call"] = f"Our operational hours are {settings['chatbox_hours']}."
    if "chatbox_services" in settings:
        KEYWORD_RESPONSES["services"] = f"We offer the following services: {settings['chatbox_services']}."

# Function to fetch selected pages from the API
def get_selected_pages():
    api_url = "https://isigmasolutions.com/wp-json/chatbox/v1/selected-pages"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.json()  # Return the JSON content if successful
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            return {"error": "Access denied. Please check your API permissions."}
        return {"error": f"HTTP error occurred: {str(http_err)}"}
    except requests.RequestException as e:
        return {"error": f"Failed to fetch selected pages: {str(e)}"}

# Function to fetch specific content from a URL
def fetch_website_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract headers and paragraphs
        content = {
            "h1": [header.get_text(strip=True) for header in soup.find_all('h1')],
            "h2": [header.get_text(strip=True) for header in soup.find_all('h2')],
            "h3": [header.get_text(strip=True) for header in soup.find_all('h3')],
            "p": [para.get_text(strip=True) for para in soup.find_all('p')]
        }
        return json.dumps(content)
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 403:
            return json.dumps({"error": "Access denied. Please check the URL permissions."})
        return json.dumps({"error": f"HTTP error occurred: {str(http_err)}"})
    except requests.RequestException as e:
        return json.dumps({"error": f"Error fetching content: {str(e)}"})
# Function to generate a refined prompt using JSON content
def generate_prompt(user_input, json_content):
    # If content was not found, use a more generic response
    no_content_found_response = (
        "It seems like I couldn't find the specific information you're looking for. "
        "As a knowledgeable support assistant for Wallingford Financial, I can still help you with your query, "
        "or you can visit our contact page for more details."
    )
    
    # Check if the content from the website has the specific information requested by the user
    if "error" in json_content or not json_content:
        return (
            f"User query: {user_input}\n\n"
            f"{no_content_found_response}\n\n"
            "Please respond as a friendly support assistant for Wallingford Financial, offering assistance where possible."
        )
    else:
        # If content is available, include it and ask the assistant to respond based on it
       return (
    f"Here is some content from our website (structured in JSON format):\n{json_content}\n\n"
    f"User query: {user_input}\n\n"
    "Please respond as a friendly, knowledgeable support assistant for Wallingford Financial. "
    "Reference the content above to help with the user's query and keep the response under 250 characters. "
    "Additionally, ask a relevant follow-up question based on the user's input or the overall conversation flow."
)


# Function to interact with ChatGPT
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly and concise assistant. Respond like a human in casual chat, with short sentences, and keep it under 150 characters."},
                {"role": "user", "content": prompt}
            ]
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

    # Fetch dynamic settings and update keyword responses
    settings = fetch_chatbox_settings()
    if "error" in settings:
        return jsonify({"error": settings["error"]}), 500
    update_keyword_responses(settings)

    # Check if the user input matches any predefined keywords
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword.lower() in user_input.lower():
            return jsonify({"response": response})

    # Fetch selected pages if no keyword matched
    selected_pages = get_selected_pages()
    if "error" in selected_pages:
        return jsonify({"error": selected_pages["error"]}), 500

    # Fetch content from selected pages
    content_from_pages = {}
    for page_name, page_url in selected_pages.items():
        json_content = fetch_website_content(page_url)
        content = json.loads(json_content)

        if "error" in content:
            return jsonify({"error": content["error"]}), 500

        content_from_pages[page_name] = content

    # Combine content into JSON string
    combined_content = json.dumps(content_from_pages)

    # Create a refined prompt and get GPT response
    prompt = generate_prompt(user_input, combined_content)
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
