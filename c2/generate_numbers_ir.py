import random
from db import get_database
import motor.motor_asyncio



client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
db = client.gathering
# Define the format of the Iranian mobile numbers
mobile_format = "98919{:07d}"

# Generate 100 random phone numbers
phone_numbers = [mobile_format.format(random.randint(0, 9999999)) for _ in range(1000)]
breakpoint()
# Print the phone numbers
for phone_number in phone_numbers:
    db.profile.insert_one({"mobile":phone_number})
