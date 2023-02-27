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
output_xml_file = common.OutputXML.OutputXML("ec_compraspublicas")

def extract_and_save_notice(tender_html_element):
    global notice_count
    notice_data = NoticeData()
    notice_data.performance_country = 'Ecuador'
    notice_data.contact_country = 'Ecuador'
    notice_data.language = "ES"
    notice_data.procurement_method = "Other"
    notice_data.currency = 'USD'
    
    try:
        published_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        published_date = re.findall('\d{4}-\d+-\d+',published_date)[0]
        notice_data.published_date = datetime.strptime(published_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.published_date)
    except:
        pass

    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:
        status = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
        if ('Adjudicada' in status):
            notice_data.notice_type = 'ca'
        else:
            notice_data.notice_type = 'spn'
    except:
        notice_data.notice_type = 'spn'
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
    except:
        pass

    try:
        title_en = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.title_en = GoogleTranslator(source='es', target='en').translate(title_en)
    except:
        pass
    
    try:
        est_cost = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.est_cost = re.sub("[^\d\.]", "", est_cost)
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1) a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            notice_data.notice_text += WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ladoDer"]'))).get_attribute('outerHTML')
        except:
            pass
        if notice_data.notice_type !='ca':
            page_details.find_element(By.XPATH,'//*[@id="tab2"]').click()
            try:
                end_date = WebDriverWait(page_details, 30).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'Fecha Límite entrega Ofertas')]//following::td"))).text
                end_date = re.findall('\d{4}-\d+-\d+',end_date)[0]
                notice_data.end_date = datetime.strptime(end_date,'%Y-%m-%d').strftime('%Y/%m/%d')
            except:
                try:
                    end_date = WebDriverWait(page_details, 30).until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'Fecha Límite de Propuestas')]//following::td"))).text
                    end_date = re.findall('\d{4}-\d+-\d+',end_date)[0]
                    notice_data.end_date = datetime.strptime(end_date,'%Y-%m-%d').strftime('%Y/%m/%d')
                except:
                    pass
        try:
            page_details.find_element(By.LINK_TEXT,'Archivos').click()
            WebDriverWait(page_details, 30).until(EC.presence_of_element_located((By.XPATH,'//*[@id="rounded-corner"]/tbody/tr[2]/td[2]/div/a')))
            rsrs = page_details.find_elements(By.CSS_SELECTOR, 'table tr:nth-child(2) td div a')
            notice_data.resource_url.clear()
            for rsr in rsrs:
                resource = rsr.get_attribute('href')
                if 'cpe?Archivo' in resource:
                    notice_data.resource_url.append(resource)
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

# ----------------------------------------- Main Body
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    url = 'https://www.compraspublicas.gob.ec/ProcesoContratacion/compras/PC/buscarProceso.cpe?sg=1' 
    logging.info('----------------------------------')
    logging.info(url)
    fn.load_page(page_main, url)
    page_main.find_element(By.XPATH,'//*[@id="alertInicial"]/div/div[2]/button').click()
    time.sleep(30)
    page_main.find_element(By.XPATH,'/html/body/div/div[5]/div/form/table[3]/tbody/tr[2]/td[12]/table/tbody/tr/td/table/tbody/tr/td[1]/a').click()
    for page_no in range(1,30):
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divProcesos"]/table[1]/tbody/tr[2]/td[3]'))).text
        for tender_html_element in WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="divProcesos"]/table[1]/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[1:]:
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
        try:
            next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Siguiente')))
            page_main.execute_script("arguments[0].click();",next_page)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="divProcesos"]/table[1]/tbody/tr[2]/td[3]'),page_check))
            logging.info("Next Page")
        except:
            logging.info("No Next Page")
            break
    
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log('ec_compraspublicas', notice_count, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log('ec_compraspublicas', e)
        fn.session_log('ec_compraspublicas', notice_count, 'Script error')
    except:
        pass
    raise e
finally:
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("latin")
