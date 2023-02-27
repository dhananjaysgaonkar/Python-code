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
script_name = "za_dffe"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'South Africa'
    notice_data.buyer_internal_id = '7784527'
    notice_data.contact_country = 'South Africa'
    notice_data.language = "EN"  
    notice_data.buyer = 'Department of Forestry, Fisheries and the Environment'
    
    if notice_type == 'spn':

        try:  
            notice_data.end_date = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
            notice_data.end_date = re.findall('\d{4}-\d+-\d+',notice_data.end_date)[0]
            try:
                notice_data.end_date = datetime.strptime(notice_data.end_date,'%Y-%m-%d').strftime("%Y/%m/%d")
            except:
                notice_data.end_date = datetime.strptime(notice_data.end_date,'%Y-%d-%m').strftime("%Y/%m/%d")
            logging.info('end_date = '+notice_data.end_date)
        except:
            pass
        if notice_data.end_date is not None and notice_data.end_date < threshold:
            return

        try:
            notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
        except:
            pass

        try:
            notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
            notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)

            if('expression of interest' in title_en.lower() or 'eoi' in title_en.lower()):
                notice_data.notice_type = 'rei'
            else:
                notice_data.notice_type = 'spn'
        except:
            pass

        try: 
            notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3) a'))).get_attribute('href')
        except:
            notice_data.notice_url = url

        try:
            rsrs = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').find_elements(By.CSS_SELECTOR, 'a')
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                notice_data.resource_url.append(resource)
        except:
            pass
    
    else:
        notice_data.notice_type = 'ca'
        
        try:
            notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
        except:
            pass

        try:
            notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2)'))).text
            notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        except:
            pass
        
        try: 
            notice_data.award_company = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
            notice_data.award_company = notice_data.award_company.split('Amount:')[0]
            
            if 'Company name:' in notice_data.award_company:
                notice_data.award_company.strip('Company name:')
        except:
            pass
        
        try: 
            notice_data.est_cost = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
            notice_data.est_cost = notice_data.est_cost.split('Amount:')[1]      
            notice_data.est_cost = re.sub("[^\d\.]", "", notice_data.est_cost)
        except:
            pass
        
        try: 
            notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(2) a'))).get_attribute('href')
        except:
            notice_data.notice_url = url
        

    try:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
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
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:  
    url = 'https://www.dffe.gov.za/procurement/tenders'
    fn.load_page(page_main, url)
    logging.info(url)
    
    notice_type = 'spn'

    for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="quicktabs-tabpage-tenders_tabs-0"]/div/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr'):
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break
    
    WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="quicktabs-tab-tenders_tabs-1"]'))).click()
    
    notice_type = 'ca'
    
    for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="quicktabs-tabpage-tenders_tabs-1"]/div/div/table[1]/tbody'))).find_elements(By.CSS_SELECTOR,'tr'):
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
    output_xml_file.copyFinalXMLToServer("africa") 
