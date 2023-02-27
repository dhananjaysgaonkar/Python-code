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
script_name = "br_al"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    
    notice_data.performance_country = 'Brazil'
    notice_data.contact_country = 'Brazil'
    notice_data.procurement_method = "Other"
    notice_data.language = 'ES'  
    notice_data.buyer ='ASSEMBLEIA LEGISLATIVA DO ESTADO DO MARANHAO'
    notice_data.buyer_internal_id = '7785872'
    notice_data.notice_type = 'spn'

    try:
        status = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div > div > p.mb-4'))).text
        status = GoogleTranslator(source='auto', target='en').translate(status)
        if status == 'In progress':

            try:                      
                notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div > div > p:nth-child(3)'))).text
                try:  
                    notice_data.end_date = re.findall('\d+/\d+/\d{4}',notice_data.end_date)[0]
                except:
                    notice_data.end_date = notice_data.end_date.split('Bidding date: ')[1]
                try:
                    notice_data.end_date = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
                except:
                    notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
                logging.info(notice_data.end_date)  
            except:
                pass

#             if notice_data.end_date is not None and notice_data.end_date < threshold:
#                 return

            try:
                notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div > div > div > h5'))).text
                notice_data.reference = GoogleTranslator(source='auto', target='en').translate(notice_data.reference)
                notice_data.reference = notice_data.reference.split('No. ')[1]
            except:
                pass

            try:
                title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div > div > p:nth-child(3)'))).text
                notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
                notice_data.title_en = notice_data.title_en.split('Bidding date:')[0]
                logging.info(notice_data.title_en)  
            except:
                pass
            
            try:
                notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except:
                pass 
            
            try:        
                rsrs = tender_html_element.find_elements(By.CSS_SELECTOR, 'a')
                notice_data.resource_url.clear()
                for rsr in rsrs:
                    resource = rsr.get_attribute('href')
                    notice_data.resource_url.append(resource)
            except:
                pass

            try:
                notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
            except:
                pass 

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
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:                         
    url = 'http://www.al.ma.leg.br/licitacoes/'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '/html/body/section[2]/div').find_elements(By.CSS_SELECTOR,'div.row'):
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
    page_main.quit()
    output_xml_file.copyFinalXMLToServer("latin")
