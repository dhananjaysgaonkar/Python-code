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
script_name = "gh_tenders"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Ghana'
    notice_data.contact_country = 'Ghana'
    notice_data.procurement_method = "Other"
    notice_data.language = "EN"  
    notice_data.notice_type = "spn"
    
    try:
        published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div > div > p > span.text-success"))).text
        notice_data.published_date = datetime.strptime(published_date, '%b %d, %Y   ').strftime("%Y/%m/%d")
        logging.info('published_date '+notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try: 
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        
        
        try:
            notice_data.notice_text =  WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tender-details"]'))).get_attribute('outerHTML')
        except:
            pass 
    except:
        notice_data.notice_url = url
        
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#track-tender"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, " div:nth-child(2) > p > span"))).text
        
    except:
        pass

    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, " div > div > p > span.text-danger"))).text
        notice_data.end_date = datetime.strptime(end_date, '%b %d, %Y').strftime("%Y/%m/%d")
         
    except:
        pass        
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)
        
    notice_data.cleanup()

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
    for page_no in range(1,5):
        url = 'https://tenders.com.gh/tenders/lists/'+str(page_no)
        fn.load_page(page_main, url)
        logging.info(url)
        
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="myListType"]').find_elements(By.CSS_SELECTOR,'li'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
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
    output_xml_file.copyFinalXMLToServer("africa") 