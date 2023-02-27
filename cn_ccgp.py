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
script_name = "cn_ccgp"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'China'
    notice_data.contact_country = 'China'
    notice_data.language = "CN"  
    notice_data.notice_type = "spn"
    
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.XPATH, 'em'))).text
        notice_data.published_date = re.findall('\d{4}-\d+-\d+',notice_data.published_date)[0]
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info('published_date: '+notice_data.published_date) 
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info('title_en: '+notice_data.title_en)
    except:
        pass
  
    try:
        buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'em:nth-of-type(3)'))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info('buyer: '+notice_data.buyer)
    except:
        pass

    try:
        notice_data.notice_url = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))).get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        logging.info(notice_data.notice_url)
        
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[2]'))).get_attribute('outerHTML')
            temp = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[2]'))).text
        except:
            pass
        
        try:
            notice_data.reference = temp.split('项目编号：')[1]
            notice_data.reference = notice_data.reference.split('\n')[0]
            logging.info('reference: ' + notice_data.reference)
        except:
            pass

        try:
            temp = temp.split('提交投标文件截止时间、开标时间和地点')[1]
            temp = GoogleTranslator(source='auto', target='en').translate(temp)
            end_date = re.findall('\w+ \d+, \d{4}',temp)[0]
            notice_data.end_date = datetime.strptime(end_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info('end_date: ' + notice_data.end_date)
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

try:        
    for page_no in range(0,12):
        if (page_no == 0):
            url = 'http://www.ccgp.gov.cn/cggg/zygg/gkzb/index.htm'
        else:
            url = 'http://www.ccgp.gov.cn/cggg/zygg/gkzb/index_' + str(page_no) + '.htm'
        fn.load_page(page_main, url)
        logging.info(url)
        for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul').find_elements(By.CSS_SELECTOR,'li'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
        if notice_data.published_date is not None and notice_data.published_date < threshold:
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