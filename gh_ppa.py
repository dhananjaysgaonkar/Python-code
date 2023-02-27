import logging
import time
import re
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData

MAX_NOTICES = 2000

notice_count = 0
output_xml_file = common.OutputXML.OutputXML("gh_ppa")

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    
    notice_data = NoticeData()
    notice_data.performance_country = 'Ghana'
    notice_data.contact_country = 'Ghana'
    notice_data.language = "EN"
    
    if "http://tenders.ppa.gov.gh/contracts?page=" in url:
        notice_data.notice_type = 'ca'
    elif "http://tenders.ppa.gov.gh/eois?page=" in url or "http://tenders.ppa.gov.gh/prqs?page=" in url:
        notice_data.notice_type = 'rei'
    else:
        notice_data.notice_type = 'spn'
    logging.info(notice_data.notice_type)
    
    try:
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, '.list-title').text
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, '.list-agency').text
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'div.list-title a').get_attribute('href')
        fn.load_page_expect_xpath(page_details, notice_data.notice_url, "/html/body/div/section[2]/div/div/div/div/div[2]/h3", 100)
        logging.info(notice_data.notice_url)

        if notice_data.notice_type == 'spn':
            try:
                published_date = page_details.find_element(By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[4]/dd').text.replace('nd','').replace('th','').replace('rd','').replace('st ', ' ')
                notice_data.published_date = datetime.strptime(published_date, '%d %B, %Y').strftime('%Y/%m/%d')
            except:
                pass
            
            if notice_data.published_date is not None and notice_data.published_date < threshold:
                return

            try:
                end_date = page_details.find_element(By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[5]/dd').text.replace('nd','').replace('th','').replace('rd','').replace('st ', ' ')
                notice_data.end_date = datetime.strptime(end_date, '%d %B, %Y').strftime('%Y/%m/%d')
            except:
                pass
            
            try:
                notice_data.city = page_details.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[14]/dd').text
            except:
                pass
            
            try:
                notice_data.contact_email = page_details.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[16]/dd').text
            except:
                pass
            
            try:
                notice_data.reference = page_details.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[3]/dd').text
            except:
                pass

        if notice_data.notice_type == 'rei':
            try:
                published_date = page_details.find_element(By.XPATH,'/html/body/div/section[2]/div/div/div/div/div[2]/div/dl[3]/dd').text.replace('nd','').replace('th','').replace('rd','').replace('st ', ' ')
                notice_data.published_date = datetime.strptime(published_date, '%d %B, %Y').strftime('%Y/%m/%d')
            except:
                pass
            
            if notice_data.published_date is not None and notice_data.published_date < threshold:
                return
            
            try:
                notice_data.reference = page_details.find_element(By.XPATH, '/html/body/div/section[2]/div/div/div/div/div[2]/div/dl[2]/dd').text
            except:
                pass     
            
            try:
                notice_data.resource_url = page_details.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[17]/dd/a').get_attribute('href')
            except:
                pass
                
            try:
                end_date = page_details.find_element(By.XPATH,'/html/body/div/section[2]/div/div/div/div/div[2]/div/dl[4]/dd').text.replace('nd','').replace('th','').replace('rd','').replace('st ', ' ')
                notice_data.end_date = datetime.strptime(end_date, '%d %B, %Y').strftime('%Y/%m/%d')
            except:
                pass

        if notice_data.notice_type == 'ca':
            try:
                awarding_award_date = page_details.find_element(By.XPATH,'/html/body/div/section[2]/div/div/div/div/div[2]/div/dl[9]/dd').text.replace('nd','').replace('th','').replace('rd','').replace('st ', ' ')
                notice_data.awarding_award_date = datetime.strptime(awarding_award_date, '%d %B, %Y').strftime('%Y/%m/%d')
                notice_data.published_date = notice_data.awarding_award_date
            except:
                pass
            
            if notice_data.awarding_award_date is not None and notice_data.awarding_award_date < threshold:
                return

            try:
                notice_data.award_company = page_details.find_element(By.XPATH,"//*[contains(text(),'Contract Awarded To:')]//following::dd").text
            except:
                pass
            try:
                notice_data.currency = page_details.find_element(By.XPATH,"//*[contains(text(),'Contract Currency:')]//following::dd").text
            except:
                pass
            try:
                award_price = page_details.find_element(By.XPATH,"//*[contains(text(),'Contract Award Price:')]//following::dd").text
                notice_data.awarding_final_value = re.sub("[^\d\.]", "", award_price)
            except:
                pass
            
            try:
                notice_data.reference = page_details.find_element(By.XPATH, '/html/body/div/section[2]/div/div/div/div/div[2]/div/dl[2]/dd').text
            except:
                pass                                                        
        
        try:
            tender_method = page_details.find_element(By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div/div[2]/div/dl[2]/dd').text

            if(tender_method == 'NCT'):
                notice_data.procurement_method = 'National procurement'
            elif(tender_method =='ICT'):
                notice_data.procurement_method = 'International procurement'
            else:
                notice_data.procurement_method = 'Other'
        except:
            notice_data.procurement_method = 'Other'

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div/div/div[2]/div').get_attribute('outerHTML')
        except:
            pass

    except:
        notice_data.notice_url = url

    notice_data.cleanup()

    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(), notice_data.category) 

    logging.info('-------------------------------')
    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1  

#-----------------------------------
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()

try:    
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    rundate = th.strftime("%Y-%m-%d")

    for i in range(1,3):
        urls = ['http://tenders.ppa.gov.gh/tenders?page='+str(i),
                'http://tenders.ppa.gov.gh/eois?page='+str(i),
                'http://tenders.ppa.gov.gh/prqs?page='+str(i),
                'http://tenders.ppa.gov.gh/contracts?page='+str(i)
               ]
        for url in urls:
            logging.info('----------------------------------')
            logging.info(url)
            fn.load_page_expect_xpath(page_main, url,'/html/body/div/section[2]/div/div/div/div/div[2]/div/div[1]/div[1]', 100)

            for tender_html_element in WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/section[2]/div/div/div/div/div[2]/div'))).find_elements(By.CSS_SELECTOR, 'div.list-wrap'):
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    logging.info("ok breaking")
                    break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log('gh_ppa', notice_count, 'XML uploaded')
except Exception as e:
    try:
        fn.error_log('gh_ppa', e)
        fn.session_log('gh_ppa', notice_count, 'Script error')
    except:
        pass
    raise e
finally:
    logging.info('finally')
    page_main.quit()
    page_details.quit()
    output_xml_file.copyFinalXMLToServer("africa")
