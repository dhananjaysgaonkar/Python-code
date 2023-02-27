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
output_xml_file = common.OutputXML.OutputXML("de_vmp_rheinland")


def extract_and_save_notice(tender_html_element):
    global ml_cpv
    global notice_count
    global notice_data
    
    wait = WebDriverWait(page_details, 10) 
    notice_data = NoticeData()

    notice_data.performance_country = 'Germany'
    notice_data.contact_country = 'Germany'
    notice_data.procurement_method = "Other"
    notice_data.language = "DE"
    
    p_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    if('Vergebener Auftrag' in p_type):
        notice_data.notice_type = "ca"
    elif("Beabsichtigte Ausschreibung" in p_type):
        notice_data.notice_type = "pp"
    else:
        notice_data.notice_type = "spn"
    logging.info(notice_data.notice_type)
    
    try:
        title_en = tender_html_element.find_element(By.CSS_SELECTOR, "td.word-break").text
    except:
        title_en = 'Please refer to notice details'
    try:
        notice_data.title_en = GoogleTranslator(source='de', target='en').translate(title_en)
    except:
        notice_data.title_en = title_en
    logging.info(notice_data.title_en)
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except:
        pass
    logging.info(notice_data.buyer)
    
    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(1)').text
        notice_data.published_date = datetime.strptime(notice_data.published_date,'%d.%m.%Y').strftime('%Y/%m/%d')
    except:
        notice_data.published_date = threshold
    logging.info(notice_data.published_date)
    
    if notice_data.published_date < threshold:
        return
     
    if notice_data.notice_type == "spn" or notice_data.notice_type == "pp":
        try:
            notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(2)').text
            notice_data.end_date  = datetime.strptime(notice_data.end_date ,'%d.%m.%Y').strftime('%Y/%m/%d')
        except:
            if notice_data.notice_type == "spn":
                end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(15)
                notice_data.end_date = end_date.strftime('%Y/%m/%d')
            elif notice_data.notice_type == "pp":
                end_date = datetime.strptime(notice_data.published_date,'%Y/%m/%d') + timedelta(365)
                notice_data.end_date = end_date.strftime('%Y/%m/%d')
            else:
                pass
        logging.info(notice_data.end_date) 
        
    try:
        page_details_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) a').get_attribute('href')
        id= page_details_url.split('id=')[1]
        id= id.split('%',1)[0]
        notice_data.notice_url = 'https://vmp-rheinland.de/VMPSatellite/public/company/projectForwarding.do?pid='+id
        logging.info(notice_data.notice_url)
        fn.load_page(page_details, notice_data.notice_url, "content", 10)
    except:
        notice_data.notice_url = "https://vmp-rheinland.de/VMPSatellite/common/project/search.do?method=searchExtended"
    
    try:
        notice_data.reference =  page_details.find_element(By.XPATH,"//*[contains(text(),'Ausschreibungs-ID')]//following::div").text
        logging.info(notice_data.reference)
    except:
        notice_data.reference = ''
        
    try:
        cpv = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'p.margin-bottom-10 b'))).text.split('-')[0]
        notice_data.cpvs.clear()
        notice_data.cpvs.append(cpv)
        logging.info(notice_data.cpvs)
        if (cpv == ''):
            cpvs = classifier.get_cpvs(notice_data.title_en.lower(), notice_data.category)
            notice_data.cpvs.clear()
            cpv_count = 0
            if cpvs:
                for cpv in cpvs:
                    if cpv not in false_cpv:
                        notice_data.cpvs.append(cpv)
                        cpv_count += 1
            if (cpv_count != 0):
                ml_cpv += 1
    except:
        cpvs = classifier.get_cpvs(notice_data.title_en.lower(), notice_data.category)
        cpv_count = 0
        notice_data.cpvs.clear()
        if cpvs:
            for cpv in cpvs:
                if cpv not in false_cpv:
                    notice_data.cpvs.append(cpv)
                    cpv_count += 1
        if cpv_count != 0:
            ml_cpv += 1
            
    try:
        notice_data.resource_url = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[4]/div/div[5]/div/table/tbody/tr/td[5]/a'))).get_attribute('href')
    except:
        try:
            resource_url = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/ul/li[4]/a'))).click()
            notice_data.resource_url = wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[4]/div/span[2]/div/div/a'))).get_attribute('href')
        except:  
            pass
    logging.info(notice_data.resource_url)
    
    try:
        info =  wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/ul/li[3]/a'))).click()            
    except:
        try:
            info =  wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/ul/li[2]/a'))).click()
        except:
            pass
        
    try:
        notice_data.address =wait.until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div[4]/div/span[1]/div/div[1]/fieldset'))).text
    except:
        pass

    try:
        notice_data.contact_phone = wait.until(EC.presence_of_element_located((By.XPATH,"//*[contains(text(),'Telefon')]//following::div"))).text
    except:
        pass

    try:
        notice_data.contact_email = page_details.find_element(By.XPATH,"//*[contains(text(),'E-Mail')]//following::div").text
    except:
        pass

    if notice_data.notice_type == 'ca':
        try:
            award_company =  page_details.find_element(By.XPATH,"//*[contains(text(),'Los-Nr.')]//following::div/div").text
            notice_data.award_company = award_company.split("Bezeichnung")[1]
            logging.info(notice_data.award_company)
        except:
            try:
                award_company =  page_details.find_element(By.XPATH,"//*[contains(text(),'Wirtschaftsteilnehmer')]//following::div/div/div").text
                award_company = award_company.split("Bezeichnung")[1]
                notice_data.award_company = award_company.split("Postleitzahl")[0]
                logging.info(notice_data.award_company)
            except:
                 notice_data.award_company = "Please refer notice details"
    
    try:
        notice_data.notice_text += wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[4]'))).get_attribute('outerHTML')
    except:
        notice_data.notice_text += '</br>'
        notice_data.notice_text = 'Title:'
        notice_data.notice_text += notice_data.title_en
        notice_data.notice_text += '</br>'
        notice_data.notice_text += 'publish_date : '
        notice_data.notice_text += notice_data.published_date
        notice_data.notice_text += 'Buyer'
        notice_data.notice_text += notice_data.buyer
        notice_data.notice_text += '</br>'
        if notice_data.notice_type != 'ca':
            notice_data.notice_text += ' End_date :'
            notice_data.notice_text += notice_data.end_date
            notice_data.notice_text += '</br>'
        if notice_data.address != '':
            notice_data.notice_text += 'Address'
            notice_data.notice_text += notice_data.address
            notice_data.notice_text += '</br>'
        if notice_data.contact_phone != '':
            notice_data.notice_text += 'phone'
            notice_data.notice_text += notice_data.contact_phone
            notice_data.notice_text += '</br>'
        if notice_data.contact_email != '':
            notice_data.notice_text += 'email'        
            notice_data.notice_text +=notice_data.contact_email
            notice_data.notice_text += '</br></br>'
            
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')
    
#-------------------------------------------
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    url = 'https://vmp-rheinland.de/VMPSatellite/common/project/search.do?method=searchExtended'
    logging.info('----------------------------------')
    logging.info(url)
    fn.load_page(page_main, url,"masterForm",10)
    
    for i in range(1,50):
        for tender_html_element in WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH,'//*[@id="masterForm"]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr'):
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date < threshold:
            break
            
        try:
            nxt_page = page_main.find_element(By.CSS_SELECTOR,'a.browseForward.waitClick')
            page_main.execute_script("arguments[0].click();",nxt_page)
            time.sleep(5)
        except:
            break
        
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log('de_vmp_rheinland', notice_count, 0, ml_cpv, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log('de_vmp_rheinland', e)
        fn.session_log('de_vmp_rheinland', notice_count, 0, ml_cpv, 'Script error')
    except:
        pass
    raise e
finally:
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("europe")