from flask import Flask, request, jsonify, render_template
from chatbot_logic import check_user, store_user_data, chat_with_model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')

    if not all([name, email, phone]):
        return jsonify({'error': 'Missing required fields'}), 400

    user_name, last_session = check_user(email, phone)
    is_new_user = user_name is None

    if is_new_user:
        return jsonify({
            'message': f"Nice to meet you, {name}!",
            'is_new_user': True,
            'last_session': None
        })
    else:
        response = chat_with_model("Ask a question related to the last session", last_session)
        # Clear old chat after asking the last session question
        store_user_data(name, email, phone, "")
        return jsonify({
            'message': f"Welcome back, {name}!",
            'is_new_user': False,
            'last_session_question': response,
            'last_session': last_session
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    chat_history = data.get('chat_history', '')

    if not all([user_input, name, email, phone]):
        return jsonify({'error': 'Missing required fields'}), 400

    response = chat_with_model(user_input)
    chat_history += f"User: {user_input}\nPsychiatrist: {response}\n"

    # Store chat history
    store_user_data(name, email, phone, chat_history)

    return jsonify({
        'response': response,
        'chat_history': chat_history
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# url="https://72eade17-727f-4f58-91ad-d9c79196a229.europe-west3-0.gcp.cloud.qdrant.io:6333",  # Replace with your Qdrant Cloud cluster URL
# api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.3Oi2ODDSMy4rrawMSC2j-83R64oCLyl64G75Xx1LSJc",  # Replace with your Qdrant Cloud API key
