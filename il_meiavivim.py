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
from selenium.webdriver.support.ui import Select
import dateparser
from hijri_converter import convert

notice_count = 0 
MAX_NOTICES = 2000
script_name = "il_meiavivim"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'IRAN'
    notice_data.contact_country = 'IRAN'
    notice_data.procurement_method = "Other"
    notice_data.language = "FA"  
    notice_data.buyer_internal_id = "7769303"
    notice_data.buyer = 'PARS SPECIAL ECONOMIC ENERGY ORGANIZATION (EPA)'
    
    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div > div.last_date_offer_td > span:nth-child(2)"))).text
        end_date = GoogleTranslator(source='auto', target='en').translate(end_date)
        end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info("end_date " +notice_data.end_date)
    except:
        pass
    
    if notice_data.end_date is not None and notice_data.end_date < threshold:
        return

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div > div.name_td > span:nth-child(2)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        if('expression of interest' in notice_data.title_en.lower() or 'eoi' in notice_data.title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
        logging.info("notice_type " +notice_data.notice_type)
        logging.info("title_en " +notice_data.title_en)
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div > div.number_td > span:nth-child(2) "))).text
        logging.info("reference " +notice_data.reference)
    except:
        pass
        
    try: 
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div > div.actions_td > a'))).get_attribute('href')
        logging.info("notice_url " +notice_data.notice_url)
        fn.load_page(page_details, notice_data.notice_url)
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_cphMiddle_pnl00cphMiddle_2169"]/div/div/div[2]'))).get_attribute('outerHTML')
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
    url = 'https://www.mei-avivim.co.il/%D7%9E%D7%9B%D7%A8%D7%96%D7%99%D7%9D-%D7%A4%D7%95%D7%9E%D7%91%D7%99%D7%99%D7%9D/'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="block-module-2"]/div/div/div/div[2]').find_elements(By.CSS_SELECTOR,'div')[1:]:
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