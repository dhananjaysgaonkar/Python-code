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
script_name = "eg_amcham"
notice_count = 0
output_xml_file = common.OutputXML.OutputXML(script_name) 

def extract_and_save_notice(tender_html_element):
    global ml_cpv
    global notice_count
    global notice_data
    
    notice_data = NoticeData()
    notice_data.performance_country = 'Egypt'
    notice_data.contact_country = 'Egypt'
    notice_data.notice_type = 'spn'
    notice_data.procurement_method = "Other"
    notice_data.language = "EN"

    try: 
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div > div.col-sm-8.col-xs-12._buff-sm-pb > div.h3.buff-mt-flat.buff-mb-flat.relative.text-red.pr-4 > a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info("notice_url " +notice_data.notice_url)
    except: 
        pass
 
    try:
        notice_data.title_en = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]/div[1]/div/div[1]'))).text
        logging.info('title_en '+notice_data.title_en)  
    except: 
        pass

    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div > div.col-sm-8.col-xs-12._buff-sm-pb > div:nth-child(3)'))).text
        notice_data.published_date = datetime.strptime(notice_data.published_date,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info('published_date '+notice_data.published_date)  
    except:
        pass

    try:
        notice_data.end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ' div > div.col-sm-4.col-xs-12.text-center > div:nth-child(2) > div.h3.buff-mt-flat.buff-mb-flat.ng-binding'))).text
        notice_data.end_date = datetime.strptime(notice_data.end_date,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info('end_date '+notice_data.end_date)  
    except:
        pass
    
    try:
        notice_data.category = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.col-sm-8.col-xs-12._buff-sm-pb > div.h4.regular-text.text-blue-light.text-normal.buff-mb-flat > div > a'))).text
        logging.info('category '+notice_data.category)  
    except:
        pass

    try:
        iframe = WebDriverWait(page_details, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="recaptcha"]/no-captcha/div/div/iframe')))
        page_details.switch_to.frame(iframe)
        checkbox = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="recaptcha-anchor"]'))).click()
    except:
        pass    
        
    try:
        notice_data.buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]/div[2]/div/div/div[2]/div[1]'))).text
        notice_data.buyer = notice_data.buyer.split('Company Name: ')[1]
        logging.info("buyer " +notice_data.buyer)
    except:
        pass
    
    try:
        notice_data.address = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]/div[2]/div/div/div[2]/div[2]'))).text
        notice_data.address = notice_data.address.split('Address: ')[1]
        logging.info("address " +notice_data.address)
    except:
        pass
    
    try:
        notice_data.contact_phone = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]/div[2]/div/div/div[2]/div[3]'))).text
        notice_data.contact_phone = notice_data.contact_phone.split('Phone: ')[1]
        logging.info("contact_phone " +notice_data.contact_phone)
    except:
        pass
    
    try:
        notice_data.contact_email = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]/div[2]/div/div/div[2]/div[4]'))).text
        notice_data.contact_email = notice_data.contact_email.split('Email: ')[1]
        logging.info("contact_email " +notice_data.contact_email)
    except:
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainContent"]/div[1]'))).get_attribute('outerHTML')
    except:
        pass
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)
        
    notice_data.cleanup()

    if notice_data.published_date is not None and notice_data.published_date < threshold:
         return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------') 


# -------------------------------------------------------------------------Main Body------------------------------------------------------------------------------------

page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() - timedelta(2)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:
    for login in ['kumar@globalecontent.com','thevar@globalecontent.com','dineshthiru36@gmail.com','muthueswari27@gmail.com']:
        url = 'https://www.amcham.org.eg/login/login.asp'
        fn.load_page(page_details, url)
        WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.ID, 'UserEmail'))).send_keys(login)
        WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.ID, 'Password'))).send_keys('muthu123456')
        WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#loginForm > form > div:nth-child(19) > div > input'))).click()
        
        url = 'https://www.amcham.org.eg/tas/search?area=All&status=Active&bidBondTo=1000000&typeID=999&sortType=desc&sortBy=3'
        fn.load_page(page_main, url)
        logging.info(url)

        for load_more in range(1,5):
            try:
                WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-result > div.thumbnail > ac-overlay-spinner > div > ng-transclude > div > div > div.clearfix.caption.pt-0.ng-scope > div.ng-isolate-scope > p > button'))).click()
            except:
                break

        for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="search-result"]/div[1]/ac-overlay-spinner/div/ng-transclude/div/div/div[2]'))).find_elements(By.CSS_SELECTOR,'div.relative.ng-scope.footer'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                logging.info("ok breaking")
                break
                
        page_details.get('https://www.amcham.org.eg/includes/logoff.asp')
        
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