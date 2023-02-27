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
script_name = "il_mod_gov"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Israel'
    notice_data.buyer_internal_id = '7591473'
    notice_data.contact_country = 'Israel'
    notice_data.language = 'HE'  
    notice_data.notice_type = "spn"
    notice_data.buyer = 'MINISTRY OF DEFENCE (MOD)'
    
    try:
        published_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.published_date = datetime.strptime(published_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info('published_date '+notice_data.published_date)
    except:
        pass
    
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
    except:
        pass

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info('title_en '+notice_data.title_en)
    except:
        pass
    
    if('expression of interest' in notice_data.title_en.lower() or 'eoi' in notice_data.title_en.lower()):
        notice_data.notice_type = 'rei'
    else:
        notice_data.notice_type = 'spn'
    
    try:
        notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.end_date = notice_data.end_date.split(' ')[1]
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        pass
    
    notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
    
    if notice_data.title_en is not None :
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)
        
    notice_data.cleanup()

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

#-------------------------------------------
page_main = fn.init_chrome_driver()
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:  
    url = 'https://www.online.mod.gov.il/Online2016/Pages/General/Balam/BalamList.aspx?Reset=1'
    fn.load_page(page_main, url)
    logging.info(url)    
    
    for page_no in range(2,5):
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_gvBalam"]/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:4]:
            page_check = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        try:
            nxt_page = page_main.find_element(By.LINK_TEXT,str(page_no)).click()        
            logging.info("---Next Page "+str(page_no)+"---")
            WebDriverWait(tender_html_element, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'td:nth-child(2)'),page_check))
        except:
            logging.info("No Next Page")
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
    output_xml_file.copyFinalXMLToServer("middle_east") 
