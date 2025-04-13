import streamlit as st
import httpx
from typing import List, Dict, Any, Optional
from api_utils import api_request
import time

def show_users_ui(token: str, api_url: str):
    """Display user management UI."""
    st.title("User Management")
    
    # Check if user has admin role
    user_data = st.session_state.user
    if user_data.get("role") != "admin":
        st.error("Access Denied. Only administrators can access user management.")
        return
    
    # Determine if user is super admin
    is_super_admin = user_data.get("is_super_admin", False)
    current_user_id = user_data.get("sub")
    
    # Display user management UI
    manage_users(token, api_url)

def fetch_users(token: str, api_url: str, role: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """Fetch users from API with optional filtering."""
    try:
        params = {}
        if role and role != "All":
            params["role"] = role
        if is_active is not None:
            params["is_active"] = "true" if is_active else "false"
            
        response = api_request("get", "/admin/users", token, api_url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch users: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []

def create_user(
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    password: str,
    role: str,
    is_active: bool,
    is_super_admin: bool,
    token: str,
    api_url: str,
    city: str = "",
    state: str = "",
    company_name: str = "",
    gstin: str = ""
) -> bool:
    """Create a new user."""
    try:
        # Prepare user data
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "password": password,
            "role": role,
            "is_active": is_active,
            "is_super_admin": is_super_admin,
            "city": city,
            "state": state,
            "company_name": company_name,
            "gstin": gstin
        }
        
        # Send API request
        response = api_request(
            "post", 
            "/admin/users", 
            token, 
            api_url,
            json=user_data
        )
        
        if response.status_code == 201:
            st.success(f"User created successfully!")
            return True
        else:
            st.error(f"Failed to create user: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def update_user(
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    role: str,
    password: Optional[str],
    is_active: bool,
    is_super_admin: bool,
    token: str,
    api_url: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    company_name: Optional[str] = None,
    gstin: Optional[str] = None
) -> bool:
    """Update an existing user."""
    try:
        # Prepare user data
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "role": role,
            "is_active": is_active,
            "is_super_admin": is_super_admin
        }
        
        # Include optional fields if provided
        if city is not None:
            user_data["city"] = city
        if state is not None:
            user_data["state"] = state
        if company_name is not None:
            user_data["company_name"] = company_name
        if gstin is not None:
            user_data["gstin"] = gstin
        
        # Only include password if provided (for password changes)
        if password:
            user_data["password"] = password
        
        # Send API request
        response = api_request(
            "put", 
            f"/admin/users/{user_id}", 
            token, 
            api_url,
            json=user_data
        )
        
        if response.status_code == 200:
            st.success(f"User updated successfully!")
            return True
        else:
            st.error(f"Failed to update user: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error updating user: {str(e)}")
        return False

def delete_user(user_id: str, token: str, api_url: str) -> bool:
    """Delete a user."""
    try:
        response = api_request(
            "delete", 
            f"/admin/users/{user_id}", 
            token, 
            api_url
        )
        
        if response.status_code == 204:
            st.success("User deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete user: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting user: {str(e)}")
        return False

