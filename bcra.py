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
script_name = "ar_bcra"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice_spn(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Argentina'
    notice_data.contact_country = 'Argentina'
    notice_data.procurement_method = "Other"
    notice_data.language = 'ES'  
    notice_data.buyer ='BANCO CENTRAL DE LA REPÚBLICA ARGENTINA'
    notice_data.buyer_internal_id = '7785754'
    notice_data.notice_url = url
 
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(6)'))).text
        notice_data.published_date = re.findall('\d+/\d+/\d{4}',notice_data.published_date)[0]
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        notice_type = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(5)'))).text
        notice_type = GoogleTranslator(source='auto', target='en').translate(notice_type)
        if notice_type == 'Rev RFI':
            notice_data.notice_type = 'rei'
        elif notice_type == 'Awarded':
            notice_data.notice_type = 'ca'
        elif notice_type == 'Cancelled':
            notice_data.notice_type = 'spn'
            notice_data.update = True
        elif notice_type == 'Authorized':
            notice_data.notice_type = 'spn'
        else:
            return
    except:
        pass
    
    try:                      
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(7)'))).text
        notice_data.end_date = re.findall('\d+/\d+/\d{4}',notice_data.end_date)[0]
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(4)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
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
    url = 'https://ps.bcra.gob.ar/psp/sup/SUPPLIER/ERP/c/BCA_ESUP.AUC_RESP_INQ_AUC.GBL?&cmd=uninav&Rnode=LOCAL_NODE&uninavpath=Ra%C3%ADz{PORTAL_ROOT_OBJECT}&PORTALPARAM_PTCNAV=BCA_RESP_INQ_AUC_GBL&EOPP.SCNode=ERP&EOPP.SCPortal=SUPPLIER&EOPP.SCName=ADMN_CONTRATACIONES&EOPP.SCLabel=&EOPP.SCPTcname=PT_PTPP_SCFNAV_BASEPAGE_SCR&FolderPath=PORTAL_ROOT_OBJECT.PORTAL_BASE_DATA.CO_NAVIGATION_COLLECTIONS.ADMN_CONTRATACIONES.ADMN_F202107072100361672414319.ADMN_S202107072107341043427838&IsFolder=false'
    fn.load_page(page_main, url)
    logging.info(url)
 
    iframe = page_main.find_element(By.XPATH, '//*[@id="ptifrmtgtframe"]')
    page_main.switch_to.frame(iframe)          
    
    rows = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tdgbrRESP_INQA_HD_VW_GR$0"]/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[:20]
    length = len(rows)
    for k in range(0,(length-1)):
        tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tdgbrRESP_INQA_HD_VW_GR$0"]/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[k]
        extract_and_save_notice_spn(tender_html_element)
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
    output_xml_file.copyFinalXMLToServer("latin")
