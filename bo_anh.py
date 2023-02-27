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
script_name = "bo_anh"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Bolivia'
    notice_data.contact_country = 'Bolivia'
    notice_data.procurement_method = 'Other'
    notice_data.language = 'ES'
    notice_data.currency ='BOB'
    notice_data.buyer = 'AGENCIA NACIONAL DE HIDROCARBUROS'
    notice_data.buyer_internal_id = '7769238'
    notice_data.contact_email = 'contact @ anh.gob.bo'
    notice_data.contact_phone = '(591)-2-2614000'
    notice_data.notice_url = url

    try:                                                                                                                                              
        notice_data.end_date = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(5)'))).text
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)  
    except:
        pass
    
    if notice_data.end_date is not None and notice_data.end_date < threshold:
        return
    
    try:
        reference = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(1)'))).text
        notice_data.reference = GoogleTranslator(source='auto', target='en').translate(reference)
        notice_data.reference = notice_data.reference.split('\n')[0].strip()
    except:
        pass
    
    try:
        title_en = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(1)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        notice_data.title_en = notice_data.title_en.split('\n')[1].strip()
    except:
        pass
    
    if('expression of interest' in title_en.lower() or 'eoi' in title_en.lower()):
        notice_data.notice_type = 'rei'
    else:
        notice_data.notice_type = 'spn'
        
    try:
        EOS  = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(4)'))).text
        notice_data.est_cost  = re.findall('\d+\.\d+',EOS)[0].replace(".","")
    except:
        pass

    try:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML') 
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
    url = 'https://www.anh.gob.bo/w2019/contenido.php?s=55'
    fn.load_page(page_main, url)
    logging.info(url)
    
    for page_no in range(2,4):
        for tender_html_element in page_main.find_element(By.XPATH, '/html/body/div[3]/div/div[2]/div[2]/div/table/tbody').find_elements(By.CSS_SELECTOR,'tr'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

        try:     
            nxt_page = page_main.find_element(By.LINK_TEXT,str(page_no)).click()
            logging.info("---Next Page---")
        except:
            logging.info("---No Next Page---")
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
    output_xml_file.copyFinalXMLToServer("latin") 