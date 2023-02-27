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
script_name = "kw_kcb"
output_xml_file = common.OutputXML.OutputXML(script_name)
 
def extract_and_save_notice_spn(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Kuwait'
    notice_data.contact_country = 'Kuwait'
    notice_data.procurement_method = "Other"
    notice_data.language = 'AR'  
    notice_data.buyer ='KUWAIT CREDIT BANK'
    notice_data.buyer_internal_id = '7555639'
 
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(9)'))).text
        try:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        except:
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y/%m/%d').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:                      
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(8)'))).text
        try:
            notice_data.end_date = datetime.strptime(notice_data.end_date ,'%m/%d/%Y').strftime('%Y/%m/%d')
        except:
            notice_data.end_date = datetime.strptime(notice_data.end_date ,'%Y/%m/%d').strftime('%Y/%m/%d')
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(11)'))).text
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(10)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        
        if('expression of interest' in title_en.lower() or 'eoi' in title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
    except:
        pass
    
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(10) a'))).get_attribute('href')
    except:
        notice_data.notice_url = url

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
    url = 'https://www.kcb.gov.kw/sites/arabic/Pages/ApplicationPages/TendersAnnouncements.aspx'
    fn.load_page(page_main, url)
    logging.info(url)
    
    for page_no in range(1,15):
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="ctl00_ctl45_g_c04846fd_3afe_4911_9355_ba5c91057299"]/main/div/div/div[3]/table').find_elements(By.CSS_SELECTOR,'tbody'):
            extract_and_save_notice_spn(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        try:
            WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_ctl45_g_c04846fd_3afe_4911_9355_ba5c91057299_DataPager1"]/a['+str(page_no)+']'))).click()
            logging.info("---Next Page---")
        except:
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
