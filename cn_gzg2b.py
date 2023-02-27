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
script_name = "cn_gzg2b"
output_xml_file = common.OutputXML.OutputXML(script_name)
global index

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
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td a"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info(notice_data.title_en)
    except:
        pass
    
    try:
        id = tender_html_element.find_element(By.CSS_SELECTOR,'td a').get_attribute('id')
        page_details_url = 'https://gzg2b.gzfinance.gov.cn/gzgpimp/portalsys/portal.do?method=pubinfoView&&info_id='+str(id)+'&&porid=zbgg&t_k=null'
        fn.load_page(page_details, page_details_url)
        notice_data.notice_url = page_details_url
        logging.info("page_details_url " +page_details_url)
    except:
        pass
    
    
    if index == 2:
        notice_type = 'rei'
        try:
            buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="template"]/div/p[3]'))).text
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info(notice_data.buyer)
        except:
            pass
        
        try:
            published_date = tender_html_element.find_element(By.XPATH,'td[2]').text
            published_date = GoogleTranslator(source='auto', target='en').translate(published_date)
            notice_data.published_date = datetime.strptime(published_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass
    
        try:
            notice_data.est_cost = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(5)"))).text
            logging.info(notice_data.est_cost)
        except:
            pass
        
    elif index == 3:
        notice_type = 'spn'
        try:
            buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="template"]/div/p[24]'))).text
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info(notice_data.buyer)
        except:
            pass
        
        try:
            published_date = tender_html_element.find_element(By.XPATH,'td[2]').text
            published_date = GoogleTranslator(source='auto', target='en').translate(published_date)
            notice_data.published_date = datetime.strptime(published_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass

        try:
            end_date = page_details.find_element(By.XPATH,'//*[@id="template"]/div/p[9]').text
            end_date = GoogleTranslator(source='auto', target='en').translate(end_date)
            end_date = re.findall('\w+ \d+, \d{4}',end_date)[0]
            notice_data.end_date = datetime.strptime(end_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.end_date)  
        except:
            pass

        try:
            rsrs = page_details.find_elements(By.CSS_SELECTOR,'div:nth-child(4) a')
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                notice_data.resource_url.append(resource)
            logging.info(notice_data.resource_url)
        except:
            pass
    
    elif index == 6:
        notice_type = 'spn'
        
        try:
            reference = page_details.find_element(By.XPATH,'//*[contains(text(), "项目编号")]').text
            notice_data.reference = reference.split('：')[1]
            logging.info(notice_data.reference)
        except:
            try:
                reference = page_details.find_element(By.XPATH,'//*[@id="noticeArea"]/p[2]').text
                notice_data.reference = reference.split('：')[1]
                logging.info(notice_data.reference)
            except:
                pass

        try:
            buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="noticeArea"]/p[17]'))).text
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info(notice_data.buyer)
        except:
            pass
        
        try:
            published_date = tender_html_element.find_element(By.XPATH,'td[2]').text
            published_date = GoogleTranslator(source='auto', target='en').translate(published_date)
            notice_data.published_date = datetime.strptime(published_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass
        
        try:
            end_date = page_details.find_element(By.XPATH,'//*[@id="template"]/div/p[11]').text
            end_date = GoogleTranslator(source='auto', target='en').translate(end_date)
            end_date = end_date.split('to ')[1]
            notice_data.end_date = datetime.strptime(end_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.end_date)  
        except:
            pass
        
        try:
            notice_data.est_cost = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(6)"))).text
            logging.info(notice_data.est_cost)
        except:
            pass

    elif index == 7:
        notice_type = 'spn'
        notice_data.update = True
        
        try:
            reference = page_details.find_element(By.XPATH,'//*[contains(text(), "项目编号")]').text
            notice_data.reference = reference.split('：')[1]
            logging.info(notice_data.reference)
        except:
            try:
                reference = page_details.find_element(By.XPATH,'//*[@id="noticeArea"]/p[2]').text
                notice_data.reference = reference.split('：')[1]
                logging.info(notice_data.reference)
            except:
                pass
        
        try:
            buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="noticeArea"]/p[11]'))).text
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info(notice_data.buyer)
        except:
            pass
        
        try:
            published_date = tender_html_element.find_element(By.XPATH,'td[2]').text
            published_date = GoogleTranslator(source='auto', target='en').translate(published_date)
            notice_data.published_date = datetime.strptime(published_date ,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass
        
    elif index == 8:
        notice_type = 'ca'
        notice_data.awarding_company_country = "CN"
        
        try:
            reference = page_details.find_element(By.XPATH,'//*[contains(text(), "项目编号")]').text
            notice_data.reference = reference.split('：')[1]
            logging.info(notice_data.reference)
        except:
            try:
                reference = page_details.find_element(By.XPATH,'//*[@id="noticeArea"]/h4[1]').text
                notice_data.reference = reference.split('：')[1]
                logging.info(notice_data.reference)
            except:
                pass

        try:
            published_date = tender_html_element.find_element(By.XPATH,'td[2]').text
            published_date = re.findall('\d{4}-\d+-\d+',published_date)[0]
            notice_data.published_date = datetime.strptime(published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
            logging.info(notice_data.published_date)  
        except:
            pass
        
        try:
            text = page_details.find_element(By.XPATH, '//*[@id="template"]/div').text
        except:
            pass

        try:
            buyer = text.split('采购代理机构信息')[1]
            buyer = text.split('称：')[1]
            buyer = buyer.split('\n')[0]
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
            logging.info(notice_data.buyer)
        except:
            pass
            
        try:
            notice_data.award_company = page_details.find_element(By.CSS_SELECTOR, "td:nth-of-type(1)").text
            notice_data.award_company = GoogleTranslator(source='auto', target='en').translate(notice_data.award_company)
            logging.info(notice_data.award_company)
        except:
            pass
        
        try:
            notice_data.awarding_company_address = page_details.find_element(By.CSS_SELECTOR, "td:nth-of-type(2)").text
            notice_data.awarding_company_address = GoogleTranslator(source='auto', target='en').translate(notice_data.awarding_company_address)
            logging.info(notice_data.awarding_company_address)
        except:
            pass
        
        try:
            rsrs = page_details.find_elements(By.CSS_SELECTOR,'div:nth-child(4) a')
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                notice_data.resource_url.append(resource)
            logging.info(notice_data.resource_url)
        except:
            pass
              
    notice_data.notice_type = notice_type
     
    try:
        notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="template"]/div'))).get_attribute('outerHTML')
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.title_en is not None :
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None:
        if notice_data.published_date < threshold:
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
    url = 'https://gzg2b.gzfinance.gov.cn/gzgpimp/portalindex.do?method=goInfogsgg&linkId=gsgg'
    fn.load_page(page_main, url)
    logging.info(url)
    tab_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/div[2]/table/tbody/tr[1]/td[1]/a'))).text

    for index in [2,3,6,7,8]:
        try: 
            nxt_tab = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="categoryList"]/ul/li['+str(index)+']/a'))).click()      
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/div[2]/table/tbody/tr[1]/td[1]/a'),tab_check))
            for i in range(1,25):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/div[2]/table/tbody/tr[1]/td[1]/a'))).text
                rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="protalInfoid"]/tbody'))).find_elements(By.CSS_SELECTOR,'tr')
                length_rows=len(rows)
                for k in range(0, length_rows-1):
                    tender_html_element = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="protalInfoid"]/tbody'))).find_elements(By.CSS_SELECTOR,'tr')[k]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:
                    nxt_page = page_main.find_element(By.XPATH,'//*[@id="protalInfoid-footer"]/div/div[1]/ul/li[8]/a').click()        
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/div[3]/div[2]/div[2]/table/tbody/tr[1]/td[1]/a'),page_check))
                    logging.info("---Next Page---")
                except:
                    logging.info("---No Next Page---")
                    break     
        except:
            pass
        

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