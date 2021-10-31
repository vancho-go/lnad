import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging
import sys
from datetime import datetime
import shutil

# Setup logger
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("lnad_loader")
logging.getLogger("chardet.charsetprober").disabled = True
logging.getLogger("chardet.universaldetector").disabled = True

#Delete unnecessary logs
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

url = ''
headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36.'}
auth = ('can02', 'can020519')

now = datetime.now().strftime('%d%m%y%H%M%S')

folder_location = f'/home/user/Downloads/adb.org_{now}'
if not os.path.exists(folder_location):os.mkdir(folder_location)

def load_last_downloaded_filename():
    with open ('log.txt', 'r') as logfile:
        name = logfile.read()
        return name

def get_links(url):
    response = requests.get(url, auth = auth, headers = headers)
    soup = BeautifulSoup(response.text, "html.parser") 

    #Find all links on page
    links = [link['href'] for link in soup.select('td > a.xspLink[href]')]
    links_edited = []
    for link in links[0:4]:
        if 'adb.org' in link:
            link = link.replace('https', 'http')
            links_edited.append(link)
        else:
            link = 'http://adb.org' + link
            links_edited.append(link)
    return links_edited

def get_redirected_link(link):
    response = requests.get(link, auth = auth, headers = headers)
    soup = BeautifulSoup(response.text,  "html.parser")  
    element = soup.find('meta', attrs={'http-equiv': 'refresh'})
    refresh_content = element['content']
    redirected_link = refresh_content.partition('=')[2]
    return redirected_link

def log_last_downloaded_file(filename):
    logger.info(f'Downloaded file - {filename}')
    with open('log.txt', 'a') as logfile:
        logfile.write(filename + '\n')

def download_pdf(link):
    filename = os.path.join(folder_location,link.split('/')[-1])
    with open(filename, 'wb') as f:
        f.write(requests.get(urljoin(url,link), headers = headers, auth = auth, verify=False).content)

def get_already_downloaded_links():
    with open ('log.txt', 'r') as logfile:
        result = list(logfile.read().split('\n'))
    return result[:len(result)-1]

def clear_logfile(already_downloaded_links):
    if len(already_downloaded_links) > 40:
        already_downloaded_links = already_downloaded_links[len(already_downloaded_links)-40:]
        with open ('log.txt', 'w') as logfile:
            for link in already_downloaded_links:
                logfile.write(link + '\n')
    else:
        logger.info('Logfile is not overflowed')


if __name__ == "__main__":

    # Loading log file (links)
    already_downloaded_links = get_already_downloaded_links()
    links = get_links(url)

    # Downloading PDFs
    for link in links:
        if not link in already_downloaded_links:
            redirected_link = get_redirected_link(link)
            download_pdf(redirected_link)
            log_last_downloaded_file(link)
            already_downloaded_links.append(link)
        else:
            logger.info(f'Link {link} was already downloaded')

    # Zip folder
    shutil.make_archive(folder_location, 'zip', folder_location)
    shutil.rmtree(folder_location)    

    # Removing old links from logfile
    clear_logfile(already_downloaded_links)