import streamlit as st
import httpx
import jwt
from datetime import datetime
from typing import Dict, Optional, Any, List

def is_token_expired(token: str) -> bool:
    """Check if a token is expired."""
    try:
        payload = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
        if "exp" in payload:
            return datetime.utcnow().timestamp() > payload["exp"]
        return False
    except Exception:
        return True

def refresh_access_token(refresh_token: str, api_url: str) -> Dict:
    """Use refresh token to get a new access token."""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{api_url}/auth/refresh-token",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to refresh token"
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error refreshing token: {str(e)}"
        }

def get_auth_header(token: str) -> Dict[str, str]:
    """Get authorization header with token."""
    return {"Authorization": f"Bearer {token}"}

def api_request(method: str, endpoint: str, token: str, api_url: str, **kwargs) -> httpx.Response:
    """Make an API request with automatic token refresh."""
    # Get authorization header
    headers = kwargs.get("headers", {})
    headers.update(get_auth_header(token))
    kwargs["headers"] = headers
    
    # Make the request
    with httpx.Client() as client:
        url = f"{api_url}/{endpoint.lstrip('/')}"
        method_func = getattr(client, method.lower())
        return method_func(url, **kwargs)

def upload_image(file, bucket: str, token: str, api_url: str) -> Optional[str]:
    """Upload an image file to the API."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        
        response = api_request(
            "post", 
            f"/admin/upload/{bucket}", 
            token, 
            api_url,
            files=files
        )
        
        if response.status_code == 200:
            return response.json().get("url")
        else:
            st.error(f"Failed to upload image: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading image: {str(e)}")
        return None 

def api_request_with_feedback(method: str, endpoint: str, token: str, api_url: str, feedback_location=None, **kwargs) -> httpx.Response:
    """Make API request with visual feedback on errors."""
    try:
        response = api_request(method, endpoint, token, api_url, **kwargs)
        
        # Handle different status codes
        if response.status_code >= 400:
            error_msg = f"Error {response.status_code}"
            try:
                error_detail = response.json().get("detail", "Unknown error")
                error_msg = f"{error_msg}: {error_detail}"
            except:
                error_msg = f"{error_msg}: {response.text}"
            
            # Show error in the specified location or default to st
            if feedback_location:
                feedback_location.error(error_msg)
            else:
                st.error(error_msg)
        
        return response
    except Exception as e:
        error_msg = f"Network error: {str(e)}"
        if feedback_location:
            feedback_location.error(error_msg)
        else:
            st.error(error_msg)
        
        # Return a fake response with error info
        class FakeResponse:
            status_code = 500
            text = error_msg
            
            def json(self):
                return {"detail": error_msg}
        
        return FakeResponse() 

def perform_api_action(action_type: str, endpoint: str, token: str, api_url: str, **kwargs) -> bool:
    """Perform an API action with appropriate toast notifications."""
    # Generate action descriptions
    actions = {
        "create": {"ing": "Creating", "past": "created"},
        "update": {"ing": "Updating", "past": "updated"},
        "delete": {"ing": "Deleting", "past": "deleted"},
        "publish": {"ing": "Publishing", "past": "published"},
        "archive": {"ing": "Archiving", "past": "archived"}
    }
    
    action = actions.get(action_type, {"ing": "Processing", "past": "processed"})
    
    # Extract item name from kwargs if provided
    item_name = kwargs.pop("item_name", "item")
    
    # Show spinner during operation
    with st.spinner(f"{action['ing']} {item_name}..."):
        try:
            # Perform the API request
            response = api_request("post", endpoint, token, api_url, **kwargs)
            
            # Handle success
            if response.status_code in [200, 201, 204]:
                # Show toast notification
                st.toast(f"✅ Successfully {action['past']} {item_name}", icon="✅")
                return True
            else:
                # Show error toast
                error_msg = response.json().get("detail", f"Failed to {action_type} {item_name}")
                st.toast(f"❌ {error_msg}", icon="❌")
                
                # Show detailed error message
                st.error(f"Error: {error_msg}")
                return False
                
        except Exception as e:
            # Show error for exceptions
            st.toast(f"❌ Operation failed", icon="❌")
            st.error(f"Error: {str(e)}")
            return False 