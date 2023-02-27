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
script_name = "cn_czi"
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

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info('title :'+notice_data.title_en)
    except:
        pass
    
    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
        fn.load_page(page_details, page_details_url)
        notice_data.notice_url = page_details_url
        logging.info("page_details_url " +page_details_url)
    except:
        pass
    
    try:
        published_date = tender_html_element.find_element(By.CSS_SELECTOR,'span').text
        published_date = re.findall('\d{4}-\d+-\d+',published_date)[0]
        notice_data.published_date = datetime.strptime(published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info('published_date :'+notice_data.published_date)  
    except:
        pass
    
    try:
        iframe = page_details.find_element(By.XPATH,'//*[@id="detail_frame"]')
        page_details.switch_to.frame(iframe)
        text = page_details.find_element(By.XPATH, '/html/body').text
    except:
        pass
    
    try:
        reference = text.split('项目编号：')[1]
        reference = GoogleTranslator(source='auto', target='en').translate(reference)
        notice_data.reference = reference.split('\n')[0]
        logging.info('reference :'+notice_data.reference)
    except:
        try:
            reference = page_details.find_element(By.XPATH,'//*[contains(text(), "采购项目编号")]').text
            reference = GoogleTranslator(source='auto', target='en').translate(reference)
            notice_data.reference = reference.split('：')[1]
            logging.info('reference :'+notice_data.reference)
        except:
            pass

    try:
        buyer = text.split('采购代理机构信息')[1]
        try:
            buyer = buyer.split('名 称：')[1]  
        except:
            buyer = buyer.split('名    称：')[1]
        buyer = buyer.split('\n')[0]
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info('buyer: '+notice_data.buyer)
    except:
        try:
            buyer = text.split('采购代理机构名称：')[1]
            buyer = buyer.split('\n')[0]
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info('buyer: '+notice_data.buyer)
        except:
            pass

    if url==urls[0]:
        notice_data.notice_type = 'ca'
        notice_data.awarding_company_country = "CN"

        try: 
            notice_data.award_company = page_details.find_element(By.CSS_SELECTOR, 'td.code-winningSupplierName').text
            notice_data.award_company = GoogleTranslator(source='auto', target='en').translate(notice_data.award_company)
            logging.info('award_company :'+notice_data.award_company)
        except:
            pass

        try:
            notice_data.awarding_company_address = page_details.find_element(By.CSS_SELECTOR, 'td.code-winningSupplierAddr').text
            notice_data.awarding_company_address = GoogleTranslator(source='auto', target='en').translate(notice_data.awarding_company_address)
            logging.info('awarding_company_address :'+notice_data.awarding_company_address)
        except:
            pass
 
        try:
            est_value = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td.code-summaryPrice"))).text
            est_value = GoogleTranslator(source='auto', target='en').translate(notice_data.est_cost)
            notice_data.est_cost = re.sub("[^\d\.]", "", est_value)
            logging.info('est_cost :'+notice_data.est_cost)
        except:
            pass
          
    else:
        notice_data.notice_type = 'spn'
        notice_data.update = True
             
    try:
        rsrs = page_details.find_elements(By.CSS_SELECTOR,'li > p > a')
        notice_data.resource_url.clear()
        for rsr in rsrs:
            resource = rsr.get_attribute('href')
            notice_data.resource_url.append(resource)
        logging.info(notice_data.resource_url)
    except:
        pass

    try:
        notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div'))).get_attribute('outerHTML')
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
    urls =[ 'http://czj.hangzhou.gov.cn/col/col1677847/index.html',
            'http://czj.hangzhou.gov.cn/col/col1677848/index.html',
            'http://czj.hangzhou.gov.cn/col/col1677849/index.html']
    
    for url in urls:
        logging.info('----------------------------------')
        fn.load_page(page_main, url)
        logging.info(url)
        for i in range(1,25):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="7293371"]/div/li[1]/a'))).text
            rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="7293371"]/div'))).find_elements(By.CSS_SELECTOR,'li')
            length_rows=len(rows)
            for k in range(0, length_rows-1):
                tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="7293371"]/div'))).find_elements(By.CSS_SELECTOR,'li')[k]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
            if notice_data.published_date is not None and notice_data.published_date < threshold:
                break

            try:
                nxt_page = page_main.find_element(By.XPATH,'//*[@id="7293371"]/table/tbody/tr/td/table/tbody/tr/td[6]/a').click()        
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="7293371"]/div/li[1]/a'),page_check))
                logging.info("---Next Page---")
            except:
                logging.info("---No Next Page---")
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