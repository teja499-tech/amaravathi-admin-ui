import streamlit as st
import httpx
from typing import Dict, Optional

def show_password_reset(api_url: str, on_success_callback=None):
    """
    Display the password reset UI.
    
    Args:
        api_url: Base URL for API endpoint
        on_success_callback: Function to call after successful password reset
    """
    st.title("Reset Password")
    
    # Determine which step of the reset process we're on
    if "reset_step" not in st.session_state:
        st.session_state.reset_step = "request"  # First step is requesting a reset
    
    # Step 1: Request password reset
    if st.session_state.reset_step == "request":
        show_request_form(api_url)
    
    # Step 2: Enter token and new password
    elif st.session_state.reset_step == "reset":
        show_reset_form(api_url, on_success_callback)

def show_request_form(api_url: str):
    """Show form to request a password reset."""
    st.subheader("Request Password Reset")
    st.write("Enter your email or phone number to receive a password reset code.")
    
    with st.form("request_reset_form"):
        # Radio buttons to choose between email and phone
        contact_method = st.radio("Reset using:", ["Email", "Phone"])
        
        # Display appropriate input field based on selection
        if contact_method == "Email":
            email = st.text_input("Email Address")
            phone = None
        else:
            phone = st.text_input("Phone Number")
            email = None
        
        submit_button = st.form_submit_button("Request Reset Code")
        
        if submit_button:
            if (contact_method == "Email" and not email) or (contact_method == "Phone" and not phone):
                st.error(f"Please enter your {contact_method.lower()}")
            else:
                # Save the contact info for the next step
                if contact_method == "Email":
                    st.session_state.reset_email = email
                    st.session_state.reset_phone = None
                else:
                    st.session_state.reset_phone = phone
                    st.session_state.reset_email = None
                
                # Call API to request reset
                success = request_password_reset(api_url, email, phone)
                
                if success:
                    st.success("Reset code sent! Please check your email or phone for the code.")
                    # Move to the next step
                    st.session_state.reset_step = "reset"
                    st.experimental_rerun()

def show_reset_form(api_url: str, on_success_callback=None):
    """Show form to enter reset code and new password."""
    st.subheader("Enter Reset Code")
    st.write("Enter the code you received and your new password.")
    
    # Show which contact method was used
    if st.session_state.reset_email:
        st.info(f"Reset code was sent to email: {st.session_state.reset_email}")
    else:
        st.info(f"Reset code was sent to phone: {st.session_state.reset_phone}")
    
    with st.form("reset_password_form"):
        reset_code = st.text_input("Reset Code", help="Enter the 6-digit code you received")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submit_button = st.form_submit_button("Reset Password")
        cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            st.session_state.reset_step = "request"
            st.experimental_rerun()
        
        if submit_button:
            # Validate inputs
            if not reset_code:
                st.error("Please enter the reset code")
            elif not new_password:
                st.error("Please enter a new password")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                # Call API to reset password
                success = reset_password(
                    api_url,
                    st.session_state.reset_email,
                    st.session_state.reset_phone,
                    reset_code,
                    new_password
                )
                
                if success:
                    st.success("Password has been reset successfully!")
                    # Clear session state for reset process
                    for key in ["reset_step", "reset_email", "reset_phone"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Show a button to return to login
                    if st.button("Return to Login"):
                        if on_success_callback:
                            on_success_callback()
                        else:
                            st.experimental_rerun()

def request_password_reset(api_url: str, email: Optional[str], phone: Optional[str]) -> bool:
    """
    Call API to request password reset.
    
    Args:
        api_url: API base URL
        email: User email or None
        phone: User phone or None
        
    Returns:
        True if request successful, False otherwise
    """
    try:
        with httpx.Client() as client:
            # Prepare form data
            form_data = {}
            if email:
                form_data["email"] = email
            if phone:
                form_data["phone"] = phone
            
            # Make API request
            response = client.post(
                f"{api_url}/auth/request-password-reset",
                data=form_data
            )
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Error: {response.json().get('detail', 'Failed to request password reset')}")
                return False
    except Exception as e:
        st.error(f"Error connecting to the server: {str(e)}")
        return False

def reset_password(
    api_url: str, 
    email: Optional[str], 
    phone: Optional[str], 
    otp: str, 
    new_password: str
) -> bool:
    """
    Call API to reset password.
    
    Args:
        api_url: API base URL
        email: User email or None
        phone: User phone or None
        otp: Reset code/OTP
        new_password: New password to set
        
    Returns:
        True if reset successful, False otherwise
    """
    try:
        with httpx.Client() as client:
            # Prepare form data
            form_data = {
                "otp": otp,
                "new_password": new_password
            }
            if email:
                form_data["email"] = email
            if phone:
                form_data["phone"] = phone
            
            # Make API request
            response = client.post(
                f"{api_url}/auth/reset-password",
                data=form_data
            )
            
            if response.status_code == 200:
                return True
            else:
                st.error(f"Error: {response.json().get('detail', 'Failed to reset password')}")
                return False
    except Exception as e:
        st.error(f"Error connecting to the server: {str(e)}")
        return False 