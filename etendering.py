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
script_name = "bh_etendering"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Bahrain'
    notice_data.contact_country = 'Bahrain'
    notice_data.language = "EN"  
    notice_data.notice_type = "spn"

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
    except:
        pass
    
    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(5)'))).text
    except:
        pass
     
    try:
        end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(9)').text
        notice_data.end_date = end_date.split(' ')[0]
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d-%m-%Y').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'td:nth-child(13) a:nth-child(1)'))).click()
        page_main.switch_to.window(page_main.window_handles[1])
        published_date = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Tender Published Date')]//following::td"))).text
        try:
            notice_data.published_date = datetime.strptime(published_date,'%d-%m-%Y').strftime("%Y/%m/%d")
        except:
            notice_data.published_date = datetime.strptime(published_date,'%m-%d-%Y').strftime("%Y/%m/%d")
        logging.info('published_date '+notice_data.published_date)
    except:
        pass

    try:
        notice_data.notice_url = page_main.current_url
    except:
        notice_data.notice_url = url

    try:
        notice_data.notice_text = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div/div'))).get_attribute('outerHTML')
        page_main.switch_to.window(page_main.window_handles[0])
    except:
        pass
  
    try:
        id = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(13) a:nth-child(1)'))).get_attribute('onclick')
        id = id.split("('")[1]
        id = id.split("')")[0]
        notice_data.resource_url = 'https://etendering.tenderboard.gov.bh/Tenders/template/TenderAdvertisement'+str(id)+'.pdf'
    except:
        pass
    
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
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
    url = 'https://etendering.tenderboard.gov.bh/Tenders/publicDash?viewFlag=NewTenders&CTRL_STRDIRECTION=LTR&encparam=viewFlag,CTRL_STRDIRECTION,randomno&hashval=78ca087819d1ecc2ccf72801acd105fc1538485253d7f8c5ff7fd61d0707a420%27'
    fn.load_page(page_main, url)
    logging.info(url)
    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="NewTndRecord"]/tbody').find_elements(By.CSS_SELECTOR,'tr'):
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
    output_xml_file.copyFinalXMLToServer("middle_east") 
