import logging
import re
import time
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import common.OutputXML
import functions as fn
import ml.cpv_classifier as classifier
from common.NoticeData import NoticeData

notice_count = 0
MAX_NOTICES = 2000
global notice_type
script_name = 'mx_compranet'
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = NoticeData() 
    wait = WebDriverWait(page_main, 20)

    notice_data.performance_country = 'Mexico'
    notice_data.contact_country = 'Mexico'
    notice_data.procurement_method = "Other"
    notice_data.language = "ES"
    notice_data.notice_type = notice_type
    logging.info(notice_data.notice_type)
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        logging.info(notice_data.reference)
    except:
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        logging.info(notice_data.category)
    except:
        pass
        
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        logging.info(notice_data.buyer)
    except:
        pass

    try:
        title_en = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        logging.info(notice_data.title_en)
    except:
        pass
    
    notice_data.notice_url = url
    
    id = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(5) > a').get_attribute('onclick')
    id = id.split("('")[1]
    id = id.split("',")[0]
    notice_data.resource_url = 'https://compranet.hacienda.gob.mx/esop/toolkit/opportunity/current/'+str(id)+'/detail.si'
    fn.load_page(page_details, notice_data.resource_url)
    logging.info("page_details_url " +notice_data.resource_url)

    try:
        published_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Fecha de publicación del anuncio (Convocatoria / Invitación / Adjudicación / Proyecto de Convocatoria)')]//following::div").text
        published_date = re.findall('\d+/\d+/\d{4}',published_date)[0]
        notice_data.published_date =  datetime.strptime(published_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)
    except:
        pass

    try:
        end_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Plazo de participación o vigencia del anuncio')]//following::div").text
        end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date =  datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)
    except:
        pass

    try:
        notice_data.contact_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Correo Electrónico del Operador en la UC')]//following::div").text
        logging.info(notice_data.contact_email)
    except:
        pass

    try:
        notice_data.contact_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Nombre del Operador en la UC')]//following::div").text
        logging.info(notice_data.contact_name)
    except:
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.ID, 'container').get_attribute('outerHTML')
    except:
        pass

    notice_data.cleanup()
    
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    time.sleep(3)
    ##Added sleep site blocking issue Too many request...

    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    logging.info('-------------------------------')
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1

# ----------------------------------------- Main Body

page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
try:

    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    datetemp = th.strftime('%d/%m/%Y')
    logging.info("Scraping from or greater than: " + threshold)
    
    url = 'https://compranet.hacienda.gob.mx/web/login.html'

    logging.info('----------------------------------')
    logging.info(url)
    fn.load_page(page_main, url)
    fn.load_page(page_details, url)
    
    WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navbar"]/ul/li[4]/a'))).click()   
    WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="navbar"]/ul/li[4]/ul/li[1]/a'))).click()
    page_details.switch_to.window(page_details.window_handles[1])
    
    WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="navbar"]/ul/li[4]/a'))).click()   
    WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="navbar"]/ul/li[4]/ul/li[1]/a'))).click()
    page_main.switch_to.window(page_main.window_handles[1])

    for method_type in range(0,2):
        
        for page_no in range(2,25):
            if method_type == 0:
                notice_type = "spn"
            else:
                notice_type = "ca"
                
            page_check = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(3)'))).text
            rows = page_main.find_element(By.XPATH,'//*[@id="OpportunityListManager"]/div/table/tbody[2]').find_elements(By.CSS_SELECTOR, 'tr')
            length = len(rows)
            logging.info(length)

            for k in range(0,length):
                tender_html_element = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="OpportunityListManager"]/div/table/tbody[2]'))).find_elements(By.CSS_SELECTOR, 'tr')[k]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            try:
                nxt_page = page_main.find_element(By.CSS_SELECTOR,'a.NavBtnForward').click()
                logging.info("NEXT PAGE") 
                MAX_LOAD_DRIVER_ATTEMPTS = 3
                nxt_page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(3)'))).text
                for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS):
                    if nxt_page_check != page_check:
                        break
                    else:
                        time.sleep(10)
                        pass
            except:
                logging.info("no next page")
                break
        try:
            WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="navigationSecondLevel"]/div/div/div[2]/a'))).click()
            logging.info("CA")
            MAX_LOAD_DRIVER_ATTEMPTS = 3
            nxt_page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(3)'))).text
            for loop_counter in range(1, MAX_LOAD_DRIVER_ATTEMPTS):
                if nxt_page_check != page_check:
                    break
                else:
                    time.sleep(20)
                    pass
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
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("latin")