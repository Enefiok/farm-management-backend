import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_golden_path_auth_to_farm_to_item():
    """
    Proves the entire Sprint 2 flow works:
    1. User registers and gets an Account.
    2. User logs in.
    3. User creates a Farm (and gets Owner role).
    4. User creates an Item in that Farm's catalog.
    """
    client = APIClient()

    # 1. Register
    reg_payload = {
        "email": "testfarmer@example.com",
        "full_name": "Test Farmer",
        "password": "SecurePassword123!",
        "password2": "SecurePassword123!"
    }
    reg_response = client.post('/api/auth/register/', reg_payload)
    assert reg_response.status_code == 201, f"Registration failed: {reg_response.content}"
    
    # 2. Login
    login_payload = {"email": "testfarmer@example.com", "password": "SecurePassword123!"}
    login_response = client.post('/api/auth/login/', login_payload)
    assert login_response.status_code == 200, f"Login failed: {login_response.content}"

    # 3. Create Farm
    farm_payload = {"name": "Green Valley Poultry", "location": "Lagos", "contact_info": "08012345678"}
    farm_response = client.post('/api/farms/', farm_payload)
    assert farm_response.status_code == 201, f"Farm creation failed: {farm_response.content}"
    
    # Extract the farm ID from the response
    farm_id = farm_response.data['farm']['id']

    # 4. Create an Item in the Catalog (Scoped to the new Farm)
    item_payload = {
        "name": "Layer Mash", 
        "category": "FEED", 
        "base_unit": "bag", 
        "is_stock_tracked": True
    }
    # Notice we use the farm_id in the URL, not in the JSON body!
    item_response = client.post(f'/api/farms/{farm_id}/items/', item_payload)
    assert item_response.status_code == 201, f"Item creation failed: {item_response.content}"
    
    # Verify the item was actually saved to the database
    from apps.catalog.models import Item
    assert Item.objects.filter(name="Layer Mash", farm_id=farm_id).exists()