import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_custom_user_creation():
    """Test that we can create a custom user successfully."""
    user = User.objects.create_user(
        username="testfarmer",
        email="farmer@example.com",
        password="securepassword123"
    )
    
    assert user.username == "testfarmer"
    assert user.email == "farmer@example.com"
    assert user.check_password("securepassword123") is True
    assert user.is_active is True
