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
MAX_NOTICES = 2000
notice_count = 0
output_xml_file = common.OutputXML.OutputXML("br_compraspara")

def extract_and_save_notice(tender_html_element):
    global notice_count
    notice_data = NoticeData()
    notice_data.performance_country = 'Brazil'
    notice_data.contact_country = 'Brazil'
    notice_data.language = "PT"
    notice_data.procurement_method = "Other"
    notice_data.notice_type = 'spn'
    notice_data.notice_url = url
    try:
        end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('Data/Hora de Abertura: ')[1].split('\n')[0]
        end_date = re.findall('\d+/\d+/\d{4}',end_date)[0]
        notice_data.end_date = datetime.strptime(end_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.end_date)
    except:
        pass
    if notice_data.end_date is not None and notice_data.end_date < threshold:
        return
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('Nº/Exercício: ')[1].split('\n')[0]
    except:
        pass

    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('Órgão: ')[1].split('\n')[0]
    except:
        pass            

    try:
        title_en = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('Objeto: ')[1].split('\n')[0]
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        pass

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3) a').click()
        time.sleep(5)
        try:
            notice_data.notice_text += WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="form_view_licitacao"]'))).get_attribute('outerHTML')
        except:
            pass
        page_main.find_element(By.XPATH,'//*[@id="dialog_view_licitacao"]/div[1]/a').click()
        time.sleep(5)
    except:
        pass
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category)
    notice_data.cleanup()
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
page_main = fn.init_chrome_driver()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    url = 'https://www.sistemas.pa.gov.br/compraspara/public/licitacao_list.xhtml' 
    logging.info('----------------------------------')
    logging.info(url)
    fn.load_page(page_main, url)
    
    for page_no in range(1,10):
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result_form:list_data"]/tr[1]/td[2]'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result_form:list_data"]'))).find_elements(By.CSS_SELECTOR, 'tr')
        length = len(rows)
        for k in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="result_form:list_data"]'))).find_elements(By.CSS_SELECTOR, 'tr')[k]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
        try:
            next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="result_form:list_paginator_bottom"]/span[5]/span')))
            page_main.execute_script("arguments[0].click();",next_page)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="result_form:list_data"]/tr[1]/td[2]'),page_check))
            logging.info("Next Page")
        except:
            logging.info("No Next Page")
            break
    
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log('br_compraspara', notice_count, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log('br_compraspara', e)
        fn.session_log('br_compraspara', notice_count, 'Script error')
    except:
        pass
    raise e
finally:
    page_main.quit()
    output_xml_file.copyFinalXMLToServer("latin")
