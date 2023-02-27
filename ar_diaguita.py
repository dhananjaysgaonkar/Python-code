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
script_name = "ar_diaguita"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Argentina'
    notice_data.contact_country = 'Argentina'
    notice_data.procurement_method = 'Other'
    notice_data.language = 'ES'
    notice_data.notice_type = 'spn'
    notice_data.buyer = 'UNIVERSIDAD NACIONAL DE CORDOBA'
    notice_data.buyer_internal_id = '7530923'
    
    try:                                                                                                                                              
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(4)'))).text
        notice_data.published_date = notice_data.published_date.split(' ')[0]
        try:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        except:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:                                                                                                                                              
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(5)'))).text
        notice_data.end_date = notice_data.end_date.split(' ')[0]
        try:
            notice_data.end_date = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        except:
            notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(3)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        pass
     
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(1) > a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)

        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="convocatoria"]'))).get_attribute('outerHTML') 
        except:
            pass 
      
        try:
            rsrs = page_details.find_element(By.XPATH, '//*[@id="ef_form_110000015_form_descargadocumentos_adjuntos"]/div').find_elements(By.CSS_SELECTOR, 'a')[::2]
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                notice_data.resource_url.append(resource)
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
    url = 'https://diaguita.unc.edu.ar/spgi/diaguita/aplicacion.php?ah=st52811aafc81ca&ai=diaguita%7C%7C110000003'
    fn.load_page(page_main, url)
    logging.info(url)
    
    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="cuerpo_js_cuadro_110000008_cuadro_convocatorias"]/tbody/tr[2]/td/table/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
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
    output_xml_file.copyFinalXMLToServer("latin") 
