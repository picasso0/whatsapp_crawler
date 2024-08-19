import phonenumbers
import motor.motor_asyncio
import asyncio
from phonenumbers import PhoneNumberType
from time import sleep

def is_israeli_mobile_number(number):
    if phonenumbers.is_valid_number(number):
        number_type = phonenumbers.number_type(number)
        if number_type == PhoneNumberType.MOBILE:
            country_code = number.country_code
            if country_code == 972:  # Israel country code
                return True
    return False

async def generate_and_insert_numbers(prefix, start=1000000, end=10000000):
    while(True):
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://77.238.108.86:27000/log?retryWrites=true&w=majority")
            db = client["gathering"]
            collection = db["profile"]
            for i in range(start, end):
                number_str = f"972{prefix}{i:06d}"
                number = phonenumbers.parse(number_str, "IL")
                # if is_israeli_mobile_number(number):
                #     formatted_number = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
                existing_number = await collection.find_one({"mobile": number_str})
                if not existing_number:
                    await collection.insert_one({"mobile": number_str, "whatsapp_searching": 0})
                    print(f"{number_str} inserted")
                sleep(0.1)
            client.close()
        except:
            pass
        
                

async def main():

    mobile_prefixes = ["56", "57", "58", "59","50", "51", "52", "53","54", "55",]
    tasks = []

    for prefix in mobile_prefixes:
        task = asyncio.create_task(generate_and_insert_numbers(prefix))
        tasks.append(task)

    await asyncio.gather(*tasks)

    client.close()

if __name__ == "__main__":
    asyncio.run(main())