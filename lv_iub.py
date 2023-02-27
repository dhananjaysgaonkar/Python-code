import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
from functions import ET
from selenium.webdriver.support.ui import Select

notice_count = 0 
MAX_NOTICES = 2000
script_name = "lv_iub"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Latvia'
    notice_data.contact_country = 'Latvia'
    notice_data.language = "LV"  
    notice_data.procurement_method = 'Other'
    notice_data.notice_type = 'spn'
    
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.c1'))).text
        notice_data.published_date = re.findall('\d+/\d+/\d{4}',notice_data.published_date)[0]
        try:
            notice_data.published_date = datetime.strptime(notice_data.published_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        except:
            notice_data.published_date = datetime.strptime(notice_data.published_date,'%m/%d/%Y').strftime("%Y/%m/%d")
        logging.info('published_date = '+notice_data.published_date)
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    if url[0] in url:
        type = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'.c2 div'))).text
        if type == 'Rezultāts':
            notice_data.notice_type = 'ca'
    elif urls[2] in url:
        notice_data.notice_type = 'ca'

    try:  
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.c5'))).text
        notice_data.end_date = re.findall('\d+/\d+/\d{4}',notice_data.end_date)[0]
        try:
            notice_data.end_date = datetime.strptime(notice_data.end_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        except:
            notice_data.end_date = datetime.strptime(notice_data.end_date,'%m/%d/%Y').strftime("%Y/%m/%d")
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.c1'))).text
        notice_data.reference = notice_data.reference.split('\n')[1]
    except:
        pass

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.c3'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.c4'))).text
    except:
        pass
    
    try:
        notice_data.cpvs.clear()
        cpvs = tender_html_element.find_element(By.CSS_SELECTOR,'div.c3').text
        cpv = re.findall("\d{8}\-\d{1}",cpvs)
        if cpv != '':
            for i in cpv:
                i=i.split('-')[0]
                notice_data.cpvs.append(i)
    except:
        try:
            notice_data.cpvs.clear()
            cpvs = tender_html_element.find_element(By.CSS_SELECTOR,'.c3 .name a:nth-of-type(2)').text
            if cpvs != '':
                for i in cpvs:
                    i=i.split('-')[0]
                    notice_data.cpvs.append(i)
        except:
            pass
    
    try:  
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.c3 > div.name > a.open_doc').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)        
        try: 
            notice_data.notice_text = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="open"]/section[2]'))).get_attribute('outerHTML')
        except:
            pass

    except:
        notice_data.notice_url = url
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

#-------------------------------------------
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:  
    urls = ['https://info.iub.gov.lv/meklet/pt/_pr/page/',
           'https://info.iub.gov.lv/meklet/pt/_disc/page/',
           'https://info.iub.gov.lv/meklet/pt/_pp/page/']
    
    for temp in urls:   
        for page_no in range(1,3):
            url = temp+str(page_no)
            fn.load_page(page_main, url)
            logging.info(url)
            for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/section/article/section[2]/section'))).find_elements(By.CSS_SELECTOR,'section.tr')[:1]:
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(script_name, notice_count, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log(script_name, e)
        fn.session_log(script_name, notice_count, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("europe") 