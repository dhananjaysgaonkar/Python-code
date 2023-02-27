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
script_name = "gy_npta"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice_spn(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Guyana'
    notice_data.contact_country = 'Guyana'
    notice_data.procurement_method = "Other"
    notice_data.language = "EN"  
    notice_data.notice_type = "spn"
    notice_data.notice_url = url
    
    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(3)"))).text
        try:
            notice_data.end_date = datetime.strptime(end_date, '%m/%d/%y').strftime("%Y/%m/%d")
        except:
            notice_data.end_date = datetime.strptime(end_date, '%m/%d/%Y').strftime("%Y/%m/%d")
        logging.info(notice_data.end_date)  
    except:
        pass
    
    if notice_data.end_date is not None and notice_data.end_date < threshold:
        return
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(1)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(2)"))).text
       
    except:
        pass
    
    try:  
        notice_data.resource_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.ninja_column_5.ninja_clmn_nm_notice.footable-last-visible > a').get_attribute('href')
        
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
    
#             -------------------------------------CA-------------------------------------

def extract_and_save_notice_ca(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Guyana'
    notice_data.contact_country = 'Guyana'
    notice_data.procurement_method = "Other"
    notice_data.language = "EN"  
    notice_data.notice_type = "ca"
    notice_data.notice_url = url
    
    try:
        awarding_award_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(9)"))).text
        try:
            notice_data.awarding_award_date = datetime.strptime(awarding_award_date, '%m/%d/%y').strftime("%Y/%m/%d")
        except:
            notice_data.awarding_award_date = datetime.strptime(awarding_award_date, '%m/%d/%Y').strftime("%Y/%m/%d")
        notice_data.published_date = notice_data.awarding_award_date
        logging.info(notice_data.awarding_award_date)  
    except:
        pass
    
    if notice_data.awarding_award_date is not None and notice_data.awarding_award_date < threshold:
        return
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(4)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
         
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(1)"))).text
         
    except:
        pass
    
    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(2)"))).text
        
    except:
        pass
    
    try:
        notice_data.award_company = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(3)"))).text
        
    except:
        pass
    
    try:
        notice_data.awarding_final_value = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(5)"))).text
        
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
    url = 'https://www.npta.gov.gy/procurement-opportunities/'
    fn.load_page(page_main, url)
    logging.info(url)

    for i in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="footable_71500"]/tbody/tr[2]/td[1]'))).text
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="footable_71500"]/tbody').find_elements(By.CSS_SELECTOR,'tr'):
            extract_and_save_notice_spn(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.end_date is not None and notice_data.end_date < threshold:
            break

        try:
            nxt_page = page_main.find_element(By.XPATH,'//*[@id="footable_71500"]/tfoot/tr/td/div/ul/li[12]/a').click()        
            logging.info("---Next Page---")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="footable_71500"]/tbody/tr[2]/td[1]'),page_check))
        except:
            logging.info("No Next Page")
            break
            
#             -------------------------------------CA-------------------------------------

    url = 'https://www.npta.gov.gy/tenders-awarded/'
    fn.load_page(page_main, url)    
    logging.info(url)
    

    for i in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2)'))).text
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="footable_71517"]/tbody').find_elements(By.CSS_SELECTOR,'tr'):
            extract_and_save_notice_ca(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.awarding_award_date is not None and notice_data.awarding_award_date < threshold:
            break

        try:
            nxt_page = page_main.find_element(By.XPATH,'//*[@id="footable_71517"]/tfoot/tr/td/div/ul/li[92]/a').click()        
            logging.info("---Next Page---")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'td:nth-child(2)'),page_check))
        except:
            logging.info("No Next Page")
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