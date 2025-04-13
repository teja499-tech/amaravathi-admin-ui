import streamlit as st
import time
from typing import Dict, Any, Optional
from PIL import Image

def api_request(method: str, endpoint: str, token: str, api_url: str, data: dict = None) -> dict:
    """
    Make API requests to the backend with proper authentication.
    
    Args:
        method: HTTP method (get, post, put, delete)
        endpoint: API endpoint path
        token: JWT access token
        api_url: Base API URL
        data: Optional data for POST/PUT requests
        
    Returns:
        Response data as dictionary
    """
    import httpx
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{api_url}{endpoint}"
    
    try:
        with httpx.Client() as client:
            if method.lower() == "get":
                response = client.get(url, headers=headers)
            elif method.lower() == "post":
                response = client.post(url, headers=headers, json=data)
            elif method.lower() == "put":
                response = client.put(url, headers=headers, json=data)
            elif method.lower() == "delete":
                response = client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
        return {"error": e.response.text}
    except Exception as e:
        st.error(f"Request Error: {str(e)}")
        return {"error": str(e)}

def show_dashboard(user_data: Dict[str, Any], api_url: str, token: str):
    """Display the admin dashboard home page with modern UI."""
    
    # Top greeting section with logo and welcome message
    col1, col2, col3 = st.columns([6, 3, 1])
    
    with col1:
        # Extract user name
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = "Admin"
        
        st.markdown(f"## Hello, {full_name} 👋")
    
    # Cards section - 3 cards in a row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("### Product Management")
            st.markdown("Handle your product catalog with ease")
            st.markdown("When managing products, you can easily review their details and see who's added items at a glance.")
            st.markdown("")
            st.markdown("")
            st.markdown("[See the product catalog →](#products)")
            
            # Direct navigation to products page
            if st.button("Go to Products", key="goto_products"):
                # Set multiple session state variables to ensure navigation works
                st.session_state["dashboard_selection"] = "products"
                st.session_state["tabs_catalog"] = 2
                st.session_state["page"] = "products"
                st.session_state["sidebar_menu"] = "🏗️ Products"  # Match the sidebar menu option
                st.rerun()
    
    with col2:
        with st.container(border=True):
            st.markdown("### Category Management")
            st.markdown("Compare global category structure")
            st.markdown("Use insights across categories, manage hierarchies, and make competitive groupings for products.")
            st.markdown("")
            st.markdown("")
            st.markdown("[Use the category manager →](#categories)")
            
            # Direct navigation to categories page
            if st.button("Go to Categories", key="goto_categories"):
                # Set multiple session state variables to ensure navigation works
                st.session_state["dashboard_selection"] = "categories"
                st.session_state["tabs_catalog"] = 0
                st.session_state["page"] = "categories"
                st.session_state["sidebar_menu"] = "📊 Categories"  # Match the sidebar menu option
                st.rerun()
    
    with col3:
        with st.container(border=True):
            st.markdown("### User Management")
            st.markdown("Manage employee access on the go")
            st.markdown("Check and manage the users that can access the admin panel, set roles and permissions easily for each user.")
            st.markdown("")
            st.markdown("")
            st.markdown("[See the user manager →](#users)")
            
            # Direct navigation to users page
            if st.button("Go to Users", key="goto_users"):
                # Set multiple session state variables to ensure navigation works
                st.session_state["dashboard_selection"] = "users"
                st.session_state["page"] = "users"
                st.session_state["sidebar_menu"] = "👥 Users"  # Match the sidebar menu option
                st.rerun()
                
    # Recent stats section (optional)
    try:
        # Try to fetch some stats if available
        response = api_request("GET", f"{api_url}/admin/dashboard-metrics", token)
        if response and response.status_code == 200:
            metrics = response.json()
            
            st.markdown("### Quick Stats")
            stat_cols = st.columns(4)
            
            with stat_cols[0]:
                st.metric("Products", metrics.get("products_count", 0))
            with stat_cols[1]:
                st.metric("Categories", metrics.get("categories_count", 0))
            with stat_cols[2]:
                st.metric("Subcategories", metrics.get("subcategories_count", 0))
            with stat_cols[3]:
                st.metric("Users", metrics.get("users_count", 0))
    except Exception:
        # Silently fail if metrics can't be loaded
        pass

