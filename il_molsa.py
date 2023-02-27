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
script_name = "il_molsa"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Israel'
    notice_data.buyer_internal_id = '7769305'
    notice_data.contact_country = 'Israel'
    notice_data.language = "HE"  
    notice_data.buyer = 'Ministry of Welfare and Social Security'
    notice_data.contact_name = 'Jordan Garnirer'
    notice_data.contact_email = 'michrazim@molsa.gov.il'

    try:
        published_date = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
        notice_data.published_date = datetime.strptime(published_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        logging.info('published_date = '+notice_data.published_date)
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2)'))).text
    except:
        pass
    
    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td span a'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        
        if('expression of interest' in title_en.lower() or 'eoi' in title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
    except:
        pass
    
    try:
        update = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
        update = GoogleTranslator(source='auto', target='en').translate(update)

        if update == 'Updated':
            notice_data.update = True
    except:
        pass
    
    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(5)'))).text
        end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        pass

    try: 
        notice_data.notice_url = WebDriverWait(tender_html_element, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td span a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            rsrs = page_details.find_element(By.XPATH, '//*[@id="related-documents"]/div[2]').find_elements(By.CSS_SELECTOR, 'a')[::2]
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                if resource in notice_data.resource_url:
                    pass
                else:
                    notice_data.resource_url.append(resource)
        except:
            pass
        
        try:
            notice_data.notice_text = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]'))).get_attribute('outerHTML')
        except:
            pass
    except:
        pass
    
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
    url = 'https://www.molsa.gov.il/Tenders/Pages/ServicesTendersSearch.aspx'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="__gvctl00_SPWebPartManager1_g_556ac700_bf84_4752_afd7_cf7be3c12600_ctl05__div"]/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[1:]:
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