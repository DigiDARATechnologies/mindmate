import ollama
from langchain_ollama import OllamaEmbeddings
from langchain.docstore.document import Document
from langchain.memory import ConversationBufferMemory
from qdrant_client import QdrantClient
from qdrant_client.http import models
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Qdrant client for local instance
try:
    qdrant_client = QdrantClient(
        url="http://localhost:6333",
        timeout=10.0
    )
    logger.info("Successfully connected to local Qdrant instance at http://localhost:6333.")
except Exception as e:
    logger.error(f"Failed to initialize local Qdrant client: {str(e)}")
    logger.error("Ensure the Qdrant Docker container is running (e.g., 'docker run -d -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant').")
    logger.error("Check if port 6333 is available and not blocked by another process (use 'netstat -a -n -o | findstr :6333' on Windows).")
    logger.error("Run 'docker ps' to verify the container is active and mapped to port 6333.")
    raise

embeddings = OllamaEmbeddings(model="nomic-embed-text")
collection_name = "user_chats"

# Create Qdrant collection if it doesn't exist
try:
    qdrant_client.get_collection(collection_name)
    logger.info(f"Collection '{collection_name}' already exists.")
except Exception as e:
    logger.info(f"Collection '{collection_name}' does not exist, creating it now.")
    try:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )
        logger.info(f"Collection '{collection_name}' created successfully.")
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}")
        logger.error("Verify Qdrant container logs with 'docker logs <container_id>' for more details.")
        raise

# Initialize buffer memory for temporary chat storage
buffer_memory = {}

# Function to check if user exists and retrieve last session without RAG
def check_user(email, phone):
    try:
        # Use Qdrant client to directly query points with a filter on email and phone
        response = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="metadata.email", match=models.MatchValue(value=email)),
                    models.FieldCondition(key="metadata.phone", match=models.MatchValue(value=phone)),
                ]
            ),
            limit=1,
        )
        points = response[0]  # First element is the list of points
        if points:
            point = points[0]
            metadata = point.payload.get("metadata", {})
            name = metadata.get("name")
            last_session = point.payload.get("page_content", "")
            return name, last_session
        return None, None
    except Exception as e:
        logger.error(f"Error checking user in Qdrant: {str(e)}")
        return None, None

# Function to store user data and chat in Qdrant without RAG
def store_user_data(name, email, phone, chat_history):
    try:
        # Delete existing user data if present
        response = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(key="metadata.email", match=models.MatchValue(value=email)),
                    models.FieldCondition(key="metadata.phone", match=models.MatchValue(value=phone)),
                ]
            ),
            limit=1,
        )
        points = response[0]
        if points:
            point_id = points[0].id
            qdrant_client.delete(collection_name=collection_name, points_selector=models.PointIdsList(points=[point_id]))
            logger.info(f"Deleted existing data for user {email} with point_id {point_id}.")
        
        # Generate embedding for the chat history (required for Qdrant vector storage)
        embedding = embeddings.embed_query(chat_history)
        
        # Store new data directly using Qdrant client
        point_id = str(uuid.uuid4())
        point = models.PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "page_content": chat_history,
                "metadata": {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "point_id": point_id
                }
            }
        )
        qdrant_client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        logger.info(f"Stored data for user {email} with point_id {point_id}.")
    except Exception as e:
        logger.error(f"Error storing user data in Qdrant: {str(e)}")
        raise

