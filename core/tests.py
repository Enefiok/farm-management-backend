from django.test import TestCase
from core.models import BaseModel

class BaseModelTests(TestCase):
    def test_base_model_is_abstract(self):
        """Ensure BaseModel does not create its own database table."""
        self.assertTrue(BaseModel._meta.abstract)

    def test_base_model_has_required_fields(self):
        """Ensure BaseModel enforces SRS 7.3 and SRS 11 fields."""
        self.assertTrue(hasattr(BaseModel, 'event_date'))
        self.assertTrue(hasattr(BaseModel, 'entry_timestamp'))
        self.assertTrue(hasattr(BaseModel, 'classification'))
        self.assertTrue(hasattr(BaseModel, 'created_by'))