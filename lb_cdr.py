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
script_name = "lb_cdr"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice_spn(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Lebanon'
    notice_data.contact_country = 'Lebanon'
    notice_data.procurement_method = "Other"
    notice_data.language = 'AR'  
    notice_data.buyer ='COUNCIL FOR DEVELOPMENT AND RECONSTRUCTION'
    notice_data.buyer_internal_id = '7581233'
    notice_data.notice_url = url
    
    try:
        published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(6)'))).text
        if('كانون الثاني' in published_date):
            published_date =published_date.replace('كانون الثاني','1')
        elif('شباط' in published_date):
            published_date =published_date.replace('شباط','2')
        elif('آذار' in published_date):
            published_date =published_date.replace('آذار','3')
        elif('نيسان' in published_date):
            published_date =published_date.replace('نيسان','4')
        elif('أيار' in published_date):
            published_date =published_date.replace('أيار','5')
        elif('حزيران' in published_date):
            published_date =published_date.replace('حزيران','6')
        elif('تموز'in published_date):
            published_date =published_date.replace('تموز','7')
        elif('آب' in published_date):
            published_date =published_date.replace('آب','8')
        elif('أيلول' in published_date):
            published_date =published_date.replace('أيلول','9')
        elif('تشرين الأول' in published_date):
            published_date =published_date.replace('تشرين الأول','10')
        elif('تشرين الثاني' in published_date):
            published_date =published_date.replace('تشرين الثاني','11')
        elif('كانون الأول' in published_date):
            published_date =published_date.replace('كانون الأول','12')
        else:
            pass
        notice_data.published_date = datetime.strptime(published_date, '%d %m %Y').strftime('%Y/%m/%d')
        logging.info('Published Date = '+notice_data.published_date)
    except:
        pass

    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:                 
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(8)'))).text
        if('كانون الثاني' in end_date):
            end_date =end_date.replace('كانون الثاني','1')
        elif('شباط' in end_date):
            end_date =end_date.replace('شباط','2')
        elif('آذار' in end_date):
            end_date =end_date.replace('آذار','3')
        elif('نيسان' in end_date):
            end_date =end_date.replace('نيسان','4')
        elif('أيار' in end_date):
            end_date =end_date.replace('أيار','5')
        elif('حزيران' in end_date):
            end_date =end_date.replace('حزيران','6')
        elif('تموز'in end_date):
            end_date =end_date.replace('تموز','7')
        elif('آب' in end_date):
            end_date =end_date.replace('آب','8')
        elif('أيلول' in end_date):
            end_date =end_date.replace('أيلول','9')
        elif('تشرين الأول' in end_date):
            end_date =end_date.replace('تشرين الأول','10')
        elif('تشرين الثاني' in end_date):
            end_date =end_date.replace('تشرين الثاني','11')
        elif('كانون الأول' in end_date):
            end_date =end_date.replace('كانون الأول','12')
        else:
            pass
        notice_data.end_date = datetime.strptime(end_date, '%d %m %Y').strftime('%Y/%m/%d')
   
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(1) a').get_attribute('href')
   
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(1)'))).text
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
    url = 'https://www.cdr.gov.lb/ar/Procurment.aspx?aliaspath=%2fProcurment'
    fn.load_page(page_main, url)
    logging.info(url)
        
    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="ProcurmentsTbody"]').find_elements(By.CSS_SELECTOR,'.content'):
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
    output_xml_file.copyFinalXMLToServer("middle_east")
