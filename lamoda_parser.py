import requests
from bs4 import BeautifulSoup
import smtplib
From lamoda_info import urls, HEADERS, SENDER, ADDRESSEE, PASSWORD

# get links along with the threshold from txt file


def get_title(link):
    page = requests.get(link, headers=HEADERS)
    souped = BeautifulSoup(page.text, 'lxml')
    brand = souped.find('span', itemprop="brand").string
    # item_name = souped.find("div", {"class": "product-title__model-name"}).string
    # item_name_ascii = item_name[item_name.find(' ')+1:]
    # return f'{item_name_ascii} ({brand.upper()})'     # output: 'Forever Floatride (REEBOK)'
    return brand


def get_price(link):
    page = requests.get(link, headers=HEADERS)
    souped = BeautifulSoup(page.text, 'lxml')
    # checking if the item is on sale and searching in different sections of the code
    if souped.find(itemprop="price").string is not None:
        price = int(souped.find(itemprop="price").string[:-2].replace(' ', ''))
    else:
        # the discount price is javascript rendered -> pull data from another location
        item_data = str(souped.find('script', {'data-module': "statistics"}))
        endofstr_pos = item_data.find('currency: ')
        # extracting and formatting the price
        price = int(
            item_data[
            item_data.find('current: ')+10:endofstr_pos-9
            ].replace("'", '')
        )
    # return f'{price:,} ({if_disc})'
    return price


def get_sizes_nondisc(link):
    page = requests.get(link, headers=HEADERS)
    souped = BeautifulSoup(page.text, 'lxml')
    sizes_code = str(souped.find('div', class_='product__select-notes'))
    sizes_string = ''
    try:
        string = sizes_code[sizes_code.find('[[')+2:sizes_code.find(']]')]
        list1 = string.split('],[')
        list2 = []
        sizes_dic = {}
        list_available_sizes = []
        for set in list1:
            list2.append(set.split(', '))
        for index in range(len(list2)):
            is_available, sizeRus, sizeOther = list2[index][0], list2[index][2][1:-1], list2[index][3][1:-1]
            sizes_dic[f'{sizeRus} ({sizeOther})'] = is_available
        for key in sizes_dic.keys():
            if sizes_dic[key] == 'true':
                # list_available_sizes.append(key)
                sizes_string += key + '\n'
    except:
        # list_available_sizes = 'could not find available sizes'
        sizes_string = 'could not load the sizes'
    return sizes_string


def send_email(link):
    subject = "lamoda items on sale"
    mailtext='Subject:'+subject\
             +'\n\n' \
             + get_title(link) + link\
             + '\n' \
             + str(get_price(link)) \
             + '\n' \
             + 'sizes available:\n' \
             + get_sizes_nondisc(link) \
             + '\n' \
             + '_'*50

    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.ehlo()
    server.starttls()
    server.login(SENDER, PASSWORD)
    server.sendmail(SENDER, ADDRESSEE, mailtext)
    pass


for line in urls:
    threshold, URL = int(line.split(' = ')[0]), line.split(' = ')[1].strip()
    if get_price(URL) <= threshold:
        send_email(URL)
    print('done')
