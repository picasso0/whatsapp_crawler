import motor.motor_asyncio
import asyncio

async def generate_numbers(prefix, length):
    digits = [str(i) for i in range(10)]
    
    async def generate_combinations(current_combo=""):
        if len(current_combo) == length:
            yield prefix + current_combo
        else:
            for digit in digits:
                async for number in generate_combinations(current_combo + digit):
                    yield number
    
    async for number in generate_combinations():
        yield number

async def insert_numbers(numbers, db):
    async for number in numbers:
        await db.profile.insert_one({"mobile": number, "whatsapp_searching": 0})

async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
    db = client["gathering"]
    prefix = "9725"
    length = 8

    numbers = generate_numbers(prefix, length)
    await insert_numbers(numbers, db)

if __name__ == "__main__":
    asyncio.run(main())

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
