import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
from functions import ET

notice_count = 0 
MAX_NOTICES = 2000
script_name = "il_betshemesh"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Israel'
    notice_data.contact_country = 'Israel'
    notice_data.procurement_method = "Other"
    notice_data.language = "HE"  
    notice_data.buyer_internal_id = "7636991"
    notice_data.buyer = 'ISRAEL AIRPORTS AUTHORITY'
    
    
    try:
        published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(3)"))).text
        published_date = GoogleTranslator(source='auto', target='en').translate(published_date)
        notice_data.published_date = datetime.strptime(published_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info("published_date " +notice_data.published_date)
    except:
        pass
            
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(1)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        if('expression of interest' in notice_data.title_en.lower() or 'eoi' in notice_data.title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
    except:
        pass

    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(4)"))).text
        GoogleTranslator(source='auto', target='en').translate(end_date)
        notice_data.end_date = datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y/%m/%d')   
    except:
        pass
        
    try:  
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div/div/main'))).get_attribute('outerHTML')
        except:
            pass 
    except:
        notice_data.notice_url = url

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
    url = 'https://www.betshemesh.muni.il/bids/'
    fn.load_page(page_main, url)
    logging.info(url)
    
    WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[5]/div/div/div/main/h2[1]/i'))).click()

    for tender_html_element in WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="bids_div_1"]/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[1:]:
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
    output_xml_file.copyFinalXMLToServer("middle_east") 