import itertools
import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
db = client.gathering

# Define the prefix for Israeli mobile numbers
prefix = "9725"

# Define the length of the remaining digits
length = 8

# Generate all possible combinations of the remaining digits
digits = [str(i) for i in range(10)]
combinations = [''.join(combo) for combo in itertools.product(digits, repeat=length)]

# Combine the prefix and the remaining digits to form the complete phone numbers
phone_numbers = [prefix + combo for combo in combinations]
# Print the generated phone numbers
for number in phone_numbers:
    db.profile.insert_one({"mobile":number})



# FOR IRAN

# import random




# client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
# db = client.gathering
# # Define the format of the Iranian mobile numbers
# mobile_format = "98919{:07d}"

# # Generate 100 random phone numbers
# phone_numbers = [mobile_format.format(random.randint(0, 9999999)) for _ in range(1000)]
# breakpoint()
# # Print the phone numbers
# for phone_number in phone_numbers:
#     db.profile.insert_one({"mobile":phone_number})
