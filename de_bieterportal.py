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
MAX_NOTICES = 2000

ml_cpv = 0
notice_count = 0
script_name = 'de_bieterportal'
output_xml_file = common.OutputXML.OutputXML(script_name)


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global script_name
    notice_data = NoticeData()
    wait = WebDriverWait(page_main, 10) 
    notice_data.performance_country = 'Germany'
    notice_data.contact_country = 'Germany'
    notice_data.procurement_method = "Other"
    notice_data.language = "DE"  
    
    if(url == 'https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vergaben'):
        notice_data.notice_type = "spn"
    elif(url == 'https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/zuschlagsbekanntmachungen'):
        notice_data.notice_type = "ca"
    elif(url == 'https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vorinformationen'):
        notice_data.notice_type = "pp"
    logging.info(notice_data.notice_type)
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.color-primary.card-title-style"))).text
        notice_data.title_en = GoogleTranslator(source='de', target='en').translate(title_en)
        logging.info('title_en :'+notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.contracting-authority-style > span'))).text
        logging.info('buyer :'+notice_data.buyer)
    except:
        pass
    
    try:
        notice_data.reference =  WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div:nth-child(1) > div:nth-child(1) > label'))).text
        logging.info('reference :'+notice_data.reference)
    except:
        pass

    if (notice_data.notice_type == "spn" or notice_data.notice_type == "ca"):  
        WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.button-area-style > button > span.mat-button-wrapper "))).click()
        time.sleep(5)
        page_details_url = page_main.current_url
        notice_data.notice_url = page_details_url
        logging.info("page_details_url " +page_details_url)

    if notice_data.notice_type == "spn" :
        try:
            published_date = wait.until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(), "Bekanntmachung")]//following::div'))).text
            published_date = published_date.split(",")[0]
            notice_data.published_date = datetime.strptime(published_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            logging.info('published_date :'+notice_data.published_date)
        except:
            pass
            
    elif notice_data.notice_type == "ca":
        try:
            published_date = page_main.find_element(By.XPATH,'//*[contains(text(), "Veröffentlichungsdatum")]//following::div').text
            published_date = published_date.split(",")[0]
            notice_data.published_date = datetime.strptime(published_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            logging.info('published_date :'+notice_data.published_date)
        except:
            pass
    else:
        try:
            published_date = tender_html_element.find_element(By.CSS_SELECTOR,'div:nth-child(2) > div:nth-child(1) > label').text 
            published_date = published_date.split(",")[0]
            notice_data.published_date = datetime.strptime(published_date,'%d.%m.%Y').strftime('%Y/%m/%d')
            logging.info('published_date :'+notice_data.published_date)
        except:
            pass
     
    if (notice_data.notice_type == "spn"):
        try:
            end_date = wait.until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(), "Einreichungsfrist")]//following::div'))).text 
            end_date = end_date.split(",")[0]
            notice_data.end_date  = datetime.strptime(end_date ,'%d.%m.%Y').strftime('%Y/%m/%d')
            logging.info('end_date :'+notice_data.end_date)
        except:
            try:
                end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
                notice_data.end_date = end_date.strftime('%Y/%m/%d')
                logging.info('end_date :'+notice_data.end_date)
            except:
                pass 
        
    if (notice_data.notice_type == "pp"):
        end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(365)
        notice_data.end_date = end_date.strftime('%Y/%m/%d')
        logging.info('end_date :'+notice_data.end_date) 
            
        id=page_main.find_element(By.CSS_SELECTOR,'dashboard-project-prior-card > mat-card').get_attribute('id')
        id= id[-36:]
        notice_data.notice_url="https://bieterportal.noncd.db.de/evergabe.bieter/api/supplier/subproject/"+str(id)+"/attachment/contractnotice"
        logging.info('notice_url : '+notice_data.notice_url)
  
    try:
        notice_data.address = page_main.find_elements(By.XPATH,'//*[contains(text(), "Adresse")]//following::div').text
        logging.info('address :'+str(notice_data.address))
    except:
        pass
    
    if (notice_data.notice_type == "ca"):
        try:
            notice_data.contact_phone = page_main.find_elements(By.XPATH,"//*[contains(text(),'Telefon')]//following::div").text
            logging.info('contact_phone :'+str(notice_data.contact_phone))
        except:
            pass
        
        try:
            notice_data.contact_email = page_main.find_element(By.XPATH,"//*[contains(text(),'E-Mail')]//following::div").text
            logging.info('contact_email :'+str(notice_data.contact_email))
        except:
            pass
        
        try:
            notice_data.award_company =  page_main.find_element(By.XPATH,"//*[contains(text(),'Firma')]//following::div").text
            logging.info('award_company :'+str(notice_data.award_company))
        except:
            pass
        
        try:
            notice_data.awarding_company_address =  page_main.find_element(By.XPATH,"/html/body/app/supplier-portal-frame/div/mat-sidenav-container/mat-sidenav-content/div/project-award-details/div/div/div/mat-card/mat-card-content/div/div[22]/div[2]/div").text
            logging.info('awarding_company_address :'+str(notice_data.awarding_company_address))
        except:
            pass
        
        
        if notice_data.award_company != None:
            notice_data.awarding_company_country =  "German"   
            logging.info('awarding_company_country :'+str(notice_data.awarding_company_country))

    try:
        notice_data.notice_text = WebDriverWait(page_main, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/app/supplier-portal-frame/div/mat-sidenav-container/mat-sidenav-content/div/project-details/div/div[2]/div[1]/mat-card/mat-card-content/div'))).get_attribute('outerHTML')
    except:
        try:
            notice_data.notice_text = WebDriverWait(page_main, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/app/supplier-portal-frame/div/mat-sidenav-container/mat-sidenav-content/div/project-award-details/div/div/div/mat-card/mat-card-content/div'))).get_attribute('outerHTML')
        except:
            pass
        
    notice_data.cleanup()

    if (notice_data.notice_type == "spn" or notice_data.notice_type == "ca"):  
        page_main.back()
        time.sleep(5)
        
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
th = date.today() - timedelta(20)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:    
    urls = ['https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vergaben',
            'https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/zuschlagsbekanntmachungen',
            'https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vorinformationen']

    for url in urls:
        logging.info('----------------------------------')
        fn.load_page(page_main, url) 
        logging.info(url)
        for i in range(1,25):  
            page_check = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div:nth-child(1) > div:nth-child(1) > label'))).text
            rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@id="project-vertical-container"]'))).find_elements(By.CSS_SELECTOR,'div.resolve-flex-column')
            length_rows=len(rows)
            for k in range(0, length_rows):
                tender_html_element = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="project-vertical-container"]'))).find_elements(By.CSS_SELECTOR, 'div.resolve-flex-column')[k]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break 
                    
            if notice_data.published_date is not None and notice_data.published_date < threshold:
                break
                
            try:
                nxt_page = page_main.find_element(By.CSS_SELECTOR,'button.mat-focus-indicator.mat-tooltip-trigger.mat-paginator-navigation-next.mat-icon-button.mat-button-base span.mat-button-wrapper').click()        
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div:nth-child(1) > div:nth-child(1) > label'),page_check))
                logging.info("---Next Page---")
            except:
                logging.info("---No Next Page---")
                break 
          
                    
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log(script_name, notice_count, 0, ml_cpv, 'XML uploaded')
    
except Exception as e:
    try:
        fn.error_log(script_name, e)
        fn.session_log(script_name, notice_count, 0, ml_cpv, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    output_xml_file.copyFinalXMLToServer("europe")
