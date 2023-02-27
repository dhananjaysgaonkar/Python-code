import logging
import re
import time
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData

MAX_NOTICES = 2000
SCRIPT_NAME = "ml_malipages"
notice_count = 0
output_xml_file = common.OutputXML.OutputXML(SCRIPT_NAME)

def extract_and_save_notice(tender_html_element,tid):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Mali'
    notice_data.contact_country = 'Mali'
    notice_data.procurement_method = "Other"
    notice_data.language = "FR"
    notice_data.notice_type = 'spn'
    
    try:
        published_date = tender_html_element.find_element(By.XPATH, '//*[@id="page"]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']/div[3]').text
        published_date = re.findall('\d+/\d+/\d{4}', published_date)[0]
        notice_data.published_date = datetime.strptime(published_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)
    except:
        pass

    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:
        end_date = tender_html_element.find_element(By.XPATH, '//*[@id="page"]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']/div[3]/time[2]').text
        notice_data.end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(notice_data.end_date, '%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        pass

    try:
        notice_data.title_en = tender_html_element.find_element(By.XPATH, '//*[@id="page"]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']/div[2]/p/a').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.XPATH, '//*[@id="page"]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']/div[2]/div/span[1]/a').text
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.XPATH,'//*[@id="page"]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']/div[2]/p/a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url) 
        
        try:
            notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="page"]/main/div/div/div[1]/div[1]').text
        except:
            pass
    except:
        notice_data.notice_url = url

    try: 
        if notice_data.cpvs == [] and notice_data.title_en is not None:
            notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)
    except:
        pass

    notice_data.cleanup()
    logging.info('-------------------------------')
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    
# ----------------------------------------- Main Body
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
wait = WebDriverWait(page_main, 20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    for page_number in range(1,3):
        url = "https://www.malipages.com/appels-offres/avis-dappel-doffres/page/"+str(page_number)+"/"
        logging.info('----------------------------------')
        fn.load_page(page_main, url)
        logging.info(url)
        
        for tid in range(1, 12):
            if tid != 2:
                css ='/html/body/div[2]/div[1]/main/div/div/div[1]/div[1]/ul/li['+str(tid)+']'
            else:
                continue
            tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH, css)))
            extract_and_save_notice(tender_html_element,tid)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.published_date is not None and  notice_data.published_date < threshold:
                break
                
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(SCRIPT_NAME, notice_count, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log(SCRIPT_NAME, e)
        fn.session_log(SCRIPT_NAME, notice_count, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("africa")
