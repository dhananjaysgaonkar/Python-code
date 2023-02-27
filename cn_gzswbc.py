import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
import ml.cpv_classifier as classifier
from false_cpv import false_cpv
from functions import ET
from selenium.webdriver.support.ui import Select

notice_count = 0 
MAX_NOTICES = 2000
script_name = "cn_gzswbc"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    wait = WebDriverWait(page_main, 10)  
    
    notice_data.performance_country = 'China'
    notice_data.contact_country = 'China'
    notice_data.procurement_method = "Other"
    notice_data.language = "CN"  
    notice_data.currency = "CNY"
    notice_data.notice_type = "spn"
    
    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        fn.load_page(page_details, page_details_url)
        logging.info(page_details_url)
    except:
        pass
        
    try:
        title_en = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/h1"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info(notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.reference = page_details.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div[1]/mark').text
        notice_data.reference = notice_data.reference.split('招标编号：')[1].split(']')[0]
        logging.info(notice_data.reference)
    except:
        pass
    
    try:
        notice_data.buyer = page_details.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[2]/div[1]/i[2]').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
        logging.info(notice_data.buyer)
    except:
        pass
    
    try:
        notice_data.published_date = page_details.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div[1]/i[1]/').text
        notice_data.published_date = GoogleTranslator(source='auto', target='en').translate(notice_data.published_date)
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)
    except:
        try:
            notice_data.published_date = page_details.find_element(By.XPATH,'/html/body/div/div/div[2]/div[2]/div[1]/i[1]').text
            notice_data.published_date = GoogleTranslator(source='auto', target='en').translate(notice_data.published_date)
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)
        except:
            pass

    try:
        end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
        notice_data.end_date = end_date.strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)
    except:
        pass 

    try:
        notice_data.est_cost = page_details.find_element(By.XPATH,'//*[contains(text(), "预算金额")]').text
        notice_data.est_cost = notice_data.est_cost.split("预算金额：")[1]
        notice_data.est_cost = GoogleTranslator(source='auto', target='en').translate(notice_data.est_cost)
        notice_data.est_cost=re.sub("[^\d\.]", "", notice_data.est_cost) 
        logging.info(notice_data.est_cost) 
    except:
        pass
    
    try:
        category = page_details.find_element(By.XPATH, '//*[contains(text(), "项目名称")]//following::p').text
        notice_data.category = category.split('采购方式：')[1]
        notice_data.category = GoogleTranslator(source='auto', target='en').translate(notice_data.category)
        logging.info(notice_data.category) 
    except:
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@class="detail_content"]'))).get_attribute('outerHTML')
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.title_en is not None :
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

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
    url = 'http://www.gzswbc.com/bidding/index.jhtml'
    fn.load_page(page_main, url)
    logging.info(url)

    for i in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@class="content_box"]/ol/li[1]/a'))).text
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@class="content_box"]/ol').find_elements(By.CSS_SELECTOR,'li'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

        try:
            nxt_page = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[3]/a[1]'))).click()
            logging.info("NEXT PAGE") 
            MAX_LOAD_DRIVER_ATTEMPTS = 3
            nxt_page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@class="content_box"]/ol/li[1]/a'))).text
            for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS):
                if nxt_page_check != page_check:
                    break
                else:
                    time.sleep(20)
                    pass
        except:
            logging.info("NO NEXT PAGE")
            break
                
 
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(script_name, notice_count, 0, 'XML uploaded')
    
except Exception as e:
    try:
        fn.error_log(script_name, e)
        fn.session_log(script_name, notice_count, 0, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("asia") 