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

HUMANE_URL = 'http://humanepa.org/adoption/dogs/'

def load_scraper(url):
    adoption_page = requests.get(url)
    return BeautifulSoup(adoption_page.content, 'html.parser')

def scrape_captions(soup): # scrapes all captions from adoption page
    lancaster_dogs = []
    caption_data = soup.find_all('dd') # finds all dog name headers
    for item in caption_data:
        if 'Lancaster' in str(item):
            lancaster_dogs.append(item.string)
    return lancaster_dogs

def get_dogs(names): # creates dictionary of dog names and status
    dog_dict = {}
    for item in names:
        if 'adopted' in item.lower():
            name = item[item.find(' '):item.find('(')]
            dog_dict.update({name.strip(): 'adopted'})
        else:
            name = item[:item.find('(')]
            dog_dict.update({name.strip(): 'available'})
    return dog_dict

def compare_to_current_file(soup, dict):
    new_dogs = []
    adopted_dogs = []
    with open('dogdict.txt', 'rb') as f:
        current_file = pickle.load(f)
        print('current file: ', current_file)
        for key, value in dict.items():
            if key not in current_file:
                new_dogs.append(key)
                jpegs = download_images(soup, key)
                send_email(key, 'New Dog Available!', jpegs)
            elif key in current_file and value != current_file[key]:
                adopted_dogs.append(key)
                jpegs = download_images(soup, key)
                send_email(key, 'New Adoption!', jpegs)

def save_names(dict):  # writes dog_dict to a file
    with open('dogdict.txt', 'wb') as f:
        pickle.dump(dict, f, pickle.HIGHEST_PROTOCOL)

def download_images(soup, dog): #downloads images from site
    jpegs = []
    for link in soup.find_all('img'):
        if dog in str(link):
            image = link.get('src')
            image_name = os.path.split(image)[1]
            r2 = requests.get(image)
            jpegs.append(image_name)
            with open(image_name, 'wb') as f:
                f.write(r2.content)
    return jpegs

def send_email(dog, subject, jpegs):
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

def main():
    print(datetime.datetime.now())
    soup = load_scraper(HUMANE_URL)
    names = scrape_captions(soup)
    dict = get_dogs(names)
    compare_to_current_file(soup, dict)
    save_names(dict)

while True: #starts timed loop
    main()
    time.sleep(14400) #4 hours