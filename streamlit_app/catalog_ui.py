import streamlit as st
import httpx
from typing import List, Dict, Any, Optional
import io
from api_utils import api_request
import time
import requests

def show_catalog_ui(token: str, api_url: str):
    """Display catalog UI with tabs for categories, subcategories, and products."""
    st.title("Product Catalog Management")
    
    # Get the selected tab from session state (0=categories, 1=subcategories, 2=products)
    selected_tab = st.session_state.get("tabs_catalog", 0)
    
    # Instead of showing tabs, directly display the selected content based on sidebar selection
    if selected_tab == 0:
        # Show categories management without tabs
        st.header("Category Management")
        manage_categories(token, api_url)
    elif selected_tab == 1:
        # Show subcategories management without tabs
        st.header("Subcategory Management")
        manage_subcategories(token, api_url)
    elif selected_tab == 2:
        # Show products management without tabs
        st.header("Product Management")
        manage_products(token, api_url)

def fetch_categories(token: str, api_url: str) -> List[Dict[str, Any]]:
    """Fetch all categories from API."""
    try:
        response = api_request("get", "/categories", token, api_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch categories: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {str(e)}")
        return []

def upload_image(file, token: str, api_url: str) -> Optional[str]:
    """Upload an image file to the API."""
    if not file:
        st.error("No image file provided")
        return None
    
    with st.spinner("Uploading image..."):
        try:
            # Prepare the files and headers for the request
            files = {"file": (file.name, file.getvalue(), file.type)}
            headers = {"Authorization": f"Bearer {token}"}
            
            # Use the new endpoint we developed for image uploads
            response = requests.post(
                f"{api_url}/admin/upload-image",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data.get("url")
                return image_url  # Return the public URL
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                except:
                    error_detail = response.text
                
                st.error(f"Failed to upload image: {error_detail}")
                return None
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")
            return None

def create_category(name: str, image_file, is_active: bool, token: str, api_url: str) -> bool:
    """Create a new category."""
    try:
        # Upload image if provided
        image_url = None
        if image_file is not None:
            image_url = upload_image(image_file, token, api_url)
            
        # Prepare category data
        category_data = {
            "name": name,
            "is_active": is_active
        }
        
        # Add image URL if successfully uploaded
        if image_url:
            category_data["image_url"] = image_url
        
        # Create category via API
        response = api_request(
            "post", 
            "/admin/categories", 
            token, 
            api_url,
            json=category_data
        )
        
        if response.status_code == 201:
            st.success(f"Category '{name}' created successfully!")
            return True
        else:
            st.error(f"Failed to create category: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error creating category: {str(e)}")
        return False

def update_category(category_id: str, name: str, image_file, is_active: bool, token: str, api_url: str) -> bool:
    """Update an existing category."""
    try:
        # Upload new image if provided
        image_url = None
        if image_file is not None:
            image_url = upload_image(image_file, token, api_url)
        
        # Prepare category data
        category_data = {
            "name": name,
            "is_active": is_active
        }
        
        # Add image URL if a new image was successfully uploaded
        if image_url:
            category_data["image_url"] = image_url
        
        # Update category via API
        response = api_request(
            "put", 
            f"/admin/categories/{category_id}", 
            token, 
            api_url,
            json=category_data
        )
        
        if response.status_code == 200:
            st.success(f"Category '{name}' updated successfully!")
            return True
        else:
            st.error(f"Failed to update category: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error updating category: {str(e)}")
        return False

def delete_category(category_id: str, token: str, api_url: str) -> bool:
    """Delete a category."""
    try:
        # Delete category via API
        response = api_request(
            "delete", 
            f"/admin/categories/{category_id}", 
            token, 
            api_url
        )
        
        if response.status_code == 204:
            st.success("Category deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete category: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting category: {str(e)}")
        return False

def manage_categories(token: str, api_url: str):
    """Display category management UI."""
    st.header("Category Management")
    
    # Fetch categories
    with st.spinner("Loading categories..."):
        categories = fetch_categories(token, api_url)
    
    # Add new category button (opens form in an expander)
    if st.button("+ New Category", type="primary", use_container_width=True):
        st.session_state.show_category_form = True
    
    # New category form
    if st.session_state.get("show_category_form", False):
        with st.form(key="new_category_form", clear_on_submit=True):
            st.subheader("Add New Category")
            
            # Category name input
            name = st.text_input("Category Name", key="new_cat_name")
            
            # Image upload
            image_file = st.file_uploader(
                "Category Image",
                type=["jpg", "jpeg", "png"],
                key="new_cat_image"
            )
            
            # Show image preview if uploaded
            if image_file:
                st.image(image_file, caption="Image Preview", width=300)
            
            # Active toggle
            is_active = st.checkbox("Category is active", value=True, key="new_cat_active")
            
            # Form submission buttons
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Category", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                if not name:
                    st.error("Category name is required")
                else:
                    success = create_category(name, image_file, is_active, token, api_url)
                    if success:
                        st.session_state.show_category_form = False
                        st.experimental_rerun()
            
            if cancel:
                st.session_state.show_category_form = False
                st.experimental_rerun()
    
    # Category filter
    filter_name = st.text_input("Filter categories by name", placeholder="Enter category name to filter")
    
    # Filter categories by name if filter is provided
    if filter_name:
        filtered_categories = [c for c in categories if filter_name.lower() in c.get("name", "").lower()]
    else:
        filtered_categories = categories
    
    # Show categories count
    st.markdown(f"### Showing {len(filtered_categories)} categories")
    
    # Category table with edit/delete functionality
    if filtered_categories:
        # Create a container for the table with some padding
        table_container = st.container()
        
        with table_container:
            # Create a table-like display using columns and containers
            # Table header
            header_cols = st.columns([0.15, 0.35, 0.15, 0.15, 0.2])
            with header_cols[0]:
                st.markdown("**Image**")
            with header_cols[1]:
                st.markdown("**Name**")
            with header_cols[2]:
                st.markdown("**Status**")
            with header_cols[3]:
                st.markdown("**Edit**")
            with header_cols[4]:
                st.markdown("**Delete**")
            
            st.markdown("---")
            
            # Table rows
            for category in filtered_categories:
                # Check if this category is being edited
                is_editing = st.session_state.get(f"edit_category_{category.get('id')}", False)
                
                if is_editing:
                    # Edit mode
                    with st.form(key=f"edit_category_form_{category.get('id')}"):
                        st.subheader(f"Edit Category: {category.get('name')}")
                        
                        # Category name input
                        edited_name = st.text_input(
                            "Category Name", 
                            value=category.get("name", ""),
                            key=f"edit_cat_name_{category.get('id')}"
                        )
                        
                        # Image upload
                        edited_image = st.file_uploader(
                            "New Category Image (optional)",
                            type=["jpg", "jpeg", "png"],
                            key=f"edit_cat_image_{category.get('id')}"
                        )
                        
                        # Show current image if available
                        if "image_url" in category and category["image_url"]:
                            st.markdown("**Current Image:**")
                            st.image(category["image_url"], width=200)
                        
                        # Show new image preview if uploaded
                        if edited_image:
                            st.markdown("**New Image Preview:**")
                            st.image(edited_image, width=200)
                        
                        # Active toggle
                        edited_active = st.checkbox(
                            "Category is active", 
                            value=category.get("is_active", True),
                            key=f"edit_cat_active_{category.get('id')}"
                        )
                        
                        # Form submission buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update", use_container_width=True)
                        with col2:
                            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if update_button:
                            if not edited_name:
                                st.error("Category name is required")
                            else:
                                success = update_category(
                                    category.get("id"),
                                    edited_name,
                                    edited_image,
                                    edited_active,
                                    token,
                                    api_url
                                )
                                if success:
                                    st.session_state[f"edit_category_{category.get('id')}"] = False
                                    st.experimental_rerun()
                        
                        if cancel_button:
                            st.session_state[f"edit_category_{category.get('id')}"] = False
                            st.experimental_rerun()
                else:
                    # View mode - display as a row
                    row_cols = st.columns([0.15, 0.35, 0.15, 0.15, 0.2])
                    
                    with row_cols[0]:
                        # Show image thumbnail
                        if "image_url" in category and category["image_url"]:
                            st.image(category["image_url"], width=60)
                        else:
                            st.write("No image")
                    
                    with row_cols[1]:
                        st.write(category.get("name", "Unnamed"))
                    
                    with row_cols[2]:
                        if category.get("is_active", True):
                            st.markdown("✅ Active")
                        else:
                            st.markdown("❌ Inactive")
                    
                    with row_cols[3]:
                        if st.button("Edit", key=f"btn_edit_{category.get('id')}"):
                            st.session_state[f"edit_category_{category.get('id')}"] = True
                            st.experimental_rerun()
                    
                    with row_cols[4]:
                        if st.button("Delete", key=f"btn_delete_{category.get('id')}"):
                            # Show confirmation dialog
                            st.session_state[f"confirm_delete_{category.get('id')}"] = True
                            st.experimental_rerun()
                
                # Confirmation dialog for deletion
                if st.session_state.get(f"confirm_delete_{category.get('id')}", False):
                    st.warning(f"Are you sure you want to delete category '{category.get('name')}'?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete", key=f"confirm_yes_{category.get('id')}"):
                            success = delete_category(category.get("id"), token, api_url)
                            if success:
                                st.session_state[f"confirm_delete_{category.get('id')}"] = False
                                st.experimental_rerun()
                    with col2:
                        if st.button("Cancel", key=f"confirm_no_{category.get('id')}"):
                            st.session_state[f"confirm_delete_{category.get('id')}"] = False
                            st.experimental_rerun()
                
                # Separator between rows
                st.markdown("---")
    else:
        # No categories found
        st.info("No categories found. Click 'New Category' to add one.")

def fetch_subcategories(token: str, api_url: str, category_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch subcategories from API."""
    try:
        if category_id:
            # If category_id is provided, fetch subcategories for that category
            endpoint = f"/categories/{category_id}/subcategories"
        else:
            # If no category_id, get all subcategories directly
            endpoint = "/subcategories"
        
        response = api_request("get", endpoint, token, api_url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch subcategories: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching subcategories: {str(e)}")
        return []

def create_subcategory(name: str, category_id: str, is_active: bool, image_url: Optional[str], token: str, api_url: str) -> bool:
    """Create a new subcategory."""
    try:
        # Prepare subcategory data
        subcategory_data = {
            "name": name,
            "category_id": category_id,
            "is_active": is_active
        }
        
        # Add image URL if provided
        if image_url:
            subcategory_data["image_url"] = image_url
        
        # Send API request - Use the correct admin endpoint
        response = api_request(
            "post", 
            "/admin/subcategories",  # Changed from /categories/{category_id}/subcategories
            token, 
            api_url,
            json=subcategory_data
        )
        
        if response.status_code == 201:
            st.success(f"Subcategory '{name}' created successfully!")
            return True
        else:
            st.error(f"Failed to create subcategory: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error creating subcategory: {str(e)}")
        return False

def update_subcategory(subcategory_id: str, name: str, category_id: str, image_file, is_active: bool, token: str, api_url: str) -> bool:
    """Update an existing subcategory."""
    try:
        # Upload image if provided
        image_url = None
        if image_file is not None:
            image_url = upload_image(image_file, token, api_url)
            if not image_url:
                st.error("Failed to upload image")
                return False
        
        # Prepare subcategory data
        subcategory_data = {
            "name": name,
            "category_id": category_id,
            "is_active": is_active
        }
        if image_url:
            subcategory_data["image_url"] = image_url
        
        # Send API request
        response = api_request(
            "put", 
            f"/admin/subcategories/{subcategory_id}", 
            token, 
            api_url,
            json=subcategory_data
        )
        
        if response.status_code == 200:
            st.success(f"Subcategory '{name}' updated successfully!")
            return True
        else:
            st.error(f"Failed to update subcategory: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error updating subcategory: {str(e)}")
        return False

def manage_subcategories(token: str, api_url: str):
    """Display subcategory management UI."""
    st.header("Subcategory Management")
    
    # Fetch categories for dropdown
    with st.spinner("Loading categories..."):
        categories = fetch_categories(token, api_url)
    
    # Create category name map for display
    category_map = {c.get("id"): c.get("name", "Unknown") for c in categories}
    
    # Fetch all subcategories by making a separate API call for each category
    with st.spinner("Loading subcategories..."):
        all_subcategories = []
        for category in categories:
            category_id = category.get("id")
            category_subcats = fetch_subcategories(token, api_url, category_id)
            # Add the category name for display purposes
            for subcat in category_subcats:
                subcat["category_name"] = category_map.get(category_id, "Unknown")
            
            all_subcategories.extend(category_subcats)
    
    # Add new subcategory button
    if st.button("+ New Subcategory", type="primary", use_container_width=True):
        st.session_state.show_subcategory_form = True
    
    # New subcategory form - Add this missing form
    if st.session_state.get("show_subcategory_form", False):
        with st.form(key="new_subcategory_form"):
            st.subheader("Add New Subcategory")
            
            # Subcategory name input
            name = st.text_input("Subcategory Name*")
            
            # Category selection dropdown
            if categories:
                category_options = [(c.get("id"), c.get("name", "Unknown")) for c in categories]
                selected_category = st.selectbox(
                    "Parent Category*",
                    options=[opt[0] for opt in category_options],
                    format_func=lambda x: next((name for id, name in category_options if id == x), "Unknown")
                )
            else:
                st.error("No categories available. Please create a category first.")
                selected_category = None
            
            # Active status
            is_active = st.checkbox("Subcategory is active", value=True)
            
            # Image upload field (optional)
            st.markdown("#### Subcategory Image (optional)")
            uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], key="subcategory_image")
            
            if uploaded_file:
                # Preview the image
                st.image(uploaded_file, width=200, caption="Image Preview")
            
            # Submit buttons
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Subcategory", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                # Validate inputs
                if not name:
                    st.error("Subcategory name is required.")
                elif not selected_category:
                    st.error("Parent category is required.")
                else:
                    # Handle image upload if provided
                    image_url = None
                    if uploaded_file:
                        with st.spinner("Uploading image..."):
                            image_url = upload_image(uploaded_file, token, api_url)
                    
                    # Create subcategory with or without image
                    success = create_subcategory(
                        name, 
                        selected_category, 
                        is_active, 
                        image_url,
                        token, 
                        api_url
                    )
                    
                    if success:
                        st.session_state.show_subcategory_form = False
                        st.experimental_rerun()
            
            if cancel:
                st.session_state.show_subcategory_form = False
                st.experimental_rerun()
    
    # Filter controls
    col1, col2 = st.columns([2, 1])
    
    with col1:
        filter_name = st.text_input("Filter subcategories by name", placeholder="Enter subcategory name")
    
    with col2:
        filter_category = st.selectbox(
            "Filter by Category",
            options=["All"] + list(category_map.values()),
            key="filter_subcat_category"
        )
    
    # Apply filters to the already fetched subcategories
    filtered_subcategories = all_subcategories
    
    # Filter by name
    if filter_name:
        filtered_subcategories = [s for s in filtered_subcategories if filter_name.lower() in s.get("name", "").lower()]
    
    # Filter by category
    if filter_category != "All":
        # Use the category name we added earlier
        filtered_subcategories = [s for s in filtered_subcategories if s.get("category_name") == filter_category]
    
    # Show subcategories count
    st.markdown(f"### Showing {len(filtered_subcategories)} subcategories")
    
    # Subcategory table with edit/delete functionality
    if filtered_subcategories:
        # Create a container for the table
        table_container = st.container()
        
        with table_container:
            # Table header
            header_cols = st.columns([0.1, 0.3, 0.25, 0.15, 0.1, 0.1])
            with header_cols[0]:
                st.markdown("**Image**")
            with header_cols[1]:
                st.markdown("**Name**")
            with header_cols[2]:
                st.markdown("**Category**")
            with header_cols[3]:
                st.markdown("**Status**")
            with header_cols[4]:
                st.markdown("**Edit**")
            with header_cols[5]:
                st.markdown("**Delete**")
            
            st.markdown("---")
            
            # Table rows
            for subcategory in filtered_subcategories:
                # Check if this subcategory is being edited
                is_editing = st.session_state.get(f"edit_subcategory_{subcategory.get('id')}", False)
                
                if is_editing:
                    # Edit mode
                    with st.form(key=f"edit_subcategory_form_{subcategory.get('id')}"):
                        st.subheader(f"Edit Subcategory: {subcategory.get('name')}")
                        
                        # Subcategory name input
                        edited_name = st.text_input(
                            "Subcategory Name", 
                            value=subcategory.get("name", ""),
                            key=f"edit_subcat_name_{subcategory.get('id')}"
                        )
                        
                        # Category selection dropdown
                        current_category = subcategory.get("category_id")
                        category_options = [(c.get("id"), c.get("name", "Unknown")) for c in categories]
                        
                        # Find the index of the current category
                        selected_index = 0
                        for i, (cat_id, _) in enumerate(category_options):
                            if cat_id == current_category:
                                selected_index = i
                                break
                        
                        edited_category = st.selectbox(
                            "Parent Category",
                            options=[opt[0] for opt in category_options],
                            format_func=lambda x: next((name for id, name in category_options if id == x), "Unknown"),
                            key=f"edit_subcat_category_{subcategory.get('id')}",
                            index=selected_index
                        )
                        
                        # Image upload
                        edited_image = st.file_uploader(
                            "New Subcategory Image (optional)",
                            type=["jpg", "jpeg", "png"],
                            key=f"edit_subcat_image_{subcategory.get('id')}"
                        )
                        
                        # Show current image if available
                        if "image_url" in subcategory and subcategory["image_url"]:
                            st.markdown("**Current Image:**")
                            st.image(subcategory["image_url"], width=200)
                        
                        # Show new image preview if uploaded
                        if edited_image:
                            st.markdown("**New Image Preview:**")
                            st.image(edited_image, width=200)
                        
                        # Active toggle
                        edited_active = st.checkbox(
                            "Subcategory is active", 
                            value=subcategory.get("is_active", True),
                            key=f"edit_subcat_active_{subcategory.get('id')}"
                        )
                        
                        # Form submission buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update", use_container_width=True)
                        with col2:
                            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if update_button:
                            if not edited_name:
                                st.error("Subcategory name is required")
                            elif not edited_category:
                                st.error("Parent category is required")
                            else:
                                success = update_subcategory(
                                    subcategory.get("id"),
                                    edited_name,
                                    edited_category,
                                    edited_image,
                                    edited_active,
                                    token,
                                    api_url
                                )
                                if success:
                                    st.session_state[f"edit_subcategory_{subcategory.get('id')}"] = False
                                    st.experimental_rerun()
                        
                        if cancel_button:
                            st.session_state[f"edit_subcategory_{subcategory.get('id')}"] = False
                            st.experimental_rerun()
                else:
                    # View mode - display as a row
                    row_cols = st.columns([0.1, 0.3, 0.25, 0.15, 0.1, 0.1])
                    
                    with row_cols[0]:
                        # Show image thumbnail
                        if "image_url" in subcategory and subcategory["image_url"]:
                            st.image(subcategory["image_url"], width=50)
                        else:
                            st.write("—")
                    
                    with row_cols[1]:
                        st.write(subcategory.get("name", "Unnamed"))
                    
                    with row_cols[2]:
                        # Get category name from map
                        category_name = category_map.get(subcategory.get("category_id"), "Unknown")
                        st.write(category_name)
                    
                    with row_cols[3]:
                        if subcategory.get("is_active", True):
                            st.markdown("✅ Active")
                        else:
                            st.markdown("❌ Inactive")
                    
                    with row_cols[4]:
                        if st.button("Edit", key=f"btn_edit_subcat_{subcategory.get('id')}"):
                            st.session_state[f"edit_subcategory_{subcategory.get('id')}"] = True
                            st.experimental_rerun()
                    
                    with row_cols[5]:
                        if st.button("Delete", key=f"btn_delete_subcat_{subcategory.get('id')}"):
                            # Show confirmation dialog
                            st.session_state[f"confirm_delete_subcat_{subcategory.get('id')}"] = True
                            st.experimental_rerun()
                
                # Confirmation dialog for deletion
                if st.session_state.get(f"confirm_delete_subcat_{subcategory.get('id')}", False):
                    st.warning(f"Are you sure you want to delete subcategory '{subcategory.get('name')}'?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete", key=f"confirm_yes_subcat_{subcategory.get('id')}"):
                            success = delete_subcategory(subcategory.get("id"), token, api_url)
                            if success:
                                st.session_state[f"confirm_delete_subcat_{subcategory.get('id')}"] = False
                                st.experimental_rerun()
                    with col2:
                        if st.button("Cancel", key=f"confirm_no_subcat_{subcategory.get('id')}"):
                            st.session_state[f"confirm_delete_subcat_{subcategory.get('id')}"] = False
                            st.experimental_rerun()
                
                # Separator between rows
                st.markdown("---")
    else:
        # No subcategories found
        st.info("No subcategories found. Click 'New Subcategory' to add one.")

def delete_subcategory(subcategory_id: str, token: str, api_url: str) -> bool:
    """Delete a subcategory."""
    try:
        # Delete subcategory via API
        response = api_request(
            "delete", 
            f"/admin/subcategories/{subcategory_id}", 
            token, 
            api_url
        )
        
        if response.status_code == 204:
            st.success("Subcategory deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete subcategory: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting subcategory: {str(e)}")
        return False

def fetch_products(token: str, api_url: str, category_id: Optional[str] = None, subcategory_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch products from API."""
    try:
        params = {}
        if category_id:
            params["category_id"] = category_id
        if subcategory_id:
            params["subcategory_id"] = subcategory_id
        
        response = api_request("get", "/products", token, api_url, params=params)
        
        if response.status_code == 200:
            products = response.json()
            if isinstance(products, list):
                return products
            elif isinstance(products, dict) and "items" in products:
                # Handle case where API returns {items: [...]}
                return products["items"]
            else:
                st.error(f"Unexpected response format: {products}")
                return []
        else:
            st.error(f"Failed to fetch products: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching products: {str(e)}")
        return []

def create_product(
    name: str, 
    description: str, 
    dimensions: str, 
    usage: str, 
    benefits: str, 
    price: float, 
    category_id: Optional[str], 
    subcategory_id: Optional[str], 
    image_files: List, 
    is_active: bool, 
    token: str, 
    api_url: str
) -> bool:
    """Create a new product."""
    try:
        # Upload images if provided (max 5)
        image_urls = []
        for image_file in image_files[:5]:  # Limit to 5 images
            if image_file is not None:
                image_url = upload_image(image_file, token, api_url)
                if image_url:
                    image_urls.append(image_url)
        
        # Prepare product data
        product_data = {
            "name": name,
            "description": description,
            "dimensions": dimensions,
            "usage": usage,
            "benefits": benefits,
            "price": price,
            "image_urls": image_urls,
            "is_active": is_active
        }
        
        if category_id:
            product_data["category_id"] = category_id
        if subcategory_id:
            product_data["subcategory_id"] = subcategory_id
        
        # Send API request
        response = api_request(
            "post", 
            "/admin/products", 
            token, 
            api_url,
            json=product_data
        )
        
        if response.status_code == 201:
            st.success(f"Product '{name}' created successfully!")
            return True
        else:
            st.error(f"Failed to create product: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error creating product: {str(e)}")
        return False

def update_product(
    product_id: str,
    name: str, 
    description: str, 
    dimensions: str, 
    usage: str, 
    benefits: str, 
    price: float, 
    category_id: Optional[str], 
    subcategory_id: Optional[str], 
    image_files: List, 
    is_active: bool, 
    token: str, 
    api_url: str,
    existing_images: List[str] = []
) -> bool:
    """Update an existing product."""
    try:
        # Upload new images if provided
        new_image_urls = []
        for image_file in image_files:
            if image_file is not None:
                image_url = upload_image(image_file, token, api_url)
                if image_url:
                    new_image_urls.append(image_url)
        
        # Combine with existing images (respecting max 5)
        image_urls = existing_images + new_image_urls
        image_urls = image_urls[:5]  # Limit to 5 images
        
        # Prepare product data
        product_data = {
            "name": name,
            "description": description,
            "dimensions": dimensions,
            "usage": usage,
            "benefits": benefits,
            "price": price,
            "image_urls": image_urls,
            "is_active": is_active
        }
        
        if category_id:
            product_data["category_id"] = category_id
        if subcategory_id:
            product_data["subcategory_id"] = subcategory_id
        
        # Send API request
        response = api_request(
            "put", 
            f"/admin/products/{product_id}", 
            token, 
            api_url,
            json=product_data
        )
        
        if response.status_code == 200:
            st.success(f"Product '{name}' updated successfully!")
            return True
        else:
            st.error(f"Failed to update product: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error updating product: {str(e)}")
        return False

def delete_product(product_id: str, token: str, api_url: str) -> bool:
    """Delete a product."""
    try:
        response = api_request(
            "delete", 
            f"/admin/products/{product_id}", 
            token, 
            api_url
        )
        
        if response.status_code == 204:
            st.success("Product deleted successfully!")
            return True
        else:
            st.error(f"Failed to delete product: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting product: {str(e)}")
        return False

def manage_products(token: str, api_url: str):
    """Display product management UI."""
    # Keep only one header
    st.header("Product Management")
    
    # Fetch categories and subcategories for filters
    with st.spinner("Loading categories and subcategories..."):
        categories = fetch_categories(token, api_url)
        category_map = {c.get("id"): c.get("name", "Unknown") for c in categories}
        
        # Fetch all subcategories for each category
        subcategories_by_category = {}
        all_subcategories = []
        
        for category in categories:
            category_id = category.get("id")
            subcats = fetch_subcategories(token, api_url, category_id)
            subcategories_by_category[category_id] = subcats
            all_subcategories.extend(subcats)
        
        subcategory_map = {s.get("id"): s.get("name", "Unknown") for s in all_subcategories}
    
    # Debug the API call for products
    with st.spinner("Loading products..."):
        all_products = fetch_products(token, api_url)
        # Add debug info about the products being fetched
        st.write(f"Found {len(all_products)} products from API")
    
    # Add new product button
    if st.button("+ New Product", type="primary", use_container_width=True):
        st.session_state.show_category_selector = True
        st.session_state.show_product_form = False

    # Step 1: Category selection outside the form
    if st.session_state.get("show_category_selector", False):
        st.subheader("Step 1: Select Product Category")
        
        if categories:
            category_options = [(c.get("id"), c.get("name", "Unknown")) for c in categories]
            selected_category = st.selectbox(
                "Category",
                options=[opt[0] for opt in category_options],
                format_func=lambda x: next((name for id, name in category_options if id == x), "Unknown"),
                key="pre_select_category"
            )
            
            if st.button("Continue to Product Details", type="primary"):
                st.session_state.selected_category = selected_category
                st.session_state.show_category_selector = False
                st.session_state.show_product_form = True
                st.experimental_rerun()
                
            if st.button("Cancel"):
                st.session_state.show_category_selector = False
                st.experimental_rerun()
        else:
            st.error("No categories available. Please create a category first.")

    # Step 2: Complete product form with pre-selected category
    if st.session_state.get("show_product_form", False):
        # Get pre-selected category from session state
        selected_category = st.session_state.get("selected_category")
        
        # Get subcategories for this category
        subcategory_options = []
        if selected_category and selected_category in subcategories_by_category:
            available_subcats = subcategories_by_category[selected_category]
            subcategory_options = [(s.get("id"), s.get("name", "Unknown")) for s in available_subcats]
        
        with st.form(key="new_product_form"):
            st.subheader("Add New Product")
            
            # Product name input
            name = st.text_input("Product Name", key="new_prod_name")
            
            # Description
            description = st.text_area("Description", key="new_prod_desc")
            
            # Layout in columns
            col1, col2 = st.columns(2)
            
            with col1:
                # Dimensions
                dimensions = st.text_input("Dimensions", key="new_prod_dim", 
                                        placeholder="e.g., 10cm x 20cm x 5cm")
                
                # Show selected category (readonly)
                st.write(f"**Category:** {category_map.get(selected_category, 'Unknown')}")
            
            with col2:
                # Price
                price = st.number_input("Price", min_value=0.0, step=0.01, key="new_prod_price")
                
                # Subcategory selection with options already filtered
                if subcategory_options:
                    selected_subcategory = st.selectbox(
                        "Subcategory (optional)",
                        options=["None"] + [opt[0] for opt in subcategory_options],
                        format_func=lambda x: "None" if x == "None" else next((name for id, name in subcategory_options if id == x), "Unknown"),
                        key="new_prod_subcategory"
                    )
                    if selected_subcategory == "None":
                        selected_subcategory = None
                else:
                    st.info("No subcategories available for this category")
                    selected_subcategory = None
            
            # Usage
            usage = st.text_area("Usage", key="new_prod_usage", 
                               placeholder="How should customers use this product?")
            
            # Benefits
            benefits = st.text_area("Benefits", key="new_prod_benefits", 
                                  placeholder="What are the key benefits of this product?")
            
            # Image uploads (up to 5)
            st.write("Upload Product Images (up to 5 images)")
            st.caption("Recommended: 800x600 pixels, JPG/PNG format")
            
            image_cols = st.columns(5)
            image_files = []
            
            for i in range(5):
                with image_cols[i]:
                    image_files.append(st.file_uploader(
                        f"Image {i+1}",
                        type=["jpg", "jpeg", "png"],
                        key=f"new_prod_img_{i}"
                    ))
            
            # Preview images
            if any(image_files):
                st.write("Image Previews:")
                preview_cols = st.columns(5)
                for i, img in enumerate(image_files):
                    if img:
                        with preview_cols[i]:
                            st.image(img, width=100, caption=f"Image {i+1}")
            
            # Active toggle
            is_active = st.checkbox("Product is active", value=True, key="new_prod_active")
            
            # Form submission buttons
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Create Product", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                # Validate inputs
                errors = []
                if not name:
                    errors.append("Product name is required")
                if not description:
                    errors.append("Product description is required")
                if not selected_category:
                    errors.append("Category is required")
                if not any(image_files):
                    errors.append("At least one product image is required")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Filter out None values from image_files
                    valid_image_files = [img for img in image_files if img is not None]
                    
                    success = create_product(
                        name, 
                        description, 
                        dimensions, 
                        usage, 
                        benefits, 
                        price, 
                        selected_category, 
                        selected_subcategory, 
                        valid_image_files, 
                        is_active, 
                        token, 
                        api_url
                    )
                    if success:
                        st.session_state.show_product_form = False
                        time.sleep(0.5)  # Brief delay for better UX
                        st.experimental_rerun()
            
            if cancel:
                st.session_state.show_product_form = False
                st.experimental_rerun()
    
    # Simplified filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        filter_name = st.text_input("Filter products by name", placeholder="Enter product name")
    
    with col2:
        filter_category = st.selectbox(
            "Filter by Category",
            options=["All"] + list(category_map.values()),
            key="filter_prod_category"
        )
    
    with col3:
        filter_status = st.selectbox(
            "Status",
            options=["All", "Active", "Inactive"],
            key="filter_prod_status"
        )
    
    # Apply filters to the already fetched products
    filtered_products = all_products
    
    # Filter by name
    if filter_name:
        filtered_products = [p for p in filtered_products if filter_name.lower() in p.get("name", "").lower()]
    
    # Filter by category
    if filter_category != "All":
        # Find the category ID
        category_id = next((k for k, v in category_map.items() if v == filter_category), None)
        if category_id:
            filtered_products = [p for p in filtered_products if p.get("category_id") == category_id]
    
    # Filter by status
    if filter_status != "All":
        is_active = filter_status == "Active"
        filtered_products = [p for p in filtered_products if p.get("is_active", True) == is_active]
    
    # Show products count
    st.markdown(f"### Showing {len(filtered_products)} products")
    
    # Products table with edit/delete functionality
    if filtered_products:
        # Create a container for the table
        table_container = st.container()
        
        with table_container:
            # Table header
            header_cols = st.columns([0.15, 0.25, 0.15, 0.15, 0.1, 0.1, 0.1])
            with header_cols[0]:
                st.markdown("**Image**")
            with header_cols[1]:
                st.markdown("**Name**")
            with header_cols[2]:
                st.markdown("**Category**")
            with header_cols[3]:
                st.markdown("**Price**")
            with header_cols[4]:
                st.markdown("**Status**")
            with header_cols[5]:
                st.markdown("**Edit**")
            with header_cols[6]:
                st.markdown("**Delete**")
            
            st.markdown("---")
            
            # Table rows
            for product in filtered_products:
                # Check if this product is being edited
                is_editing = st.session_state.get(f"edit_product_{product.get('id')}", False)
                
                if is_editing:
                    # Replace "Edit form coming soon..." with actual edit form
                    with st.form(key=f"edit_product_form_{product.get('id')}"):
                        st.subheader(f"Edit Product: {product.get('name')}")
                        
                        # Product name input
                        name = st.text_input("Product Name", 
                                            value=product.get("name", ""),
                                            key=f"edit_prod_name_{product.get('id')}")
                        
                        # Description
                        description = st.text_area("Description", 
                                                value=product.get("description", ""),
                                                key=f"edit_prod_desc_{product.get('id')}")
                        
                        # Layout in columns
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Dimensions
                            dimensions = st.text_input("Dimensions", 
                                                    value=product.get("dimensions", ""),
                                                    key=f"edit_prod_dim_{product.get('id')}")
                            
                            # Category selection
                            current_category = product.get("category_id")
                            category_options = [(c.get("id"), c.get("name", "Unknown")) for c in categories]
                            
                            # Find the index of the current category
                            selected_category_index = 0
                            for i, (cat_id, _) in enumerate(category_options):
                                if cat_id == current_category:
                                    selected_category_index = i
                                    break
                            
                            if categories:
                                selected_category = st.selectbox(
                                    "Category",
                                    options=[opt[0] for opt in category_options],
                                    format_func=lambda x: next((name for id, name in category_options if id == x), "Unknown"),
                                    key=f"edit_prod_category_{product.get('id')}",
                                    index=selected_category_index
                                )
                            else:
                                st.error("No categories available.")
                                selected_category = None
                        
                        with col2:
                            # Price
                            price = st.number_input("Price", 
                                                 min_value=0.0, 
                                                 step=0.01, 
                                                 value=float(product.get("price", 0)),
                                                 key=f"edit_prod_price_{product.get('id')}")
                            
                            # Subcategory selection (depends on selected category)
                            subcategory_options = []
                            if selected_category and selected_category in subcategories_by_category:
                                subcategory_options = [(s.get("id"), s.get("name", "Unknown")) 
                                                    for s in subcategories_by_category[selected_category]]
                            
                            current_subcategory = product.get("subcategory_id")
                            
                            if subcategory_options:
                                # Include None option
                                options_list = ["None"] + [opt[0] for opt in subcategory_options]
                                
                                # Find the index of the current subcategory
                                selected_index = 0  # Default to "None"
                                for i, opt in enumerate(options_list):
                                    if opt == current_subcategory:
                                        selected_index = i
                                        break
                                
                                selected_subcategory = st.selectbox(
                                    "Subcategory (optional)",
                                    options=options_list,
                                    format_func=lambda x: "None" if x == "None" else next((name for id, name in subcategory_options if id == x), "Unknown"),
                                    key=f"edit_prod_subcategory_{product.get('id')}",
                                    index=selected_index
                                )
                                # Convert "None" string to None type
                                if selected_subcategory == "None":
                                    selected_subcategory = None
                            else:
                                st.write("No subcategories available for this category")
                                selected_subcategory = None
                        
                        # Usage
                        usage = st.text_area("Usage", 
                                           value=product.get("usage", ""),
                                           key=f"edit_prod_usage_{product.get('id')}")
                        
                        # Benefits
                        benefits = st.text_area("Benefits", 
                                              value=product.get("benefits", ""),
                                              key=f"edit_prod_benefits_{product.get('id')}")
                        
                        # Existing images
                        existing_images = product.get("image_urls", [])
                        if existing_images:
                            st.write("Existing Images:")
                            existing_cols = st.columns(min(5, len(existing_images)))
                            for i, img_url in enumerate(existing_images):
                                with existing_cols[i]:
                                    try:
                                        st.image(img_url, width=100, caption=f"Image {i+1}")
                                    except:
                                        st.write(f"Image {i+1} (URL error)")
                        
                        # Upload new images (up to 5 - existing count)
                        remaining_slots = max(0, 5 - len(existing_images))
                        
                        if remaining_slots > 0:
                            st.write(f"Upload New Images (up to {remaining_slots} more):")
                            st.caption("Recommended: 800x600 pixels, JPG/PNG format")
                            
                            image_cols = st.columns(remaining_slots)
                            new_image_files = []
                            
                            for i in range(remaining_slots):
                                with image_cols[i]:
                                    new_image_files.append(st.file_uploader(
                                        f"New Image {i+1}",
                                        type=["jpg", "jpeg", "png"],
                                        key=f"edit_prod_img_{product.get('id')}_{i}"
                                    ))
                            
                            # Preview new images
                            if any(new_image_files):
                                st.write("New Image Previews:")
                                preview_cols = st.columns(remaining_slots)
                                for i, img in enumerate(new_image_files):
                                    if img:
                                        with preview_cols[i]:
                                            st.image(img, width=100, caption=f"New Image {i+1}")
                        else:
                            st.info("Maximum number of images (5) already uploaded. Delete existing images to add new ones.")
                            new_image_files = []
                        
                        # Active toggle
                        is_active = st.checkbox("Product is active", 
                                              value=product.get("is_active", True),
                                              key=f"edit_prod_active_{product.get('id')}")
                        
                        # Form submission buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Product", use_container_width=True)
                        with col2:
                            cancel_button = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if update_button:
                            # Validate inputs
                            errors = []
                            if not name:
                                errors.append("Product name is required")
                            if not description:
                                errors.append("Product description is required")
                            if not selected_category:
                                errors.append("Category is required")
                            
                            if errors:
                                for error in errors:
                                    st.error(error)
                            else:
                                # Filter out None values from new_image_files
                                valid_image_files = [img for img in new_image_files if img is not None]
                                
                                success = update_product(
                                    product.get("id"),
                                    name, 
                                    description, 
                                    dimensions, 
                                    usage, 
                                    benefits, 
                                    price, 
                                    selected_category, 
                                    selected_subcategory, 
                                    valid_image_files, 
                                    is_active, 
                                    token, 
                                    api_url,
                                    existing_images=existing_images
                                )
                                if success:
                                    st.session_state[f"edit_product_{product.get('id')}"] = False
                                    st.experimental_rerun()
                        
                        if cancel_button:
                            st.session_state[f"edit_product_{product.get('id')}"] = False
                            st.experimental_rerun()
                else:
                    # Display product as a row
                    row_cols = st.columns([0.15, 0.25, 0.15, 0.15, 0.1, 0.1, 0.1])
                    
                    with row_cols[0]:
                        # Show first image thumbnail if available
                        if product.get("image_urls") and len(product["image_urls"]) > 0:
                            # Use a placeholder image if the URL doesn't load
                            try:
                                st.image(product["image_urls"][0], width=60)
                            except:
                                st.write("Image error")
                        else:
                            st.write("No image")
                    
                    with row_cols[1]:
                        st.write(product.get("name", "Unnamed"))
                    
                    with row_cols[2]:
                        # Get category and subcategory name
                        category_name = category_map.get(product.get("category_id"), "—")
                        subcategory_name = subcategory_map.get(product.get("subcategory_id"), "—")
                        
                        if subcategory_name != "—":
                            st.write(f"{category_name} / {subcategory_name}")
                        else:
                            st.write(category_name)
                    
                    with row_cols[3]:
                        # Format price with currency symbol
                        st.write(f"₹{product.get('price', 0):.2f}")
                    
                    with row_cols[4]:
                        if product.get("is_active", True):
                            st.markdown("✅ Active")
                        else:
                            st.markdown("❌ Inactive")
                    
                    with row_cols[5]:
                        if st.button("Edit", key=f"btn_edit_prod_{product.get('id')}"):
                            st.session_state[f"edit_product_{product.get('id')}"] = True
                            st.experimental_rerun()
                    
                    with row_cols[6]:
                        if st.button("Delete", key=f"btn_delete_prod_{product.get('id')}"):
                            # Show confirmation dialog
                            st.session_state[f"confirm_delete_prod_{product.get('id')}"] = True
                            st.experimental_rerun()
                
                # Handle confirmation dialog for deletion
                if st.session_state.get(f"confirm_delete_prod_{product.get('id')}", False):
                    st.warning(f"Are you sure you want to delete product '{product.get('name')}'?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete", key=f"confirm_yes_prod_{product.get('id')}"):
                            success = delete_product(product.get("id"), token, api_url)
                            if success:
                                st.session_state[f"confirm_delete_prod_{product.get('id')}"] = False
                                st.experimental_rerun()
                    with col2:
                        if st.button("Cancel", key=f"confirm_no_prod_{product.get('id')}"):
                            st.session_state[f"confirm_delete_prod_{product.get('id')}"] = False
                            st.experimental_rerun()
                
                # Add separator between rows
                st.markdown("---")
    else:
        # No products found
        st.info("No products found. Click '+ New Product' to add one.")

def upload_product_image(image_file, token: str, api_url: str) -> Optional[str]:
    """
    Upload a product image to the server.
    
    Args:
        image_file: The uploaded file from st.file_uploader
        token: JWT token for authorization
        api_url: Base URL of the API
        
    Returns:
        The URL of the uploaded image or None if upload failed
    """
    if not image_file:
        st.error("No image file provided")
        return None
    
    with st.spinner("Uploading image..."):
        try:
            # Prepare the files and headers for the request
            files = {"file": (image_file.name, image_file, "image/jpeg" if image_file.name.endswith(('.jpg', '.jpeg')) else "image/png")}
            headers = {"Authorization": f"Bearer {token}"}
            
            # Make the POST request to the upload endpoint
            response = requests.post(
                f"{api_url}/admin/upload-image",
                files=files,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data.get("url")
                st.success("Image uploaded successfully!")
                return image_url
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Failed to upload image: {error_detail}")
                st.write(f"Debug: Full response: {response.text[:500]}")
                return None
                
        except Exception as e:
            st.error(f"Error uploading image: {str(e)}")
            import traceback
            st.write(f"Debug: Exception traceback: {traceback.format_exc()}")
            return None