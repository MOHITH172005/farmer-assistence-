# core/utils.py
import random
from .models import FarmerProfile

def generate_farmer_ids(count=3):
    """
    Generate unique farmer IDs like FARM123456
    """
    ids = set()

    while len(ids) < count:
        new_id = f"FARM{random.randint(100000, 999999)}"
        if not FarmerProfile.objects.filter(farmer_id=new_id).exists():
            ids.add(new_id)

    return list(ids)
