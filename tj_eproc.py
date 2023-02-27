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
script_name = "tj_eproc"
output_xml_file = common.OutputXML.OutputXML(script_name)

def extract_and_save_notice_pp(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Tajikistan'
    notice_data.contact_country = 'Tajikistan'
    notice_data.procurement_method = "Other"
    notice_data.language = "TJ"  
    notice_data.notice_type = "pp"
 
    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(1)'))).text
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(3)'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        pass

    try: 
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            notice_data.published_date = page_details.find_element(By.XPATH,'/html/body/div[1]/div[2]/div[3]/div[1]/div[1]/div[2]/table/tbody/tr[2]/td').text
            notice_data.published_date = notice_data.published_date.split(' ')[0]
            notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
        except:
            pass
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

        try:
            buyer = WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div[3]/div[1]/div[1]/div[2]/table/tbody/tr[7]/td'))).text
            notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        except:
            pass

        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div[3]'))).get_attribute('outerHTML')
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
        
def extract_and_save_notice_spn(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    
    notice_data.performance_country = 'Tajikistan'
    notice_data.contact_country = 'Tajikistan'
    notice_data.procurement_method = "Other"
    notice_data.language = "TJ"  
    notice_data.notice_type = "spn"
    
    if url == 'https://eprocurement.gov.tj/en/subpriceoffer?namebin=&numberPlan=&fin_year=&cpv_code=&namePlan=&region_supply1=&plan_amoun_start=&plan_amoun_end=&vid=&methodz=&statuses=430&date_start=&date_end=':
        notice_data.update = True
        
    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(4) > p').text
        notice_data.published_date = notice_data.published_date.split('Call for bids start date:')[1]
        notice_data.published_date = re.findall('\d{4}-\d+-\d+',notice_data.published_date)[0]
        notice_data.published_date = datetime.strptime(notice_data.published_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        pass
    if notice_data.published_date is not None and notice_data.published_date < threshold:
        return

    try:                      
        notice_data.end_date = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-of-type(4) > p').text
        notice_data.end_date = notice_data.end_date.split('Call for bids end date:')[1]
        notice_data.end_date = re.findall('\d{4}-\d+-\d+',notice_data.end_date)[0]
        notice_data.end_date = datetime.strptime(notice_data.end_date ,'%Y-%m-%d').strftime('%Y/%m/%d')
    except:
        pass

    try:
        notice_data.reference = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(2)'))).text
    except:
        pass

    try:
        title_en = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(4) > div > a'))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title_en)
    except:
        pass
    
    try:
        buyer = WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(3)'))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
    except:
        pass    
    
    try: 
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(4) > div > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url)
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]'))).get_attribute('outerHTML')
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

#-------------------------------------------
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()
th = date.today() - timedelta(1)
threshold = th.strftime('%Y/%m/%d')
logging.info("Scraping from or greater than: " + threshold)

try:      
            
    urls = [
        'https://eprocurement.gov.tj/en/subpriceoffer?namebin=&numberPlan=&fin_year=&cpv_code=&namePlan=&region_supply1=&plan_amoun_start=&plan_amoun_end=&vid=&methodz=&statuses=430&date_start=&date_end=',
        'https://eprocurement.gov.tj/en/subpriceoffer/?namebin=&numberPlan=&fin_year=&cpv_code=&namePlan=&region_supply1=&plan_amoun_start=&plan_amoun_end=&vid=&methodz=&statuses=220&date_start=&date_end=',
        'https://eprocurement.gov.tj/en/subpriceoffer?namebin=&numberPlan=&fin_year=&cpv_code=&namePlan=&region_supply1=&plan_amoun_start=&plan_amoun_end=&vid=&methodz=&statuses=210&date_start=&date_end='
            ]
    
    try:
        for url in urls:
            fn.load_page(page_main, url)
            logging.info(url)
            for tender_html_element in page_main.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[4]/div[3]/div/table/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
                extract_and_save_notice_spn(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.published_date is not None and notice_data.published_date < threshold:
                    break
                    
        output_xml_file.copyFinalXMLToServer("cis")
        output_xml_file = common.OutputXML.OutputXML("tj_eproc")
                
    except:
        logging.info('---NO DATA---')
        pass

        
    url = 'https://eprocurement.gov.tj/en/register/plansreg?customer=&dbc=&name_plan=&number_plan=&years_plan=&trade_method=&trade_vid=&quarter=&region=&finance_point=&point_status=5&filter=Y'
    

    fn.load_page(page_main, url)
    logging.info(url)
    for page_no in range(1,25):
        page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'td:nth-of-type(1)'))).text
        for tender_html_element in page_main.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/div[2]/div[2]/div[2]/table/tbody').find_elements(By.CSS_SELECTOR,'tr')[1:]:
            extract_and_save_notice_pp(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break

        try:
            nxt_page = page_main.find_element(By.XPATH,'/html/body/div[1]/div[2]/div[3]/div/div[2]/ul/ul/li[4]/a').click()        
            logging.info("---Next Page---")
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'td:nth-of-type(1)'),page_check))
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
    output_xml_file.copyFinalXMLToServer("cis") 