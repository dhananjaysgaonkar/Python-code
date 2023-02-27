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
notice_data = NoticeData() 
MAX_NOTICES = 2000

script_name = "cn_wsd"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    wait = WebDriverWait(page_main, 10)  
    
    notice_data.performance_country = 'China'
    notice_data.contact_country = 'China'
    notice_data.procurement_method = "Other"
    notice_data.language = "CN"  
    notice_data.notice_type = "spn"
    
    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(3) > a').get_attribute('href')
        logging.info("Processing page: {} ...".format(page_details_url))
        temp= page_details.get(page_details_url)
        logging.info("page_details_url " +temp)
    except:
        page_details_url = ""
        
    try:
        title_en = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Subject :")]//following::td'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        notice_data.title_en = 'Please refer to notice details'
    logging.info("title_en= " +notice_data.title_en)
    
    try:
        notice_data.reference = page_details.find_element(By.XPATH,'//*[contains(text(), "Tender Reference :")]//following::td').text
        try:
            notice_data.reference = notice_data.reference.split("Contract No. ")[1]
        except:
            notice_data.reference = page_details.find_element(By.XPATH,'//*[contains(text(), "Tender Reference :")]//following::td').text         
    except:
        notice_data.reference = 'Please refer to notice details'
    logging.info("reference= "+notice_data.reference)   
    
    try:
        notice_data.buyer = page_details.find_element(By.XPATH, '//*[contains(text(), "Procuring Department :")]//following::td').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
    except:
        notice_data.buyer = 'Please refer to notice details'
    logging.info("buyer= "+notice_data.buyer)
        
    try:
        notice_data.published_date = page_main.find_element(By.CSS_SELECTOR,'td:nth-of-type(1)').text
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y / %m / %d').strftime('%Y/%m/%d')
    except:
        notice_data.published_date = threshold
    logging.info("published_date= "+notice_data.published_date)
            
    try:
        notice_data.end_date = page_details.find_element(By.XPATH, '//*[contains(text(), "Closing Date / Time :")]//following::td').text 
        notice_data.end_date = notice_data.end_date.split(", ")[1]
        notice_data.end_date  = datetime.strptime(notice_data.end_date ,'%d %B %Y').strftime('%Y/%m/%d')
        logging.info("end_date= "+notice_data.end_date)
    except:
        try:
            end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
            notice_data.end_date = end_date.strftime('%Y/%m/%d')
            logging.info("end_date= "+notice_data.end_date)
        except:
            pass 
        
    try:
        notice_data.address = page_details.find_element(By.XPATH, '//*[contains(text(), "Contact :")]//following::td').text
        notice_data.address = GoogleTranslator(source='auto', target='en').translate(notice_data.address)
    except:
        notice_data.buyer = 'Please refer to notice details'
    logging.info("address= "+notice_data.address)

    try:
        notice_data.notice_text = page_details.find_element(By.XPATH,'//*[@id="content"]').text
#         logging.info(notice_data.notice_text)
    except:
        notice_data.notice_text=''
        notice_data.notice_text += notice_data.buyer 
        notice_data.notice_text += '</br>'
        notice_data.notice_text = 'Title:'
        notice_data.notice_text += notice_data.title_en
        notice_data.notice_text += '</br>'
        notice_data.notice_text += 'Published Date : '
        notice_data.notice_text += notice_data.published_date
        notice_data.notice_text += '</br>'
        notice_data.notice_text += 'Reference No : '
        notice_data.notice_text += notice_data.reference
        notice_data.notice_text += '</br>'
        
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('---------------------------------')

    fn.assign_cpvs_from_title(notice_data.title_en,notice_data.ml_cpv) 
    logging.info(notice_data.cpvs)

#     if notice_data.published_date < threshold:
#         return
#     if notice_data.end_date < threshold:
#         return
    
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

#-------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:              
    url = 'https://www.wsd.gov.hk/en/tenders-contracts-and-consultancies/contracts/tender/index.html'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="content"]/div[1]/table/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(script_name, notice_count, 0, notice_data.ml_cpv[0], 'XML uploaded')
    
except Exception as e:
    try:
        fn.error_log(script_name, e)
        fn.session_log(script_name, notice_count, 0, notice_data.ml_cpv[0], 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("asia") 