def display_metric(label: str, value: Any, icon: str = ""):
    """Display a metric in a styled container."""
    st.markdown(f"""
    <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
        <div style="font-size: 24px; margin-bottom: 8px;">{icon} {value}</div>
        <div style="color: #666; font-size: 14px;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def navigation_tile(title: str, description: str, icon: str, destination: str):
    """
    Display a navigation tile with a button.
    
    Args:
        title: Tile title
        description: Short description
        icon: Emoji icon for the tile
        destination: Destination key when button is clicked
    """
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.markdown(f"<div style='min-height: 60px;'>{description}</div>", unsafe_allow_html=True)
        
        if st.button(f"Go to {title.split()[-1]}", key=f"nav_{destination}", use_container_width=True):
            # Set the dashboard selection in session state to trigger navigation
            st.session_state.dashboard_selection = destination
            time.sleep(0.1)  # Brief delay for better UX
            st.experimental_rerun()

def sidebar_menu():
    """Create sidebar navigation menu with icons."""
    with st.sidebar:
        st.title("Amaravathi One")
        st.markdown("---")
        
        # Get user role from session state
        role = st.session_state.get("role", "admin")
        
        # Base menu options for all users
        menu_options = {
            "dashboard": "🏠 Dashboard",
            "categories": "📊 Categories",
            "subcategories": "🔖 Subcategories",
            "products": "🏗️ Products"
        }
        
        # Add role-specific options
        if role == "admin":
            menu_options["users"] = "👥 Users"
            menu_options["settings"] = "⚙️ Settings"
        
        menu_options["reports"] = "📈 Reports"
        menu_options["account"] = "👤 My Account"
        
        # Create the radio buttons for navigation
        selected = st.radio(
            "Navigation",
            options=list(menu_options.values()),
            key="sidebar_menu"
        )
        
        # Map the selection back to the destination key
        reverse_map = {v: k for k, v in menu_options.items()}
        destination = reverse_map.get(selected, "dashboard")
        
        # Set in session state if changed
        if st.session_state.get("dashboard_selection") != destination:
            st.session_state.dashboard_selection = destination
            st.experimental_rerun()
        
        # Logout button at the bottom of sidebar
        st.markdown("---")
        if st.button("Logout", type="primary", use_container_width=True):
            # Clear session state to log out
            st.session_state.clear()
            st.experimental_rerun()

def route_to_section(selection: str, user_data: Dict[str, Any], api_url: str, token: str):
    """Route to the appropriate section based on selection."""
    # Import here to avoid circular imports
    import catalog_ui
    import users_ui
    
    if selection == "dashboard":
        show_dashboard(user_data, api_url, token)
    elif selection in ["categories", "subcategories", "products"]:
        # Pass the token and API URL to catalog UI with the right tab selected
        if selection == "categories":
            st.session_state["tabs_catalog"] = 0
        elif selection == "subcategories":
            st.session_state["tabs_catalog"] = 1
        elif selection == "products":
            st.session_state["tabs_catalog"] = 2
            
        catalog_ui.show_catalog_ui(token, api_url)
    elif selection == "users":
        # Check if user has permission for user management
        if user_data.get("role") != "admin":
            st.error("You do not have permission to access User Management.")
            st.info("Please contact an administrator if you need access.")
        else:
            # Show user management UI
            users_ui.show_users_ui(token, api_url)
    elif selection == "settings":
        st.title("System Settings")
        st.info("This section is under development.")
    elif selection == "reports":
        st.title("Reports")
        st.info("This section is under development.")
    elif selection == "account":
        st.title("My Account")
        st.info("This section is under development.")
    else:
        # Default to dashboard
        show_dashboard(user_data, api_url, token)

def show_dashboard_stats(token: str, api_url: str):
    """Display dashboard statistics in a responsive grid layout."""
    st.markdown("## Key Metrics")
    
    # Fetch statistics from API
    try:
        response = api_request("get", "/admin/dashboard-stats", token, api_url)
        stats = response.json() if response.status_code == 200 else {}
    except:
        stats = {}
    
    # Create a 4-column layout for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.markdown(f"<div class='metric-value'>{stats.get('total_customers', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Customers</div>", unsafe_allow_html=True)
    
    with col2:
        with st.container(border=True):
            st.markdown(f"<div class='metric-value'>{stats.get('total_products', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Products</div>", unsafe_allow_html=True)
    
    with col3:
        with st.container(border=True):
            st.markdown(f"<div class='metric-value'>{stats.get('total_categories', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Categories</div>", unsafe_allow_html=True)
    
    with col4:
        with st.container(border=True):
            st.markdown(f"<div class='metric-value'>{stats.get('total_orders', 0)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>Orders</div>", unsafe_allow_html=True)
    
    # Create a 2-column layout for charts
    st.markdown("## Recent Activity")
    
    chart_col1, chart_col2 = st.columns([3, 2])
    
    with chart_col1:
        st.markdown("### Orders Over Time")
        # Placeholder for chart
        st.line_chart(stats.get('orders_chart_data', {'x': [0], 'y': [0]}))
    
    with chart_col2:
        st.markdown("### Top Categories")
        # Placeholder for chart
        st.bar_chart(stats.get('category_chart_data', {'x': [0], 'y': [0]})) 