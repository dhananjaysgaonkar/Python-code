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
script_name = "lv_eis"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'Latvia'
    notice_data.contact_country = 'Latvia'
    notice_data.procurement_method = 'Other'
    notice_data.language = "LV"  
    
    try:
        notice_data.published_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2)'))).text
        notice_data.published_date = re.findall('\d+.\d+.\d{4}',notice_data.published_date)[0]
        try:
            notice_data.published_date = datetime.strptime(notice_data.published_date,'%d.%m.%Y').strftime("%Y/%m/%d")
        except:
            notice_data.published_date = datetime.strptime(notice_data.published_date,'%m.%d.%Y').strftime("%Y/%m/%d")
        logging.info('published_date = '+notice_data.published_date)
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:  
        notice_data.end_date = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(5)'))).text
        notice_data.end_date = re.findall('\d+.\d+.\d{4}',notice_data.end_date)[0]
        try:
            notice_data.end_date = datetime.strptime(notice_data.end_date,'%d.%m.%Y').strftime("%Y/%m/%d")
        except:
            notice_data.end_date = datetime.strptime(notice_data.end_date,'%m.%d.%Y').strftime("%Y/%m/%d")
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2)'))).text
    except:
        pass

    try:
        notice_data.title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(3)'))).text
        if('expression of interest' in title_en.lower() or 'eoi' in title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
    except:
        pass
    
    try:
        notice_data.buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(4)'))).text
        logging.info('buyer = '+notice_data.buyer)
    except:
        pass
    
    try: 
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)

        WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="uxSubjectDescriptionTitle"]/h4/a'))).click()
        WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="uxActualProcurementDocumentsTitle"]/h4/a'))).click()
        time.sleep(5)

        try:
            notice_data.cpvs.clear()
            cpvs = page_details.find_element(By.XPATH,'//*[@id="uxSubjectDescription"]/div/div[3]/div[1]/span').text
            if(' ' in cpvs):
                cpvss = cpvs.split(' ')
                for cpv in cpvss:
                    cpv = cpv.split('-')[0].strip()
                    cpv = re.sub("[^\d]", "", cpv)
                    if cpv != '':
                        notice_data.cpvs.append(cpv)
            logging.info(notice_data.cpvs)
        except:
            pass

        notice_data.address = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="SubjectDescription_ShipmentAddress_Title"]'))).text

        try: 
            rsrs = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#ActualDocumentsRepeater > div.repeater-viewport > div.repeater-canvas > div > div'))).find_elements(By.CSS_SELECTOR, 'a')
            notice_data.resource_url.clear()
            for rsr in rsrs[::2]:
                rsr.click()
                rsr = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ViewDocumentModel_FilesRepeater"]/div/div[1]/div/div/table/tbody/tr'))).find_elements(By.CSS_SELECTOR, 'a')
                for rs in rsr:
                    resource = rs.get_attribute('href')
                    notice_data.resource_url.append(resource)
                    WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="document-container"]/div[2]/div/div[1]/button'))).click()
        except:
            pass

        try: 
            notice_data.notice_text = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main"]/div[4]'))).get_attribute('outerHTML')
        except:
            pass

    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)

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
    url = 'https://www.eis.gov.lv/EKEIS/Supplier/Index'
    fn.load_page(page_main, url)
    logging.info(url)

    for page_no in range(1,3):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-child(2)'))).text
        for tender_html_element in WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ResultsRepeater"]/div[1]/div[1]/div/div/table/tbody'))).find_elements(By.CSS_SELECTOR,'tr'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
            
        try:
            nxt_page = page_main.find_element(By.XPATH,'//*[@id="Resultsfooter-next-page"]').click()        
            logging.info("---Next Page---")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'td:nth-child(2)'),page_check))
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
    output_xml_file.copyFinalXMLToServer("europe") 