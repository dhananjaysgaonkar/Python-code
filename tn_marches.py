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
script_name = "tn_marches"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Tunisia'
    notice_data.contact_country = 'Tunisia'
    notice_data.language = "FR"  
    notice_data.notice_type = "spn"
     
    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%d/%m/%Y ').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        pass
    
    try:
        buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(1)'))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
    except:
        pass
     
    try:
        notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d/%m/%Y ').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        type = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        if(type=='National '):
            notice_data.procurement_method = 'National'
        elif(type=='International '):
            notice_data.procurement_method= 'International'
        else:
            notice_data.procurement_method = 'Other' 
    except:
        notice_data.procurement_method = 'Other'
    
    try:
        notice_data.resource_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(7) >  a'))).get_attribute('href')
    except:
        pass
    
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(9) >  a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
    
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tablecontent"]/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/table[1]/tbody'))).get_attribute('outerHTML')
        except:
            pass
    except:
        notice_data.notice_url = url
    
    notice_data.cleanup()
    
    if notice_data.title_en is not None :
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)

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
    for page_no in range(1,25):
        url = 'http://www.marchespublics.gov.tn/onmp/appeldoffre/listappeldoffrefront.php?lang=en&URLref_type_procedure=&URLdate_reception_offre_debut=&URLdate_reception_offre_fin=&URLref_lieu_execution=&URLobjet=&URLref_mode_financement=&URLref_secteur=&URLref_type=&Formlist_Sorting=6&Formlist_Sorted=6&Formlist_Page='+str(page_no)
        fn.load_page(page_main, url)
        logging.info(url)
        for tender_html_element in page_main.find_element(By.XPATH, '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
        if notice_data.published_date is not None and notice_data.published_date < threshold:
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
    output_xml_file.copyFinalXMLToServer("africa") 