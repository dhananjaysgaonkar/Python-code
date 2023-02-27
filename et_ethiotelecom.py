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
script_name = "et_ethiotelecom"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Ethiopia'
    notice_data.contact_country = 'Ethiopia'
    notice_data.language = "EN"  
    notice_data.notice_type = "spn"
    notice_data.buyer = 'Ethio Telecom'
    notice_data.buyer_internal_id = '7784532'

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div > div > div > header > h2"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info("title_en " +notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div > div > header > div'))).text
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info("end_date " +notice_data.published_date)
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    if notice_data.title_en.__contains__('NCB' or 'National Competitive Bid'):
        notice_data.procurement_method = 'National'
        logging.info('notice_data.procurement_method '+notice_data.procurement_method )
    elif notice_data.title_en.__contains__( 'ICB' or 'International Competitive Bid'):
        notice_data.procurement_method = 'International'
        logging.info('notice_data.procurement_method '+notice_data.procurement_method )
    else:
        notice_data.procurement_method = "Other"
        
    if notice_data.title_en.__contains__('Notification of bid cancelation'):
        notice_data.update = True
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > header > h2 > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info("notice_url " +notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        try:
            notice_data.reference = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div/section/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div/div/section/div/div/div/div/div/div/div/div/p[1]'))).text
            notice_data.reference = notice_data.reference.split('RFQ No.')[1]
            logging.info('reference '+notice_data.reference)
        except:
            notice_data.reference = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div/section/div[2]/div/div[1]/div/div[2]/div[3]/div/div/div/div/section/div/div/div/div/div/div/div/div/p[2]'))).text
            notice_data.reference = notice_data.reference.split('RFQ No.')[1]
            logging.info('reference '+notice_data.reference)
    except:
        pass
      
    try:
        notice_data.notice_text =  page_details.find_element(By.XPATH, '//*[@id="main"]/div/div/section/div[2]/div/div[1]/div/div[2]/div[3]').get_attribute('outerHTML')
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
    url = 'https://www.ethiotelecom.et/tender/'
    fn.load_page(page_main, url)
    logging.info(url)
    
    for load_more in range(1,4):
        try:    
            WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="eael-load-more-btn-7ae4d29"]/span'))).click()
        except:
            break
            
    time.sleep(15)    

    for tender_html_element in WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="eael-post-block-7ae4d29"]/div'))).find_elements(By.CSS_SELECTOR,'article'):
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
