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

script_name = "mx_diputados"
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
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    except:
        pass
    logging.info(notice_data.reference)
        
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-of-type(2)'))).text
        notice_data.title_en = GoogleTranslator(source='es', target='en').translate(title_en)
    except:
        pass
    logging.info(notice_data.title_en)
 
    try:
        notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(4)').text 
        notice_data.end_date  = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)
    except:
        try:
            end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
            notice_data.end_date = end_date.strftime('%Y/%m/%d')
            logging.info(notice_data.end_date)
        except:
            pass 
        
    try:
        WebDriverWait(tender_html_element, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "td:nth-of-type(1)"))).click()
    except:
        pass
        
    try:
        notice_data.published_date = page_main.find_element(By.XPATH,'//*[@id="fecha_publicacion"]').text
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
    except:
        pass
    logging.info(notice_data.published_date)
    
    try:
        notice_data.buyer = 'Av. Congreso de la Unión'
    except:
        pass
    logging.info("buyer= "+notice_data.buyer)
    
    try:
        notice_data.awarding_company_address = ' No. 66. Col. El Parque Del. Venustiano Carranza, CP 15960, Mexico City'
        logging.info(notice_data.awarding_company_address)
    except:
        pass
            
    try:
        rsrs = page_main.find_elements(By.CSS_SELECTOR,'td.calendar a')
        notice_data.resource_url.clear()
        for rsr in rsrs:
            resource = rsr.get_attribute('href')
            notice_data.resource_url.append(resource)
        logging.info(notice_data.resource_url)
    except:
        pass

    try:
        notice_data.notice_text = page_main.find_element(By.XPATH,'//*[@id="vigentesContent"]').text
    except:
        common.NoticeData.NoticeData.cleanup(notice_data)
        
    try:
        WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="ui-button-icon ui-icon ui-icon-closethick"]'))).click()
    except:
        pass

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
    url = 'http://pac.diputados.gob.mx/Home/Vigentes#'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="vigentes"]/tbody').find_elements(By.CSS_SELECTOR,'tr'):
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