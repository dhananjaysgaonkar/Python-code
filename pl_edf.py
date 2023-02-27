import logging
import time
import re
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData

MAX_NOTICES = 2000
script_name = "pl_edf"
notice_count = 0
output_xml_file = common.OutputXML.OutputXML(script_name) 

# ----------------------------------------------------------------------SPN----------------------------------------------------------------------------------------------------------
 
def extract_and_save_notice_spn(tender_html_element):
    global ml_cpv
    global notice_count
    global notice_data
    
    notice_data = NoticeData()
    notice_data.performance_country = 'Poland'
    notice_data.contact_country = 'Poland'
    notice_data.notice_type = 'spn'
    notice_data.procurement_method = "Other"
    notice_data.language = "PL"

    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(5) a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span#button-1012-btnInnerEl.x-btn-inner'))).click()
        except:
            pass
    except: 
        pass

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(5)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info(notice_data.title_en)  
    except: 
        pass
           
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
    except:
        pass

    try:
        notice_data.published_date = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.published_date = re.findall('\d{4}-\d+-\d+',notice_data.published_date)[0]
        notice_data.published_date = datetime.strptime(notice_data.published_date,'%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        notice_data.end_date = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        notice_data.end_date = re.findall('\d{4}-\d+-\d+',notice_data.end_date)[0]
        notice_data.end_date = datetime.strptime(notice_data.end_date,'%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        pass
             
    try:
        notice_data.notice_text = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/div[2]/div/div'))).get_attribute('outerHTML')
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1


# ----------------------------------------------------------------------CA----------------------------------------------------------------------------------------------------------

def extract_and_save_notice_ca(tender_html_element):
    global ml_cpv
    global notice_count
    global notice_data
    
    notice_data = NoticeData()
    notice_data.performance_country = 'Poland'
    notice_data.contact_country = 'Poland'
    notice_data.notice_type = 'ca'
    notice_data.procurement_method = "Other"
    notice_data.language = "PL"

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(4)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info(notice_data.title_en)  
    except: 
        pass
           
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text 
    except:
        pass

    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        notice_data.published_date = re.findall('\d{4}-\d+-\d+',notice_data.published_date)[0]
        notice_data.published_date = datetime.strptime(notice_data.published_date,'%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text 
    except:
        pass
        
    try:
        notice_data.notice_text = tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1 


# -------------------------------------------------------------------------Main Body------------------------------------------------------------------------------------

page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() - timedelta(2)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:
    url = 'https://edf.eb2b.com.pl/open-auctions.html'
    fn.load_page(page_main, url)
    logging.info(url)
    
    try:
        WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span#button-1012-btnInnerEl.x-btn-inner'))).click()
    except:
        pass

    for page_no in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(5)"))).text
        rows = page_main.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody').find_elements(By.CSS_SELECTOR, 'tr')[1:]
        length = len(rows)
        for k in range(0,(length-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[1:][k]
            extract_and_save_notice_spn(tender_html_element)
            if notice_count >= MAX_NOTICES:
                logging.info("ok breaking")
                break
                  
        try:
            nxt_page = page_main.find_element(By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[3]/div/div/div[7]/em/button/span[2]').click()   
            logging.info("NEXT PAGE") 
            MAX_LOAD_DRIVER_ATTEMPTS = 3
            nxt_page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(5)'))).text
            for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS):
                if nxt_page_check != page_check:
                    break
                else:
                    time.sleep(10)
                    pass
        except:
            pass
    
    
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#content > div.sidebar > div:nth-child(3) > ul > li:nth-child(2) > a'))).click()
    
    try:
        WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span#button-1012-btnInnerEl.x-btn-inner'))).click()
    except:
        pass

    for page_no in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(4)"))).text
        rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[1:]
        length = len(rows)
        for k in range(0,(length-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[2]/div[2]/div/div/div[2]/div/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[1:][k]
            extract_and_save_notice_ca(tender_html_element)
            if notice_count >= MAX_NOTICES:
                logging.info("ok breaking")
                break

        try:
            nxt_page = page_main.find_element(By.CSS_SELECTOR,'#button-1030-btnIconEl').click()
            logging.info("NEXT PAGE") 
            MAX_LOAD_DRIVER_ATTEMPTS = 3
            nxt_page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(4)'))).text
            for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS):
                if nxt_page_check != page_check:
                    break
                else:
                    time.sleep(10)
                    pass
        except:
            pass

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
    output_xml_file.copyFinalXMLToServer("europe")
