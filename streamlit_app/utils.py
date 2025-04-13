def confirm_delete_dialog(item_type, item_name):
    """Create a confirmation dialog for delete operations"""
    confirm_col, cancel_col = st.columns(2)
    
    with st.container(border=True):
        st.warning(f"Are you sure you want to delete {item_type}: **{item_name}**?")
        st.caption("This action cannot be undone.")
        
        with confirm_col:
            confirm = st.button("Yes, Delete", key=f"confirm_delete_{item_name}", use_container_width=True)
        with cancel_col:
            cancel = st.button("Cancel", key=f"cancel_delete_{item_name}", use_container_width=True)
    
    return confirm, cancel 