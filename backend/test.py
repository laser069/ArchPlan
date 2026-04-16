import requests
from bs4 import BeautifulSoup
url = 'https://google.com'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
headings = soup.find_all('div')
for heading in headings:
    print(heading.text.strip()) 