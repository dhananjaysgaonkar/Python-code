import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
import ml.cpv_classifier as classifier
from false_cpv import false_cpv
from functions import ET
from selenium.webdriver.support.ui import Select

notice_count = 0
MAX_NOTICES = 2000

script_name = "mx_cespt"
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
    notice_data.buyer_internal_id = "7782715"
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-of-type(2)'))).text
        notice_data.title_en = GoogleTranslator(source='es', target='en').translate(title_en)
    except:
        pass
    logging.info(notice_data.title_en)
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(1)').text       
    except:
        pass
    logging.info(notice_data.reference)   
     
    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(3)').text
        notice_data.published_date = GoogleTranslator(source='auto', target='en').translate(notice_data.published_date)
        try:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%d/%b/%Y').strftime('%Y/%m/%d')
        except:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%b/%d/%Y').strftime('%Y/%m/%d')
    except:
        pass
    logging.info(notice_data.published_date)
            
    try:
        notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(5)').text 
        notice_data.end_date = notice_data.end_date[:-11]
        notice_data.end_date = GoogleTranslator(source='auto', target='en').translate(notice_data.end_date)
        notice_data.end_date  = datetime.strptime(notice_data.end_date ,'%d/%b/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)
    except:
        try:
            end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
            notice_data.end_date = end_date.strftime('%Y/%m/%d')
            logging.info(notice_data.end_date)
        except:
            pass 
  
    try:
        notice_data.buyer = 'Tijuana State Public Services Commission'
    except:
        pass
    logging.info(notice_data.buyer)
    
    try:
        notice_data.awarding_company_address = 'Blvd. Federico Benítez No. 4057, Col. 20 de Noviembre Tijuana, BCCP 22430'
        logging.info(notice_data.awarding_company_address)
    except:
        pass
    
    try:
        rsrs = tender_html_element.find_elements(By.CSS_SELECTOR,'td.titItems4 a')
        notice_data.resource_url.clear()
        for rsr in rsrs:
            resource = rsr.get_attribute('href')
            notice_data.resource_url.append(resource)
        logging.info(notice_data.resource_url)
    except:
        pass
        
    common.NoticeData.NoticeData.cleanup(notice_data)

    notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
    logging.info(notice_data.cpvs)

    if notice_data.published_date < threshold:
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
    url = 'https://www.cespt.gob.mx/TransLicConv/Licitaciones.aspx'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_licita"]/table[2]/tbody').find_elements(By.CSS_SELECTOR,'tr'):
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