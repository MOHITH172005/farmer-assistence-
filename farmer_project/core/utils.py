import random
import string
from .models import FarmerProfile
def generate_farmer_ids(count=3):
    ids = []

    while len(ids) < count:
        new_id = "FRM" + "".join(random.choices(string.digits, k=6))

        # check DB uniqueness
        if not FarmerProfile.objects.filter(farmer_id=new_id).exists():
            if new_id not in ids:
                ids.append(new_id)

    return ids
