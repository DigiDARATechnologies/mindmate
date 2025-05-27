# Student Mental Health Chatbot

This project is a web-based AI chatbot designed to support students facing emotional and mental health concerns such as loneliness, stress, and guilt. The chatbot offers empathetic, neuroscience-based advice and practical strategies using a locally running LLM through Ollama, and persists conversations using Qdrant vector database.

## 🔧 Features

- Flask-based web server with REST API endpoints.
- Frontend in HTML/CSS with JavaScript for user interaction.
- Chat memory and authentication based on name, email, and phone.
- Uses Qdrant for vector-based storage of user chat histories.
- Integrated with Ollama for local LLM responses (e.g., mistral).
- LangChain-based embeddings (nomic-embed-text).

## 📁 Project Structure

```
.
├── app.py                # Flask app for routing and API endpoints
├── chatbot_logic.py      # Core logic for chat, Qdrant interaction, and embeddings
├── templates      
        index.html    # Frontend interface for users
└── requirements.txt      # Python dependencies
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/DigiDARATechnologies/mindmate.git
cd student-mental-health-chatbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
### 3. Install Docker

Guide for install Docker:

## For Windows 
## Prerequisites 
Windows 10/11 Pro, Enterprise, or Education (with WSL2 enabled)

## Steps
 ##   1.Download Docker Desktop
        Go to: https://www.docker.com/products/docker-desktop/
        Click “Download for Windows”
  ##  2.Install Docker Desktop
        Run the installer
        Enable WSL 2 if prompted
        Restart your computer if required
  ##  3.Verify Installation
        Open PowerShell or CMD:
        ```bash
        docker --version
        ```
   ## 4.After install docker
        Go to Windows search bar type docker and press enter.
        After press enter docker application is open.
        Next go for powershell to search in windows search bar
        After open the powershell follow the step 4:start qdrant step

### 4. Start Qdrant

Make sure Qdrant is running locally on port `6333`. You can use Docker:

```bash
docker pull qdrant/qdrant
docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
docker ps
```
### 5. Install ollama 
    - step 1: link
    ```bash
        https://ollama.com/download/windows.click
```
    - step 2: Verify Installation
        Open a terminal or command prompt.
        Run
```bash
        ollama --version
        ```
        to confirm Ollama is installed correctly. 
    - step 3: In your terminal, run
    ```bash
        ollama pull nomic-embed-text
        ollama list
        ```
    - step 4: Download llama3.2-vision:11b
        In your terminal, run:
        ```bash
        ollama pull llama3.2-vision:11b
        ollama list
        ```
        [OR]
    - step 5: Download mistral:latest("low system configuration")
        ```bash
        ollama pull mistral:latest
        ```
    

### 5. Run the app

```bash
python app.py
```

Visit `http://localhost:5000` in your browser to start chatting.

## 🧠 Model Notes

- Embeddings: `nomic-embed-text`
- Chat Model: Expected to run locally with Ollama (e.g., `mistral:latest`)
- You can adjust model configurations in `chatbot_logic.py`.

## 🛡️ Safety and Scope

- Only provides responses for students with emotional issues.
- Doesn't offer clinical or medical advice.
- Returns a warning for non-student or unrelated inputs.

## 📜 License

MIT License