def manage_users(token: str, api_url: str):
    """Display user management UI with consistent styling."""
    # Keep only one header
    st.header("User Management")
    
    # Fetch users
    with st.spinner("Loading users..."):
        users = fetch_users(token, api_url)
    
    # Add new user button with consistent styling
    if st.button("+ New User", type="primary", use_container_width=True):
        st.session_state.show_user_form = True
    
    # New user form - THIS IS THE MISSING PART THAT NEEDS TO BE ADDED
    if st.session_state.get("show_user_form", False):
        with st.form(key="new_user_form"):
            st.subheader("Add New User")
            
            # Get current user information to check permissions
            current_user = st.session_state.user
            is_super_admin = current_user.get("is_super_admin", False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name*")
                email = st.text_input("Email*")
                password = st.text_input("Password*", type="password")
                city = st.text_input("City*")
                gstin = st.text_input("GSTIN*")
                
                role = st.selectbox(
                    "Role*",
                    options=["customer", "back_office", "admin"],
                    format_func=lambda x: x.capitalize()
                )
            
            with col2:
                last_name = st.text_input("Last Name*")
                phone = st.text_input("Phone*")
                state = st.text_input("State*")
                company_name = st.text_input("Company Name*")
                
                # Active status
                is_active = st.checkbox("User is active", value=True)
                
                # Super admin option (only visible to super admins)
                if is_super_admin:
                    is_super_admin_new = st.checkbox("Super Admin privileges", value=False)
                else:
                    is_super_admin_new = False
            
            # Warning for admin role
            if role == "admin" and not is_super_admin:
                st.warning("Only super admins can create other admin users.")
            
            # Form submission
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create User", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                # Validate inputs
                if not first_name or not last_name:
                    st.error("First name and last name are required.")
                elif not email:
                    st.error("Email is required.")
                elif not password:
                    st.error("Password is required.")
                elif not city:
                    st.error("City is required.")
                elif not state:
                    st.error("State is required.")
                elif not company_name:
                    st.error("Company name is required.")
                elif not gstin:
                    st.error("GSTIN is required.")
                elif not phone:
                    st.error("Phone is required.")
                elif role == "admin" and not is_super_admin:
                    st.error("You don't have permission to create admin users.")
                else:
                    # Create the user
                    success = create_user(
                        first_name, 
                        last_name, 
                        email, 
                        phone,
                        password,
                        role,
                        is_active,
                        is_super_admin_new,
                        token,
                        api_url,
                        city=city,
                        state=state,
                        company_name=company_name,
                        gstin=gstin
                    )
                    
                    if success:
                        st.session_state.show_user_form = False
                        st.experimental_rerun()
            
            if cancel:
                st.session_state.show_user_form = False
                st.experimental_rerun()
    
    # Filter controls - consistent with other tabs
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_role = st.selectbox(
            "Filter by Role",
            ["All", "admin", "back_office", "customer"],
            key="filter_user_role"
        )
    
    with col2:
        filter_status = st.selectbox(
            "Status",
            ["All", "Active", "Inactive"],
            key="filter_user_status"
        )
    
    # Apply filters
    filtered_users = users
    
    if filter_role != "All":
        filtered_users = [u for u in filtered_users if u.get("role") == filter_role]
    
    if filter_status != "All":
        is_active = filter_status == "Active"
        filtered_users = [u for u in filtered_users if u.get("is_active", True) == is_active]
    
    # Show users count - consistent with other tabs
    st.markdown(f"### Showing {len(filtered_users)} users")
    
    # Apply custom CSS to fix table spacing
    st.markdown("""
    <style>
    /* Fix table spacing */
    .user-table {
        border-collapse: collapse;
        width: 100%;
    }
    .user-table-row {
        display: flex;
        border-bottom: 1px solid #e0e0e0;
        padding: 8px 0;
        align-items: center;
    }
    .user-table-header {
        font-weight: bold;
        background-color: #f8f9fa;
        border-bottom: 2px solid #dee2e6;
    }
    /* Make buttons consistent with other tabs */
    .stButton > button {
        height: 2rem;
        padding: 0 1rem;
        font-size: 0.8rem;
    }
    /* Reduce spacing between rows */
    [data-testid="stVerticalBlock"] > div > div[style*="flex-direction: column"] > div {
        margin-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Users table with consistent styling
    if filtered_users:
        # Table header - styled consistently
        header_cols = st.columns([0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1])
        with header_cols[0]:
            st.markdown("**Name**")
        with header_cols[1]:
            st.markdown("**Role**")
        with header_cols[2]:
            st.markdown("**Phone**")
        with header_cols[3]:
            st.markdown("**Email**")
        with header_cols[4]:
            st.markdown("**Status**")
        with header_cols[5]:
            st.markdown("**Edit**")
        with header_cols[6]:
            st.markdown("**Delete**")
        
        st.markdown("<hr style='margin: 0.5rem 0; padding: 0;'>", unsafe_allow_html=True)
        
        # Table rows - consistent compact styling
        for user in filtered_users:
            # Check if this user is being edited
            is_editing = st.session_state.get(f"edit_user_{user.get('id')}", False)
            
            if is_editing:
                # Implement edit user form that was missing
                with st.form(key=f"edit_user_form_{user.get('id')}"):
                    st.subheader(f"Edit User: {user.get('first_name', '')} {user.get('last_name', '')}")
                    
                    # Current user information from session state
                    current_user = st.session_state.user
                    is_super_admin = current_user.get("is_super_admin", False)
                    current_user_id = current_user.get("user_id") or current_user.get("sub")
                    
                    # Form fields
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        first_name = st.text_input("First Name", value=user.get("first_name", ""))
                        email = st.text_input("Email", value=user.get("email", ""))
                        city = st.text_input("City", value=user.get("city", ""))
                        gstin = st.text_input("GSTIN", value=user.get("gstin", ""))
                        
                        # Add state field here
                        state = st.text_input("State", value=user.get("state", ""))
                        
                        # Role selection (restrict based on permissions)
                        default_role_idx = ["customer", "back_office", "admin"].index(user.get("role", "customer"))
                        role = st.selectbox(
                            "Role",
                            options=["customer", "back_office", "admin"],
                            index=default_role_idx,
                            format_func=lambda x: x.capitalize(),
                            disabled=(not is_super_admin and user.get("role") == "admin" and user.get("id") != current_user_id)
                        )
                        
                    with col2:
                        last_name = st.text_input("Last Name", value=user.get("last_name", ""))
                        phone = st.text_input("Phone", value=user.get("phone", ""))
                        
                        # Add company_name field here
                        company_name = st.text_input("Company Name", value=user.get("company_name", ""))
                        
                        # Optional password field for changes
                        password = st.text_input("New Password (leave empty to keep current)", type="password")
                        
                        # Active status toggle
                        is_active = st.checkbox("User is active", value=user.get("is_active", True))
                    
                    # Super admin toggle - only visible to super admins
                    if is_super_admin:
                        super_admin = st.checkbox(
                            "Super Admin privileges",
                            value=user.get("is_super_admin", False),
                            disabled=(user.get("id") == current_user_id)  # Can't remove your own super admin
                        )
                    else:
                        super_admin = user.get("is_super_admin", False)
                    
                    # Warning about changing your own role
                    if user.get("id") == current_user_id and role != user.get("role"):
                        st.warning("⚠️ Changing your own role might restrict your access to this page.")
                    
                    # Submit buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Save Changes", use_container_width=True)
                    with col2:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                    
                    if submit:
                        # Validate inputs
                        if not first_name or not last_name:
                            st.error("First name and last name are required.")
                        elif not email:
                            st.error("Email is required.")
                        else:
                            # Call the update function
                            success = update_user(
                                user.get("id"),
                                first_name,
                                last_name,
                                email,
                                phone,
                                role,
                                password,
                                is_active,
                                super_admin,
                                token,
                                api_url,
                                city=city,
                                state=state,
                                company_name=company_name,
                                gstin=gstin
                            )
                            
                            if success:
                                # Clear the editing state and refresh
                                st.session_state[f"edit_user_{user.get('id')}"] = False
                                st.experimental_rerun()
                    
                    if cancel:
                        # Clear the editing state without saving
                        st.session_state[f"edit_user_{user.get('id')}"] = False
                        st.experimental_rerun()
            
            else:
                # Display user as a row with consistent styling
                cols = st.columns([0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1])
                
                with cols[0]:
                    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
                    st.write(full_name if full_name else "—")
                
                with cols[1]:
                    role_text = user.get('role', '').capitalize()
                    if user.get('is_super_admin', False):
                        st.markdown(f"{role_text} 🌟")
                    else:
                        st.write(role_text)
                
                with cols[2]:
                    st.write(user.get('phone', '—'))
                
                with cols[3]:
                    st.write(user.get('email', '—'))
                
                with cols[4]:
                    if user.get('is_active', True):
                        st.markdown("✅ Active")
                    else:
                        st.markdown("❌ Inactive")
                
                with cols[5]:
                    # Style the edit button consistently with other tabs
                    if st.button("Edit", key=f"btn_edit_user_{user.get('id')}", 
                               use_container_width=True):
                        st.session_state[f"edit_user_{user.get('id')}"] = True
                        st.experimental_rerun()
                
                with cols[6]:
                    # Style the delete button consistently with other tabs
                    if st.button("Delete", key=f"btn_delete_user_{user.get('id')}", 
                               use_container_width=True):
                        st.session_state[f"confirm_delete_user_{user.get('id')}"] = True
                        st.experimental_rerun()
            
            # Handle confirmation dialog for deletion
            if st.session_state.get(f"confirm_delete_user_{user.get('id')}", False):
                st.warning(f"Are you sure you want to delete user '{full_name}'?")
                confirm_cols = st.columns(2)
                with confirm_cols[0]:
                    if st.button("Yes, Delete", key=f"confirm_yes_user_{user.get('id')}"):
                        success = delete_user(user.get('id'), token, api_url)
                        if success:
                            st.session_state[f"confirm_delete_user_{user.get('id')}"] = False
                            st.experimental_rerun()
                with confirm_cols[1]:
                    if st.button("Cancel", key=f"confirm_no_user_{user.get('id')}"):
                        st.session_state[f"confirm_delete_user_{user.get('id')}"] = False
                        st.experimental_rerun()
            
            # Add thin separator between rows
            st.markdown("<hr style='margin: 0.25rem 0; padding: 0; border-top: 1px solid #e6e6e6;'>", unsafe_allow_html=True)
    else:
        # No users found message - consistent with other tabs
        st.info("No users found matching the filters. Try adjusting your filters or add a new user.")

def show_users_table(users: list, token: str, api_url: str, is_super_admin: bool, current_user_id: str):
    """Display users in an enhanced data table with actions."""
    if not users:
        st.info("No users found matching your criteria.")
        return
    
    # Prepare data for the table
    users_data = []
    for user in users:
        # Format the data for display
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        
        # Create role badge with color
        role = user.get("role", "customer")
        role_badge = {
            "admin": "🔷 Admin",
            "back_office": "🟢 Back Office",
            "customer": "⚪ Customer"
        }.get(role, "⚪ Customer")
        
        # Format status
        status = "✅ Active" if user.get("is_active", True) else "❌ Inactive"
        
        # Create super admin badge
        super_admin = "⭐ Super Admin" if user.get("is_super_admin", False) else ""
        
        users_data.append({
            "Name": full_name,
            "Role": role_badge,
            "Email": user.get("email", "-"),
            "Phone": user.get("phone", "-"),
            "Status": status,
            "Super Admin": super_admin,
            "ID": user.get("id")  # Hidden column for reference
        })
    
    # Display as interactive dataframe
    st.dataframe(
        users_data,
        column_config={
            "Name": st.column_config.TextColumn("Name"),
            "Role": st.column_config.TextColumn("Role"),
            "Email": st.column_config.TextColumn("Email"),
            "Phone": st.column_config.TextColumn("Phone"),
            "Status": st.column_config.TextColumn("Status"),
            "Super Admin": st.column_config.TextColumn(""),
            "ID": st.column_config.Column("ID", disabled=True)
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Action section for selected user
    st.markdown("### User Actions")
    
    # Select user to perform actions on
    selected_user_id = st.selectbox(
        "Select User",
        options=[user.get("id") for user in users],
        format_func=lambda x: next((f"{u.get('first_name', '')} {u.get('last_name', '')} ({u.get('role', 'customer')})" 
                                  for u in users if u.get("id") == x), "")
    )
    
    # Get the selected user
    selected_user = next((u for u in users if u.get("id") == selected_user_id), None)
    
    if selected_user:
        # Display user details and action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("#### User Details")
                st.markdown(f"**Name:** {selected_user.get('first_name', '')} {selected_user.get('last_name', '')}")
                st.markdown(f"**Email:** {selected_user.get('email', '-')}")
                st.markdown(f"**Phone:** {selected_user.get('phone', '-')}")
                st.markdown(f"**Role:** {selected_user.get('role', 'customer').capitalize()}")
                
                if selected_user.get("is_super_admin", False):
                    st.markdown("<span class='badge badge-amber'>Super Admin</span>", unsafe_allow_html=True)
        
        with col2:
            with st.container(border=True):
                st.markdown("#### Actions")
                
                # Action buttons
                if st.button("Edit User", key=f"edit_{selected_user_id}", use_container_width=True):
                    st.session_state.edit_user_id = selected_user_id
                
                # Delete button (with permission checks)
                is_self = selected_user_id == current_user_id
                is_admin = selected_user.get("role") == "admin"
                
                if is_self:
                    st.button("Delete User", disabled=True, 
                            help="You cannot delete your own account",
                            use_container_width=True)
                elif is_admin and not is_super_admin:
                    st.button("Delete User", disabled=True, 
                            help="Only super admins can delete admin accounts",
                            use_container_width=True)
                else:
                    if st.button("Delete User", type="primary", use_container_width=True):
                        st.session_state.confirm_delete_id = selected_user_id 