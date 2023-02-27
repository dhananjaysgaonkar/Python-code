import logging
import re
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData 
from functions import ET
from selenium.webdriver.support.ui import Select
import dateparser
from hijri_converter import convert

notice_count = 0 
MAX_NOTICES = 2000
script_name = "ir_pseez"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'IRAN'
    notice_data.contact_country = 'IRAN'
    notice_data.procurement_method = "Other"
    notice_data.language = "FA"  
    notice_data.buyer_internal_id = "7673804"
    notice_data.buyer = 'PARS SPECIAL ECONOMIC ENERGY ORGANIZATION (EPA)'
    
    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(1)"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
        if('expression of interest' in notice_data.title_en.lower() or 'eoi' in notice_data.title_en.lower()):
            notice_data.notice_type = 'rei'
        else:
            notice_data.notice_type = 'spn'
        logging.info("title_en " +notice_data.title_en)
    except:
        pass
    
    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(2)"))).text
        logging.info("reference " +notice_data.reference)
    except:
        pass
    
    try:
        end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(3)"))).text.strip()
        end_date = end_date.replace('۱','1')
        end_date = end_date.replace('۲','2')
        end_date = end_date.replace('۳','3')
        end_date = end_date.replace('۴','4')
        end_date = end_date.replace('۵','5')
        end_date = end_date.replace('۶','6')
        end_date = end_date.replace('۷','7')
        end_date = end_date.replace('۸','8')
        end_date = end_date.replace('۹','9')
        end_date = end_date.replace('۰','0')

        day = end_date.split(' ')[0].strip()
        month = end_date.split(' ')[1].strip()
        year = end_date.split(' ')[2].strip()

        if 'فروردین' in month:
            if int(day)<19:
                month = 'April'
                month = '4'
            else:
                month = 'March'
                month = '3'
        if 'اردیبهشت' in month:
            if int(day)<19:
                month = 'May'
                month = '5'
            else:
                month = 'April'
                month = '4'
        if 'خردة' in month:
            if int(day)<19:
                month = 'June'
                month = '6'
            else:
                month = 'May'
                month = '5'
        if 'تیر' in month:
            if int(day)<19:
                month = 'July'
                month = '7'
            else:
                month = 'June'
                month = '6'
        if 'مرداد' in month:
            if int(day)<19:
                month = 'August'
                month = '8'
            else:
                month = 'July'
                month = '7'
        if 'شهریور' in month:
            if int(day)<19:
                month = 'September'
                month = '9'
            else:
                month = 'August'
                month = '8'
        if 'مهر' in month:
            if int(day)<19:
                month = 'October'
                month = '10'
            else:
                month = 'September'
                month = '9'
        if 'آبان' in month:
            if int(day)<19:
                month = 'November'
                month = '11'
            else:
                month = 'October'
                month = '10'
        if 'آذر' in month:
            if int(day)<19:
                month = 'December'
                month = '12'
            else:
                month = 'November'
                month = '11'
        if 'دی' in month:
            if int(day)<19:
                month = 'January'
                month = '1'
            else:
                month = 'December'
                month = '12'
        if 'بهمن' in month:
            if int(day)<19:
                month = 'February'
                month = '2'
            else:
                month = 'January'
                month = '1'
        if 'اسفند' in month:
            if int(day)<19:
                month = 'March'
                month = '3'
            else:
                month = 'February'
                month = '2'

        end_date = convert.Hijri(int(year), int(month), int(day)).to_gregorian()
        end_date = str(end_date)
        notice_data.end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        try:
            end_date = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "td:nth-of-type(3)"))).text
            GoogleTranslator(source='auto', target='en').translate(end_date)
            notice_data.end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y/%m/%d')
            logging.info("end_date " +notice_data.end_date)
        except:
            pass
        
    try: 
        notice_data.notice_url = tender_html_element.find_element(By.XPATH, 'td[1]/div[2]/a').get_attribute('href')
        logging.info("notice_url " +notice_data.notice_url)
        fn.load_page(page_details, notice_data.notice_url)
        
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_cphMiddle_pnl00cphMiddle_2169"]/div/div/div[2]'))).get_attribute('outerHTML')
        except:
            pass 
        
    except:
        notice_data.notice_url = url
        
    if notice_data.end_date is not None and notice_data.end_date < threshold:
        return
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
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
    url = 'http://www.pseez.ir/fa/tenders-%D9%85%D9%86%D8%A7%D9%82%D8%B5%D8%A7%D8%AA-%D9%88-%D9%85%D8%B2%D8%A7%DB%8C%D8%AF%D9%87-%D9%87%D8%A7'
    fn.load_page(page_main, url)
    logging.info(url)

    for tender_html_element in page_main.find_element(By.XPATH, '//*[@id="ctl00_cphMiddle_Sampa_Web_View_TenderUI_TenderList10cphMiddle_2179_dgItems"]/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
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
    output_xml_file.copyFinalXMLToServer("middle_east") 
