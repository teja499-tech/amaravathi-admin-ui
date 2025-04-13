#!/bin/bash
# Startup script for Amaravathi One Streamlit App

# Set environment variables
export API_URL="http://localhost:8000"
export JWT_SECRET="your-actual-backend-jwt-secret"  # MUST MATCH the backend's JWT_SECRET

# Activate virtual environment if needed
# source .venv/bin/activate

# Run the Streamlit app
exec streamlit run streamlit_app/main.py