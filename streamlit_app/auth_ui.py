import streamlit as st
import httpx
import jwt
import re
from typing import Dict, Optional, Tuple
import time
from PIL import Image
import base64
from pathlib import Path
import os

def is_phone_number(input_text: str) -> bool:
    """Check if input is likely a phone number."""
    # Remove spaces and common separators
    clean_input = re.sub(r'[\s\-\(\)\.]', '', input_text)
    # Check if it's numeric and has reasonable phone number length
    return clean_input.isdigit() and 8 <= len(clean_input) <= 15

def login_admin(email_or_phone: str, password: str, api_url: str) -> Dict:
    """Login using email/phone and password through the API."""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{api_url}/auth/login-admin",
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

def request_otp(email_or_phone: str, api_url: str) -> Dict:
    """Request OTP from API."""
    try:
        with httpx.Client() as client:
            data = {}
            # Determine if input is email or phone
            if "@" in email_or_phone:
                data["email"] = email_or_phone
            else:
                data["phone"] = email_or_phone
                
            response = client.post(
                f"{api_url}/auth/request-otp",
                json=data
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "OTP sent successfully"
                }
            else:
                return {
                    "success": False,
                    "message": response.json().get("detail", "Failed to send OTP")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to API: {str(e)}"
        }

def verify_otp(email_or_phone: str, otp: str, api_url: str) -> Dict:
    """Verify OTP with API and check if the user has admin privileges."""
    try:
        with httpx.Client() as client:
            data = {"otp": otp}
            if "@" in email_or_phone:
                data["email"] = email_or_phone
            else:
                data["phone"] = email_or_phone
                
            response = client.post(
                f"{api_url}/auth/verify-otp",
                json=data
            )
            
            if response.status_code == 200:
                # Successfully verified OTP, now check the user's role
                response_data = response.json()
                
                # Decode the token to get the user's role
                token_data = verify_token(response_data.get("access_token", ""))
                
                if token_data and token_data.get("role") in ["admin", "back_office"]:
                    return {
                        "success": True,
                        "data": response_data
                    }
                else:
                    return {
                        "success": False,
                        "message": "Access denied: Insufficient privileges to access admin panel"
                    }
            else:
                return {
                    "success": False,
                    "message": response.json().get("detail", "Invalid OTP")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to API: {str(e)}"
        }

def request_password_reset(email_or_phone: str, api_url: str) -> Dict:
    """Request password reset from API."""
    try:
        with httpx.Client() as client:
            # Send as email_or_phone parameter to match backend expectation
            payload = {"email_or_phone": email_or_phone}
            
            response = client.post(
                f"{api_url}/auth/request-password-reset",
                json=payload
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Password reset OTP sent successfully"
                }
            else:
                return {
                    "success": False,
                    "message": response.json().get("detail", "Failed to send reset OTP")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to API: {str(e)}"
        }

def reset_password(email_or_phone: str, otp: str, new_password: str, api_url: str) -> Dict:
    """Reset password with API."""
    try:
        with httpx.Client() as client:
            # Use the correct payload format - send email_or_phone as a single parameter
            data = {
                "email_or_phone": email_or_phone,
                "otp": otp,
                "new_password": new_password
            }
            
            # Debug output
            print(f"Reset password payload: {data}")
            
            response = client.post(
                f"{api_url}/auth/reset-password",
                json=data
            )
            
            # Debug response
            print(f"Response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Password reset successfully"
                }
            else:
                return {
                    "success": False,
                    "message": response.json().get("detail", "Failed to reset password")
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error connecting to API: {str(e)}"
        }

def verify_token(token: str) -> Optional[Dict]:
    """Extract JWT token payload without verifying signature."""
    try:
        # Decode without verification
        payload = jwt.decode(
            token, 
            options={"verify_signature": False},
            algorithms=["HS256"]
        )
        
        return payload
    except Exception:
        return None

