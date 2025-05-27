from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://72eade17-727f-4f58-91ad-d9c79196a229.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.3Oi2ODDSMy4rrawMSC2j-83R64oCLyl64G75Xx1LSJc",
)
qdrant_client.delete_collection(collection_name="user_chats")


#a5175a1a-8825-4ba9-9701-0ac53dab1bcc|fPfDa_z8YdEL-L5eaHExogl6QZNgtMX-3njFbBSNISZ8lBQN-pa8Qg
#eyJhbGciOiJIUzI1NiJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzU1NzU0NDQzfQ.JZ3v94xiVCYp-L1lvfzQiC5jVXHKkKx1ipT3Yx1oIzY - jwt