import requests
from bs4 import BeautifulSoup
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import time
import datetime
import pickle

from login_file import *

url = 'http://humanepa.org/adoption/dogs/'
adoption_page = requests.get(url)
soup = BeautifulSoup(adoption_page.content, 'html.parser')

lancaster_dogs = []
dog_dict = {}
new_dogs = []
adopted_dogs = []
jpegs = []

def scrape_captions(): # scrapes all captions from adoption page
    caption_data = soup.find_all('dd') # finds all dog name headers
    for item in caption_data:
        if 'Lancaster' in str(item):
            lancaster_dogs.append(item.string)

def get_dogs(): # creates dictionary of dog names and status
    for item in lancaster_dogs:
        if 'adopted' in item.lower():
            name = item[item.find(' '):item.find('(')]
            dog_dict.update({name.strip(): 'adopted'})
        else:
            name = item[:item.find('(')]
            dog_dict.update({name.strip(): 'available'})

def compare_to_current_file():
    with open('dogdict.txt', 'rb') as f:
        current_file = pickle.load(f)
        print(current_file)
        for key, value in dog_dict.items():
            if key not in current_file:
                new_dogs.append(key)
                download_images(key)
                send_email(key, 'New Dog Available!')
            elif key in current_file and value != current_file[key]:
                adopted_dogs.append(key)
                download_images(key)
                send_email(key, 'New Adoption!')

def save_names():  # writes dog_dict to a file
    with open('dogdict.txt', 'wb') as f:
        pickle.dump(dog_dict, f, pickle.HIGHEST_PROTOCOL)

def download_images(dog): #downloads images from site
    for link in soup.find_all('img'):
        if dog in str(link):
            image = link.get('src')
            image_name = os.path.split(image)[1]
            r2 = requests.get(image)
            jpegs.append(image_name)
            with open(image_name, 'wb') as f:
                f.write(r2.content)

def send_email(dog, subject):
    msg = MIMEMultipart()
    message = str(''.join(dog))
    msg['From'] = 'Humane League'
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'html'))
    for jpeg in jpegs:
        fp = open(jpeg, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()
        msg.attach(msgImage)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email, password)
    server.send_message(msg)
    server.quit()

while True: #starts timed loop (60 min)
    print(datetime.datetime.now())
    scrape_captions()
    get_dogs()
    compare_to_current_file()
    save_names()
    time.sleep(3600)