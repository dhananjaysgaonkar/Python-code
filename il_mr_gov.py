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
script_name = "il_mr_gov"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Israel'
    notice_data.contact_country = 'Israel'
    notice_data.language = "HE" 
    notice_data.procurement_method = 'Other'

    try:
        published_date = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > div > div:nth-child(13) > div:nth-child(1) > span.font-weight-normal.number'))).text
        notice_data.published_date = datetime.strptime(published_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        logging.info('published_date = '+notice_data.published_date)
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > div > span.font-weight-normal.number'))).text
    except:
        pass

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > a'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        
        if('expression of interest' in notice_data.title_en.lower() or 'eoi' in notice_data.title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > div > span:nth-child(2)'))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
    except:
        pass

    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > div > div:nth-child(13) > div:nth-child(3) > span.font-weight-normal.number.last-date'))).text
        end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        pass
    
    try: 
        notice_data.notice_url = WebDriverWait(tender_html_element, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.content-wrapper.d-flex.justify-content-between.align-items-start.h-100 > div.details-main-wrapper > div > a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        
        try:
            rsrs = page_details.find_element(By.XPATH, '//*[@id="related-documents"]/div[2]').find_elements(By.CSS_SELECTOR, 'a')[::2]
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                notice_data.resource_url.append(resource)
        except:
            pass

        try:
            notice_data.notice_text = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]'))).get_attribute('outerHTML')
        except:
            pass
        
    except:
        notice_data.notice_url = url
    
    if notice_data.title_en is not None :
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
    urls =['https://mr.gov.il/ilgstorefront/he/search/?i=CENTRALTENDER',
         'https://mr.gov.il/ilgstorefront/en/search/?s=TENDER']
    
    for url in urls:
        fn.load_page(page_main, url)
        logging.info(url)

        page_main.execute_script("window.scrollBy(0, 150000)")

        for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[3]/div[2]'))).find_elements(By.CSS_SELECTOR,'div.details-main-wrapper'):
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