def set_user_session(token: str, refresh_token: str):
    """Set user session data from token."""
    # Save tokens in session state
    st.session_state.token = token
    st.session_state.refresh_token = refresh_token
    
    # Extract user info from token
    user_data = verify_token(token)
    
    if user_data:
        st.session_state.authenticated = True
        st.session_state.user = user_data
        
        # Extract additional user details if available
        if "first_name" in user_data and "last_name" in user_data:
            st.session_state.user_name = f"{user_data['first_name']} {user_data['last_name']}"
        
        # Set role explicitly for easier access
        if "role" in user_data:
            st.session_state.role = user_data["role"]

def display_logo():
    """Display the company logo."""
    try:
        import os
        from PIL import Image
        
        # Try multiple possible paths to find the logo
        possible_paths = [
            "streamlit_app/assets/ac_logo.jpg",  # Relative from run directory
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ac_logo.jpg"),  # From current file
            os.path.abspath("assets/ac_logo.jpg"),  # From absolute path
            "../assets/ac_logo.jpg",  # One directory up
            "./assets/ac_logo.jpg",  # Current directory
        ]
        
        logo_path = None
        for path in possible_paths:
            if os.path.exists(path):
                logo_path = path
                break
        
        if logo_path:
            logo = Image.open(logo_path)
            # Add CSS for centering within the container
            st.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
            st.image(logo, width=140)
            st.markdown('</div>', unsafe_allow_html=True)
            return True
        else:
            # If we can't find the logo, just show the text version
            st.warning("Logo image not found. Please check the path.")
            return False
    except Exception as e:
        st.error(f"Error displaying logo: {str(e)}")
        return False

