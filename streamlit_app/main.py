import streamlit as st
import jwt
import httpx
import os
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, Callable, Any
from auth_ui import show_login_ui
from pathlib import Path
import base64
import requests

# Function to get base64 encoded image for favicon
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Path to logo
logo_path = os.path.join("streamlit_app", "assets", "ac_logo.jpg")

# Set page config first - use the logo as favicon
try:
    favicon = get_base64_encoded_image(logo_path)
    st.set_page_config(
        page_title="Amaravathi One Admin",
        page_icon=f"data:image/jpeg;base64,{favicon}",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": None,
            "Report a bug": None,
            "About": None
        }
    )
except Exception as e:
    # Fallback if logo can't be loaded
    st.set_page_config(
        page_title="Amaravathi One Admin",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": None,
            "Report a bug": None,
            "About": None
        }
    )

# Custom CSS to hide the deploy button and other unwanted UI elements
st.markdown("""
<style>
    /* Hide deploy and other top-right buttons */
    .stDeployButton, header button[kind="secondary"] {
        display: none !important;
    }
    
    /* Hide hamburger menu and footer */
    #MainMenu, footer {
        visibility: hidden;
    }
    
    /* Hide the "made with streamlit" message */
    .viewerBadge_container__r5tak {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Import local modules after page config
from api_utils import refresh_access_token, is_token_expired, api_request
import auth_ui
import dashboard_ui
import catalog_ui
import users_ui

# Get configuration from environment variables
API_URL = os.getenv("API_URL", "http://localhost:8000")
JWT_SECRET = os.getenv("JWT_SECRET", "your-default-secret-key")

def apply_custom_styles():
    """Apply custom styling to UI elements"""
    with open('streamlit_app/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def verify_token(token: str) -> Optional[Dict]:
    """
    Extract JWT token payload without verifying signature.
    """
    try:
        # Decode without verification
        payload = jwt.decode(
            token, 
            options={"verify_signature": False},
            algorithms=["HS256"]
        )
        
        # Check if user is admin
        if payload.get("role") != "admin":
            return None
        
        return payload
    except Exception:
        return None

def login_with_credentials(email_or_phone: str, password: str) -> Dict:
    """
    Login using email/phone and password through the API.
    
    Returns:
        Dict containing tokens and status
    """
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{API_URL}/auth/login-admin",
                data={
                    "email_or_phone": email_or_phone,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": response.json().get("detail", "Login failed")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to API: {str(e)}"
        }

def check_token_expiration():
    """Check and refresh token if needed"""
    if "token" in st.session_state and "refresh_token" in st.session_state:
        try:
            # Decode token to check expiration
            payload = jwt.decode(
                st.session_state.token, 
                options={"verify_signature": False},
                algorithms=["HS256"]
            )
            
            # Check if token is close to expiration (within 5 minutes)
            if "exp" in payload:
                exp_time = datetime.fromtimestamp(payload["exp"])
                remaining = (exp_time - datetime.utcnow()).total_seconds() / 60
                
                # If token will expire soon, refresh it
                if remaining < 5:
                    result = refresh_access_token(st.session_state.refresh_token, API_URL)
                    if result["success"]:
                        st.session_state.token = result["data"]["access_token"]
                        if "refresh_token" in result["data"]:
                            st.session_state.refresh_token = result["data"]["refresh_token"]
                        st.toast("Session refreshed", icon="🔄")
        except Exception:
            pass

def verify_authentication():
    """Verify if user is authenticated"""
    return "authenticated" in st.session_state and st.session_state.authenticated and "token" in st.session_state

def verify_session():
    """
    Verify if the current session is valid and user is authenticated.
    Handles expired tokens, missing tokens, and unauthorized access.
    
    Returns:
        bool: True if session is valid, False otherwise
    """
    # Check if user is authenticated
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        # No auth at all - redirect to login
        return False
    
    # Check if token exists
    if "token" not in st.session_state:
        st.warning("Your session is missing authentication data. Please login again.")
        logout()
        return False
    
    # Check if token is expired
    try:
        # Decode without verification
        payload = jwt.decode(
            st.session_state.token, 
            options={"verify_signature": False},
            algorithms=["HS256"]
        )
        
        # Check expiration
        if "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"])
            if datetime.utcnow() > exp_time:
                st.warning("Your session has expired. Please login again.")
                logout()
                return False
        
        # Store the decoded payload in session state for easy access
        st.session_state.user_data = payload
        
        # Return True for valid session
        return True
        
    except Exception as e:
        st.error(f"Error verifying your session: {str(e)}")
        logout()
        return False

def check_permission(required_role: str = "admin"):
    """
    Check if the user has the required role.
    
    Args:
        required_role: Minimum role required to access a page
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not verify_session():
        return False
    
    user_role = st.session_state.user.get("role", "")
    
    # Check if user has required role
    if required_role == "admin" and user_role != "admin":
        st.error("Access Denied: You don't have permission to view this page.")
        st.info("This page is only accessible to administrators.")
        return False
    
    # Check if required role is back_office and user is either admin or back_office
    if required_role == "back_office" and user_role not in ["admin", "back_office"]:
        st.error("Access Denied: You don't have permission to view this page.")
        st.info("This page is only accessible to back office staff and administrators.")
        return False
    
    return True

def logout():
    """Clear session state and logout the user."""
    # Store a temporary flag for login page
    show_logout_message = "authenticated" in st.session_state
    
    # Clear all session state
    st.session_state.clear()
    
    # Set a flag to show logout message
    if show_logout_message:
        st.session_state.show_logout_message = True
    
    # Rerun the app to show login page
    st.experimental_rerun()

def sidebar_navigation():
    """Create sidebar navigation menu with styled tabs similar to login page."""
    # Display the company logo at the top of sidebar
    try:
        from PIL import Image
        logo = Image.open("streamlit_app/assets/ac_logo.jpg")
        st.sidebar.image(logo, width=150)
    except Exception:
        pass
    
    st.sidebar.title("Amaravathi One")
    st.sidebar.markdown("---")
    
    # Navigation options with icons
    options = [
        ("dashboard", "🏠 Dashboard"),
        ("categories", "📊 Categories"),
        ("subcategories", "🔖 Subcategories"),
        ("products", "🏗️ Products"),
    ]
    
    # Only show Users option for admin role
    if st.session_state.get("role") == "admin":
        options.append(("users", "👥 Users"))
    
    # Get the current page from session state
    current_page = st.session_state.get("current_page", "dashboard")
    
    # Apply custom CSS for styling
    st.sidebar.markdown("""
    <style>
    /* Navigation section title */
    .nav-section-title {
        font-weight: 600;
        margin-bottom: 10px;
        color: #333;
    }
    
    /* Make buttons look like tabs */
    .stButton button {
        width: 100%;
        text-align: left !important;
        background-color: transparent !important;
        border: none !important;
        padding: 10px 16px !important;
        border-radius: 4px !important;
        margin-bottom: 2px !important;
        color: #333 !important;
        font-weight: normal !important;
    }
    
    /* Active button styling */
    .active-nav-button {
        color: #F5A623 !important;
        font-weight: 600 !important;
        background-color: rgba(245, 166, 35, 0.1) !important;
        border-left: 3px solid #F5A623 !important;
    }
    
    /* Hide standard radio button styling */
    .stRadio > div {
        flex-direction: column !important;
    }
    
    .stRadio label {
        padding: 10px !important;
        cursor: pointer !important;
        border-radius: 4px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s !important;
    }
    
    .stRadio label:hover {
        background-color: #f5f5f5 !important;
    }
    
    .stRadio label[data-baseweb="radio"] input:checked ~ div {
        background-color: rgba(245, 166, 35, 0.1) !important;
        border-left: 3px solid #F5A623 !important;
        color: #F5A623 !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div class='nav-section-title'>Navigation</div>", unsafe_allow_html=True)
    
    # Use a hidden radio to track selection
    selected = st.sidebar.radio(
        "Navigation",
        options=[label for _, label in options],
        index=[i for i, (key, _) in enumerate(options) if key == current_page][0],
        label_visibility="collapsed"
    )
    
    # Map back to the key
    for key, label in options:
        if label == selected:
            if current_page != key:
                st.session_state.current_page = key
                st.rerun()
            break
    
    # Logout button at the bottom
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", type="primary", use_container_width=True):
        # Clear session state to log out
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.sidebar.caption("© Amaravathi One v1.0")

def display_footer():
    """Display a consistent footer across all pages"""
    st.markdown("---")
    
    # Footer container with styling
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f8f9fa;
        padding: 10px 20px;
        text-align: center;
        border-top: 1px solid #e9ecef;
        color: #6c757d;
        font-size: 14px;
        z-index: 1000;
    ">
        © 2025 Amaravathi One. All rights reserved.
    </div>
    """, unsafe_allow_html=True)

def request_password_reset(identifier):
    """Send password reset request to API."""
    try:
        # Determine if the identifier is an email or phone
        payload = {}
        if "@" in identifier:
            payload["email"] = identifier
        else:
            # Format phone number by removing any non-digit characters
            clean_phone = ''.join(filter(str.isdigit, identifier))
            payload["phone"] = clean_phone
            
        # Make API request
        response = requests.post(
            f"{API_URL}/auth/request-password-reset",
            json=payload
        )
        
        if response.status_code == 200:
            return True, "Password reset link sent successfully"
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, f"Password reset request failed: {error_detail}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main application entry point"""
    # Apply styling
    apply_custom_styles()
    
    # 1. Handle authentication
    if not verify_authentication():
        show_login_ui(API_URL)
        display_footer()  # Show footer on login page too
        return
    
    # Auto-refresh token if needed
    check_token_expiration()
    
    # 2. Show sidebar with navigation
    sidebar_navigation()
    
    # 3. Load the appropriate section based on navigation
    current_page = st.session_state.get("current_page", "dashboard")
    
    try:
        if current_page == "dashboard":
            dashboard_ui.show_dashboard(st.session_state.user, API_URL, st.session_state.token)
            
        elif current_page == "categories":
            # Only show one header instead of two
            st.title("Product Catalog Management")
            catalog_ui.manage_categories(st.session_state.token, API_URL)
            
        elif current_page == "subcategories":
            # Only show one title without additional header
            st.title("Product Catalog Management")
            # Let the function handle its own header
            catalog_ui.manage_subcategories(st.session_state.token, API_URL)
            
        elif current_page == "products":
            # Only show one title without redundant header
            st.title("Product Catalog Management")
            # Remove the redundant header here
            catalog_ui.manage_products(st.session_state.token, API_URL)
            
        elif current_page == "users":
            # Check if user has admin role
            if st.session_state.user.get("role") == "admin":
                users_ui.show_users_ui(st.session_state.token, API_URL)
            else:
                st.error("Access denied. You don't have permission to view this page.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.button("Return to Dashboard", on_click=lambda: setattr(st.session_state, "current_page", "dashboard"))
    
    # Add the footer to the end
    display_footer()

if __name__ == "__main__":
    main() 