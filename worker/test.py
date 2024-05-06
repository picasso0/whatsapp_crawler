import requests

# Make a head request to a web page
response = requests.head("https://www.google.com")

# Get the user agent string from the response headers
user_agent = response.headers.get("User-Agent")

print(user_agent)