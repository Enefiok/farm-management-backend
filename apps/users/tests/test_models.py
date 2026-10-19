import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_custom_user_creation():
    """Test that we can create a custom user successfully with email and full_name."""
    user = User.objects.create_user(
        email="farmer@example.com",
        full_name="Test Farmer",
        password="securepassword123"
    )
    assert user.email == "farmer@example.com"
    assert user.full_name == "Test Farmer"
    assert user.check_password("securepassword123")
    assert user.is_active is True
    assert user.is_staff is False

@pytest.mark.django_db
def test_custom_superuser_creation():
    """Test that we can create a custom superuser successfully."""
    superuser = User.objects.create_superuser(
        email="admin@example.com",
        full_name="Admin User",
        password="adminpassword123"
    )
    assert superuser.email == "admin@example.com"
    assert superuser.full_name == "Admin User"
    assert superuser.is_active is True
    assert superuser.is_staff is True
    assert superuser.is_superuser is True