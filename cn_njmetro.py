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
script_name = "cn_njmetro"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'China'
    notice_data.contact_country = 'China'
    notice_data.procurement_method = "Other"
    notice_data.language = "CN"  
    notice_data.buyer_internal_id = "7130650"
    notice_data.notice_type = "spn"
        
    try: 
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' li.tender_tli01 > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info("page_details_url " +notice_data.notice_url)

        try:
            notice_data.published_date = page_details.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[4]/div/div/div[2]').text
            notice_data.published_date = GoogleTranslator(source='auto', target='en').translate(notice_data.published_date)
            notice_data.published_date = notice_data.published_date.split('Source: Time:')[1].split(' Visits')[0]
            try:
                notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
            except:
                notice_data.published_date = datetime.strptime(notice_data.published_date ,' %Y-%m-%d').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

        try:
            title_en = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[1]/div[4]/div/div/div[1]"))).text
            notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        except:
            pass

        try:
            notice_data.buyer = 'Nanjing Metro Operation Co., Ltd.'
        except:
            pass

        try:
            reference = page_details.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[4]/div/div/div[3]/p[1]/span').text
            ref = reference.split('：')[1]
            reference = ref.split('）')[0]
            if len(reference)>3:
                notice_data.reference = reference
        except:
            pass

        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div[4]/div/div'))).get_attribute('outerHTML')
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
    url = 'https://www.njmetro.com.cn/njdtweb/portal/article-list/bycolumnId.do?columnId=8a808007651c972001651d88ebe20001&tag=zbgg&pageCurrent=1'
    fn.load_page(page_main, url)
    logging.info(url)
    

    for i in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[1]/div[4]/div[2]/ul/li/ul[1]/li[1]/a'))).text
        for tender_html_element in page_main.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[4]/div[2]/ul').find_elements(By.CSS_SELECTOR,'li > ul'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break

        try:
            nxt_page = page_main.find_element(By.XPATH,'/html/body/div[2]/div[1]/div[4]/div[3]/div/div/ul/li[9]/a').click()        
            logging.info("---Next Page---")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div[1]/div[4]/div[2]/ul/li/ul[1]/li[1]/a'),page_check))
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
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("asia") 