def show_login_ui(api_url: str):
    """Display login UI with professional styling matching the reference image."""
    
    # Check if already logged in - redirect to dashboard
    if "authenticated" in st.session_state and st.session_state.authenticated:
        st.experimental_rerun()
        return
    
    # Initialize session state variables for password reset
    if "reset_otp_input" not in st.session_state:
        st.session_state.reset_otp_input = ""
    
    if "reset_identifier" not in st.session_state:
        st.session_state.reset_identifier = ""
        
    if "reset_email_phone" not in st.session_state:
        st.session_state.reset_email_phone = ""
        
    if "reset_otp_sent" not in st.session_state:
        st.session_state.reset_otp_sent = False
        
    if "reset_otp_verified" not in st.session_state:
        st.session_state.reset_otp_verified = False
        
    if "new_password" not in st.session_state:
        st.session_state.new_password = ""
        
    if "confirm_password" not in st.session_state:
        st.session_state.confirm_password = ""
    
    # Apply custom login styles with yellow theme
    st.markdown("""
        <style>
        /* Remove default padding */
        .block-container {
            padding-top: 1rem;  /* Reduced from 2rem */
            max-width: 1000px;
            margin: 0 auto;
        }
        
        /* Logo container - reduce spacing */
        .logo-container {
            text-align: center;
            margin-bottom: 0.5rem;  /* Very small margin */
        }
        
        /* App header styling - minimal margin */
        .app-header {
            font-size: 1.5rem;
            font-weight: 600;
            text-align: center;
            margin-top: 0;
            margin-bottom: 0.5rem;  /* Minimal space below header */
            color: #333;
        }
        
        /* Tabs container - less space */
        .tabs-container {
            margin-top: 0.5rem; /* Minimal space above tabs */
        }
        
        /* Form container */
        .form-container {
            width: 100%;
            background-color: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        /* Footer styling */
        .footer-container {
            margin-top: 3rem;  /* More space above footer */
            text-align: center;
            color: #666;
            padding: 1.5rem;
            position: relative;
            bottom: 0;
            width: 100%;
        }
        
        /* Hide default footer */
        footer {
            visibility: hidden !important;
        }
        
        /* Hide streamlit branding */
        #MainMenu, header {
            visibility: hidden;
        }
        
        /* Form field styling */
        .form-field {
            margin-bottom: 1.2rem;
        }
        
        .field-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #333;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #F5A623 !important;
            color: white !important;
            border: none !important;
            padding: 0.7rem 1rem !important;
            font-weight: 500 !important;
            height: auto !important;
            width: 100% !important;
        }
        
        /* Fix the checkbox */
        .stCheckbox {
            margin-bottom: 1.2rem;
        }
        
        /* Tab styling */
        div[data-testid="stHorizontalBlock"] > div button {
            border-radius: 0 !important;
            border-bottom: none !important;
            margin: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Display logo and heading with less space between them
    st.markdown('<h1 class="app-header">Amaravathi One Admin Panel</h1>', unsafe_allow_html=True)
    
    # Create container for the form
    form_container = st.container()
    
    with form_container:
        # Custom tab implementation to match the design
        col1, col2, col3 = st.columns([1, 1, 1])
        
        # Get current active tab
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = "login"
            
        # Tab click handlers
        with col1:
            login_btn = st.button("Admin Login", key="tab_login", use_container_width=True)
            if login_btn:
                st.session_state.active_tab = "login"
                
        with col2:
            otp_btn = st.button("OTP Login", key="tab_otp", use_container_width=True)
            if otp_btn:
                st.session_state.active_tab = "otp"
                
        with col3:
            forgot_btn = st.button("Forgot Password", key="tab_forgot", use_container_width=True)
            if forgot_btn:
                st.session_state.active_tab = "forgot"
        
        # Style active tab indicator
        active_tab = st.session_state.active_tab
        st.markdown(f"""
        <style>
        [data-testid="stHorizontalBlock"] > div:nth-child(1) button {{
            background-color: {'white !important' if active_tab == 'login' else '#f0f2f6 !important'};
            color: {'#F5A623 !important' if active_tab == 'login' else '#666 !important'};
            font-weight: {'600 !important' if active_tab == 'login' else '400 !important'};
            border-bottom: {f'3px solid #F5A623 !important' if active_tab == 'login' else 'none !important'};
            border-radius: 4px 4px 0 0 !important;
        }}
        [data-testid="stHorizontalBlock"] > div:nth-child(2) button {{
            background-color: {'white !important' if active_tab == 'otp' else '#f0f2f6 !important'};
            color: {'#F5A623 !important' if active_tab == 'otp' else '#666 !important'};
            font-weight: {'600 !important' if active_tab == 'otp' else '400 !important'};
            border-bottom: {f'3px solid #F5A623 !important' if active_tab == 'otp' else 'none !important'};
            border-radius: 4px 4px 0 0 !important;
        }}
        [data-testid="stHorizontalBlock"] > div:nth-child(3) button {{
            background-color: {'white !important' if active_tab == 'forgot' else '#f0f2f6 !important'};
            color: {'#F5A623 !important' if active_tab == 'forgot' else '#666 !important'};
            font-weight: {'600 !important' if active_tab == 'forgot' else '400 !important'};
            border-bottom: {f'3px solid #F5A623 !important' if active_tab == 'forgot' else 'none !important'};
            border-radius: 4px 4px 0 0 !important;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Display horizontal divider
        st.markdown('<hr style="margin: 0; padding: 0; height: 1px; background-color: #ddd; border: none;">', unsafe_allow_html=True)
        
        # Form container
        main_form = st.container()
        
        with main_form:
            if active_tab == "login":
                # Admin Login Tab
                with st.form("login_form", clear_on_submit=False):
                    st.markdown('<div class="field-label">Email or Phone</div>', unsafe_allow_html=True)
                    email_or_phone = st.text_input("Email or Phone", 
                                            placeholder="Enter your email or phone", 
                                            key="email_phone_login",
                                            label_visibility="hidden")
                    
                    st.markdown('<div class="field-label">Password</div>', unsafe_allow_html=True)
                    password = st.text_input("Password", 
                                     type="password", 
                                     placeholder="Enter your password", 
                                     key="password_login",
                                     label_visibility="hidden")
                    
                    # Remember me checkbox
                    remember = st.checkbox("Remember me for 7 days", key="remember_login")
                    
                    # Login button
                    submit = st.form_submit_button("Login", use_container_width=True)
                    
                    if submit:
                        if email_or_phone and password:
                            with st.spinner("Logging in..."):
                                # Try logging in with credentials
                                response = login_admin(email_or_phone, password, api_url)
                                
                                if response["success"]:
                                    data = response["data"]
                                    # Store token and user info in session state
                                    set_user_session(data["access_token"], data["refresh_token"])
                                    st.success("Login successful!")
                                    time.sleep(1)
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Login failed: {response['message']}")
                        else:
                            st.error("Please enter your email/phone and password")
            
            elif active_tab == "otp":
                # OTP Login Tab
                if "otp_sent" not in st.session_state:
                    st.session_state.otp_sent = False
                
                with st.form("otp_form", clear_on_submit=False):
                    st.markdown('<div class="field-label">Email or Phone</div>', unsafe_allow_html=True)
                    email_or_phone = st.text_input("Email or Phone", 
                                            placeholder="Enter your email or phone", 
                                            key="email_phone_otp",
                                            label_visibility="hidden")
                    
                    if st.session_state.otp_sent:
                        st.markdown('<div class="field-label">OTP</div>', unsafe_allow_html=True)
                        otp = st.text_input("OTP", 
                                    placeholder="Enter OTP sent to your email/phone", 
                                    key="otp_input",
                                    label_visibility="hidden")
                        
                        submit_btn_text = "Verify OTP"
                    else:
                        submit_btn_text = "Request OTP"
                    
                    # Submit button - either "Request OTP" or "Verify OTP"
                    submit = st.form_submit_button(submit_btn_text, use_container_width=True)
                    
                    if submit:
                        if not email_or_phone:
                            st.error("Please enter your email or phone number")
                        elif not st.session_state.otp_sent:
                            # Request OTP
                            with st.spinner("Sending OTP..."):
                                response = request_otp(email_or_phone, api_url)
                                if response["success"]:
                                    st.session_state.otp_sent = True
                                    st.session_state.otp_email_phone = email_or_phone
                                    st.success("OTP sent successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Failed to send OTP: {response['message']}")
                        else:
                            # Verify OTP
                            if not 'otp_input' in st.session_state or not st.session_state.otp_input:
                                st.error("Please enter the OTP")
                            else:
                                with st.spinner("Verifying OTP..."):
                                    response = verify_otp(email_or_phone, st.session_state.otp_input, api_url)
                                    if response["success"]:
                                        data = response["data"]
                                        # Store token and user info in session state
                                        set_user_session(data["access_token"], data["refresh_token"])
                                        st.success("OTP verification successful!")
                                        # Reset OTP state
                                        st.session_state.otp_sent = False
                                        if "otp_input" in st.session_state:
                                            del st.session_state.otp_input
                                        if "otp_email_phone" in st.session_state:
                                            del st.session_state.otp_email_phone
                                        time.sleep(1)
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"OTP verification failed: {response['message']}")
                
                # Option to go back or resend OTP
                if st.session_state.otp_sent:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Resend OTP", key="resend_otp"):
                            with st.spinner("Resending OTP..."):
                                response = request_otp(st.session_state.otp_email_phone, api_url)
                                if response["success"]:
                                    st.success("OTP resent successfully!")
                                else:
                                    st.error(f"Failed to resend OTP: {response['message']}")
                    with col2:
                        if st.button("Back", key="back_from_otp"):
                            st.session_state.otp_sent = False
                            if "otp_input" in st.session_state:
                                del st.session_state.otp_input
                            if "otp_email_phone" in st.session_state:
                                del st.session_state.otp_email_phone
                            st.experimental_rerun()
            
            elif active_tab == "forgot":
                # Forgot Password Tab
                if "reset_otp_sent" not in st.session_state:
                    st.session_state.reset_otp_sent = False
                
                if "reset_otp_verified" not in st.session_state:
                    st.session_state.reset_otp_verified = False
                
                with st.form("forgot_form", clear_on_submit=False):
                    if not st.session_state.reset_otp_sent:
                        # Step 1: Request password reset
                        st.markdown('<div class="field-label">Email or Phone</div>', unsafe_allow_html=True)
                        email_or_phone = st.text_input("Email or Phone", 
                                                placeholder="Enter your email or phone", 
                                                key="email_phone_reset",
                                                label_visibility="hidden")
                        
                        submit_text = "Request Password Reset"
                    
                    elif not st.session_state.reset_otp_verified:
                        # Step 2: Verify OTP
                        st.markdown('<div class="field-label">OTP</div>', unsafe_allow_html=True)
                        otp = st.text_input("OTP", 
                                    placeholder="Enter OTP sent to your email/phone", 
                                    key="reset_otp_input",
                                    label_visibility="hidden")
                        
                        submit_text = "Verify OTP"
                    
                    else:
                        # Step 3: Set new password
                        st.markdown('<div class="field-label">New Password</div>', unsafe_allow_html=True)
                        new_password = st.text_input("New Password", 
                                              type="password",
                                              placeholder="Enter new password", 
                                              key="new_password",
                                              label_visibility="hidden")
                        
                        st.markdown('<div class="field-label">Confirm Password</div>', unsafe_allow_html=True)
                        confirm_password = st.text_input("Confirm Password", 
                                                 type="password",
                                                 placeholder="Confirm new password", 
                                                 key="confirm_password",
                                                 label_visibility="hidden")
                        
                        submit_text = "Reset Password"
                    
                    # Submit button
                    submit = st.form_submit_button(submit_text, use_container_width=True)
                    
                    if submit:
                        if not st.session_state.reset_otp_sent:
                            # Request password reset
                            if not email_or_phone:
                                st.error("Please enter your email or phone")
                            else:
                                with st.spinner("Requesting password reset..."):
                                    response = request_password_reset(email_or_phone, api_url)
                                    if response["success"]:
                                        st.session_state.reset_otp_sent = True
                                        st.session_state.reset_email_phone = email_or_phone
                                        st.success("Password reset OTP sent successfully!")
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Password reset request failed: {response['message']}")
                        
                        elif not st.session_state.reset_otp_verified:
                            # Verify OTP
                            if not st.session_state.reset_otp_input:
                                st.error("Please enter the OTP")
                            else:
                                with st.spinner("Verifying OTP..."):
                                    # In a real implementation, we would verify the OTP here
                                    # For this demo, we'll just move to the next step
                                    st.session_state.reset_otp_verified = True
                                    st.success("OTP verified successfully!")
                                    st.experimental_rerun()
                        
                        else:
                            # Reset password
                            if not st.session_state.new_password:
                                st.error("Please enter a new password")
                            elif st.session_state.new_password != st.session_state.confirm_password:
                                st.error("Passwords do not match")
                            else:
                                with st.spinner("Resetting password..."):
                                    # Make sure we have the correct identifier stored
                                    email_or_phone = st.session_state.reset_email_phone
                                    otp = st.session_state.reset_otp_input
                                    
                                    print(f"Debug - Reset password parameters:")
                                    print(f"Email/Phone: {email_or_phone}")
                                    print(f"OTP: {otp}")
                                    print(f"New Password: {st.session_state.new_password[:3]}***")
                                    
                                    response = reset_password(
                                        email_or_phone,
                                        otp,
                                        st.session_state.new_password,
                                        api_url
                                    )
                                    if response["success"]:
                                        st.success("Password reset successfully! Please login with your new password.")
                                        # Reset states
                                        st.session_state.reset_otp_sent = False
                                        st.session_state.reset_otp_verified = False
                                        # Switch to login tab
                                        st.session_state.active_tab = "login"
                                        time.sleep(1.5)
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Password reset failed: {response['message']}")
                
                # Option to go back
                if st.session_state.reset_otp_sent:
                    if st.button("Back", key="back_from_reset"):
                        st.session_state.reset_otp_sent = False
                        st.session_state.reset_otp_verified = False
                        if "reset_otp_input" in st.session_state:
                            del st.session_state.reset_otp_input
                        if "reset_email_phone" in st.session_state:
                            del st.session_state.reset_email_phone
                        st.experimental_rerun()
    
    # At the very end of the show_login_ui function, add the footer:
    st.markdown('<div class="footer-container">© 2025 Amaravathi One. All rights reserved.</div>', unsafe_allow_html=True) 