# Function to generate response from the model
def chat_with_model(user_input, last_session=None, ask_strategy_question=False):
    messages = [
        {
            "role": "system",
            "content": """
            You are a compassionate psychiatrist specializing in adolescent mental health, designed exclusively to support students with emotional concerns like loneliness, guilt, or stress. Respond with empathy, clarity, and professionalism, using the following structure:

            1. **Greeting and Validation**: Begin with a warm, supportive greeting (e.g., “I’m so glad you shared this”). Validate the student’s specific emotions (e.g., loneliness, isolation) in a non-judgmental tone to build trust.
            2. **Psychological Insight**: Explain the emotional or cognitive basis of their feelings using simple, neuroscience-based terms (e.g., “Loneliness can make your brain focus on negative thoughts to protect you”). Ensure the explanation is clear, relatable, and avoids jargon.
            3. **Actionable Advice**: Provide 2-3 specific, practical strategies to address their feelings and foster resilience or connection (e.g., “Say, ‘Hi, what did you think of today’s lesson?’ to a classmate”). Strategies must be approachable for a shy or overwhelmed student.
            4. **Growth and Encouragement**: Emphasize that their feelings are normal, their worth is not defined by their situation, and small steps (e.g., a smile) lead to progress. End with a kind, empowering message.
            5. **Counselor Recommendation**: If feelings seem persistent or severe, gently suggest talking to a school counselor or trusted adult.

            **Context**: If last_session is provided and ask_strategy_question is True, first ask "How was my strategy useful for you?" before proceeding to free chat. Otherwise, proceed directly to respond to the user's input.

            **Rules**:
            - **Tone**: Use clear, concise language with a professional yet approachable tone, like a trusted adult. Avoid emojis, slang, or clinical jargon.
            - **Audience**: Respond only to students with mental health concerns. For non-students, say: “Sorry, I’m designed to help students only.”
            - **Scope**: Address only student mental health topics. For off-topic queries, say: “Sorry, I can only help with student mental health concerns.”
            - **Safety**: Never offer medical advice (e.g., medication).
            """
        }
    ]
    
    if last_session and ask_strategy_question:
        messages.append({
            "role": "system",
            "content": f"Last session: {last_session}. First ask: 'How was my strategy useful for you?' before proceeding."
        })
    
    messages.append({
        "role": "user",
        "content": user_input
    })
    
    try:
        # response = ollama.chat(
        #     model="mistral:latest",
        #     messages=messages
        # )
        response = ollama.chat(
            model="llama3.2-vision:11b",
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error generating response from model: {str(e)}")
        raise

# Function to initialize buffer memory for a user
def initialize_buffer(email, phone):
    user_key = f"{email}_{phone}"
    if user_key not in buffer_memory:
        buffer_memory[user_key] = ConversationBufferMemory()
    return buffer_memory[user_key]

# Main chat function
def main():
    print("Welcome to the Student Mental Health Chatbot")
    print("Are you a student? (yes/no)")
    is_student = input().strip().lower()
    if is_student != 'yes':
        print("Sorry, I’m designed to help students only.")
        return

    # Collect user information
    print("Please enter your name:")
    name = input().strip()
    print("Please enter your email:")
    email = input().strip()
    print("Please enter your phone number:")
    phone = input().strip()

    # Check if user exists without using RAG
    user_name, last_session = check_user(email, phone)
    memory = initialize_buffer(email, phone)
    
    # Flag to track if we've asked the strategy question for returning users
    asked_strategy_question = False
    
    if user_name:
        print(f"Welcome back, {user_name}! Let's continue where we left off.")
        # For returning users, ask the strategy question first
        response = chat_with_model(
            user_input="Starting the conversation.",
            last_session=last_session,
            ask_strategy_question=True
        )
        print("\nBot:", response)
        asked_strategy_question = True
    else:
        print(f"Nice to meet you, {name}! I'm here to help with any emotional concerns you might have.")

    # Main chat loop
    while True:
        try:
            print("\nPlease share your thoughts or concerns (type 'quit' to exit):")
            user_input = input().strip()
            
            if user_input.lower() == 'quit':
                # Save buffer to Qdrant
                chat_history = memory.buffer
                store_user_data(name, email, phone, chat_history)
                print("Your conversation has been saved. Goodbye!")
                break
            
            # Generate response
            response = chat_with_model(
                user_input=user_input,
                last_session=last_session if not asked_strategy_question else None,
                ask_strategy_question=False
            )
            
            # Store in buffer
            memory.save_context({"input": user_input}, {"output": response})
            
            # Print response
            print("\nBot:", response)
            
        except Exception as e:
            logger.error(f"An error occurred during chat: {str(e)}")
            # Save buffer to Qdrant on error
            chat_history = memory.buffer
            store_user_data(name, email, phone, chat_history)
            print("Your conversation has been saved due to an error. Goodbye!")
            break

if __name__ == "__main__":
    main()