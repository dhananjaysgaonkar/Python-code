import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
from functions import ET
from selenium.webdriver.support.ui import Select

notice_count = 0
MAX_NOTICES = 2000

script_name = "mx_donaanacounty"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data 
    notice_data = NoticeData() 
    
    notice_data.performance_country = 'Mexico'
    notice_data.contact_country = 'Mexico'
    notice_data.procurement_method = "Other"
    notice_data.language = "MX"  
    notice_data.notice_type = "spn"
    notice_data.buyer = 'Dona Ana County'
    notice_data.buyer_internal_id = "7366363"
 
    try: 
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
        notice_data.title_en = GoogleTranslator(source='es', target='en').translate(title_en)
    except:
        pass
    logging.info(notice_data.title_en)
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text       
    except:
        pass
    logging.info(notice_data.reference)   
 
    try:
        end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text 
        end_date = GoogleTranslator(source='auto', target='en').translate(end_date)
        end_date = re.findall('\w+ \d+, \d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(end_date ,'%B %d, %Y').strftime('%Y/%m/%d')
    except:
        pass
    logging.info(notice_data.end_date)
 
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    logging.info(notice_data.category)
    
    notice_data.notice_url = url
    logging.info(notice_data.notice_url)

    notice_data.cleanup()

    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)
        logging.info(notice_data.cpvs)
    
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

#-------------------------------------------

page_main = fn.init_chrome_driver()
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:              
    url = 'https://www.donaanacounty.org/bids'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="block-views-bids-block"]/div/div/div/div/table/tbody').find_elements(By.CSS_SELECTOR,'tr'):
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(script_name, notice_count, 0, 'XML uploaded')
    
except Exception as e:
    try:
        fn.error_log(script_name, e)
        fn.session_log(script_name, notice_count, 0, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    output_xml_file.copyFinalXMLToServer("latin") 
