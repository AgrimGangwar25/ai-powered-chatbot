import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash')
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

# NEW: We initialize a persistent chat session to hold the history in memory
chat_session = model.start_chat(history=[])

@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.form.get("message", "")
        uploaded_file = request.files.get("file")

        if not user_message and not uploaded_file:
            return jsonify({"reply": "Error: Please send a message or a file."}), 400

        gemini_prompt = [] 
        if user_message:
            gemini_prompt.append(user_message)
            
        filepath = None

        if uploaded_file:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(filepath)
            
            gemini_file = genai.upload_file(path=filepath)
            gemini_prompt.append(gemini_file)

        # NEW: We send the prompt to our 'chat_session' instead of generating content from scratch
        # This automatically appends the user's message and the AI's response to the history list
        response = chat_session.send_message(gemini_prompt)

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({"reply": response.text})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Sorry, I ran into an issue on the server."}), 500

if __name__ == '__main__':
    app.run(debug=True)