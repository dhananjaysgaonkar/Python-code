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
script_name = "bh_tenderboard"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Bahrain'
    notice_data.contact_country = 'Bahrain'
    notice_data.language = "EN"  
    notice_data.notice_type = "spn"
    
    try: 
        notice_data.notice_url = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        

        try:
            published_date = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Publish Date")]//following::dd'))).text
            published_date = re.findall('\d+ \w+ \d{4}',published_date)[0]
            notice_data.published_date = datetime.strptime(published_date,'%d %B %Y').strftime("%Y/%m/%d")
            logging.info('published_date = '+notice_data.published_date)
        except:
            pass
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

        try:
            notice_data.reference = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="page"]/section[2]/div/div/div/div[1]/div/p[1]'))).text
            notice_data.reference = notice_data.reference.split('Tender Number: ')[1]
            
        except:
            pass

        try:
            notice_data.title_en = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="page"]/section[2]/div/div/div/div[1]/div/h3'))).text
            
        except:
            pass

        try:
            notice_data.buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="page"]/section[2]/div/div/div/div[1]/div/dl/dd[1]'))).text
            
        except:
            pass

        try:
            end_date = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Closing Date')]//following::dd"))).text
            end_date = re.findall('\d+ \w+ \d{4}',end_date)[0]
            notice_data.end_date = datetime.strptime(end_date ,'%d %B %Y').strftime('%Y/%m/%d')
            
        except:
            pass

        try:
            notice_data.notice_text = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="page"]/section[2]/div/div/div/div[1]/div'))).get_attribute('outerHTML')
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
    urls = ['https://www.tenderboard.gov.bh/Tenders/Public%20Tenders/',
          'https://www.tenderboard.gov.bh/Tenders/To%20be%20Opened/']
    
    for url in urls:
        fn.load_page(page_main, url)
        logging.info(url)
        time.sleep(30)

        for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="cphBaseBody_CphInnerBody_TenderDetailsBlock"]'))).find_elements(By.CSS_SELECTOR,'div.rows'):
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
