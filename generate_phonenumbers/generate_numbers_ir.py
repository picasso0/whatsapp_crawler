import phonenumbers
import motor.motor_asyncio
import asyncio
from phonenumbers import PhoneNumberType

def is_israeli_mobile_number(number):
    if phonenumbers.is_valid_number(number):
        number_type = phonenumbers.number_type(number)
        if number_type == PhoneNumberType.MOBILE:
            country_code = number.country_code
            if country_code == 972:  # Israel country code
                return True
    return False

async def generate_and_insert_numbers(prefix, collection, start=10000000, end=100000000):
    for i in range(start, end):
        number_str = f"+972{prefix}{i:07d}"
        number = phonenumbers.parse(number_str, "IL")
        print("_____________________")
        print(number)
        if is_israeli_mobile_number(number):
            formatted_number = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
            existing_number = await collection.find_one({"mobile": formatted_number})
            if not existing_number:
                await collection.insert_one({"mobile": formatted_number, "whatsapp_searching": 0})
                print(f"{formatted_number} inserted")
            else:
                print(f"{formatted_number} is existed")
        else:
            print("not il number")
            

async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
    db = client["gathering"]
    collection = db["profile"]

    mobile_prefixes = ["050", "051", "052", "053", "054", "055", "056", "057", "058", "059"]
    tasks = []

    for prefix in mobile_prefixes:
        task = asyncio.create_task(generate_and_insert_numbers(prefix, collection))
        tasks.append(task)

    await asyncio.gather(*tasks)

    client.close()

if __name__ == "__main__":
    asyncio.run(main())