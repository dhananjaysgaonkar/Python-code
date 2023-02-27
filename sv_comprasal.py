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
script_name = "sv_comprasal"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice_spn(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'El Salvador'
    notice_data.contact_country = 'El Salvador'
    notice_data.language = "ES"  
    notice_data.procurement_method = 'Other'
    
    if temp == 'spn':
        notice_data.notice_type = "spn"
    else:
        notice_data.notice_type = "ca"
     
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info('published_date '+notice_data.published_date)  
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(6)'))).text
        notice_data.end_date = notice_data.end_date.split('- ')[1]
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info('end_date '+notice_data.end_date)  
    except:
        pass
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info('title_en '+notice_data.title_en)  
    except:
        pass
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        logging.info('reference '+notice_data.reference)  
    except:
        pass
    
    try:
        buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(1)'))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info('buyer '+notice_data.buyer)  
    except:
        pass
     
    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3) a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info('notice_url '+notice_data.notice_url)  
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-details/div[2]/div'))).get_attribute('outerHTML')
        except:
            pass
        
        try:
            notice_data.contact_name = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Nombre del contacto')]//following::p"))).get_attribute('innerHTML')
            logging.info('contact_name: ' + notice_data.contact_name)
        except:
            pass
    except:
        notice_data.notice_url = url
    
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
temp = 'spn'

url = 'https://www.comprasal.gob.sv/comprasalweb/procesos'
fn.load_page(page_main, url)
logging.info(url)
tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[1]'))).click()
advance_src = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[1]/div/button'))).click()
srch = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[4]/div/button'))).click()

try:  
    for page_no in range(1,25):
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(2)"))).text
        rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')
        length = len(rows)

        for k in range(0,(length-1)):
            tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[k]
            extract_and_save_notice_spn(tender_html_element)
            if notice_count >= MAX_NOTICES:
                logging.info("ok breaking")
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break

        try:
            nxt_page = page_main.find_element(By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/app-paginator/div/div[1]/ngb-pagination/ul/li[6]/a').click()        
            logging.info("---Next Page---")
            time.sleep(5)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "td:nth-child(2)"),page_check))
        except:
            logging.info("---No Next Page---")
            break

    print("----CONTRACT AWARDS----")
    fn.load_page(page_main, url)
    tendr = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[2]/div/div[1]/div/div[2]/app-checkbox-buttons/div/label[1]'))).click()
    advance_src = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[1]/div/button'))).click()
    WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[3]/div/div/div[2]/div/div[2]/app-checkbox-buttons/div/label[4]/span[2]'))).click()
    WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[3]/div/div/div[2]/div/div[2]/app-checkbox-buttons/div/label[3]/span[1]'))).click()
    srch = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[4]/div/button'))).click()

    ca_url = page_main.current_url
    logging.info(ca_url)
    temp = 'ca'
    
    try:
        for page_no in range(1,25):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-child(2)"))).text
            rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')
            length = len(rows)

            for k in range(0,(length-1)):
                tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[k]
                extract_and_save_notice_spn(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    logging.info("ok breaking")
                    break

            if notice_data.published_date is not None and notice_data.published_date < threshold:
                break

            try:
                nxt_page = page_main.find_element(By.XPATH,'/html/body/app-root/div[1]/app-purchase-searchbox/div[5]/div/app-purchase-list2/div[2]/app-paginator/div/div[1]/ngb-pagination/ul/li[6]/a').click()        
                logging.info("---Next Page---")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "td:nth-child(2)"),page_check))
            except:
                logging.info("---No Next Page---")
                break
    except:
        logging.info("----No Data----")
            
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
    output_xml_file.copyFinalXMLToServer("north_america") 