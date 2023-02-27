import logging
import time
from datetime import date, datetime, timedelta
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC   
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import common.OutputXML
import functions as fn
from common.NoticeData import NoticeData

MAX_NOTICES = 2000
script_name = "kr_g2b"
notice_count = 0
output_xml_file = common.OutputXML.OutputXML(script_name) 

def extract_and_save_notice_1(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'spn'

    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        logging.info("reference: {} ".format(notice_data.reference))
    except:
        pass

    try:
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info("title_en: {} ".format(notice_data.title_en))
    except:
        pass

    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
        logging.info("buyer: {} ".format(notice_data.buyer))
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > div > a').get_attribute('href')
        fn.load_page(page_details, notice_data.notice_url )
        logging.info('notice_url: '+notice_data.notice_url)
    except:
        pass

    try:
        date_text = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(8)').text
        notice_data.published_date = date_text.split('(')[0].split(" ")[0]
        logging.info("Published date: " + notice_data.published_date) 
    except:
        pass
    
    try:
        end_date =date_text.split('(')[1]
        end_date =end_date[:10]
        if end_date.__contains__('-'):
            pass
        else:    
            notice_data.end_date = end_date
            logging.info("end date: " + notice_data.end_date) 
    except:
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]'))).get_attribute('outerHTML')
    except:
        pass
        
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

# _____________________________________________Method1__End__________________________________________

def extract_and_save_notice_2(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.awarding_company_country= 'South Korea'
    notice_data.awarding_currency='KRW'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'ca'

    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        logging.info("Reference: {} ".format(notice_data.reference))
    except:
        pass

    try:
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info("Title: {} ".format(notice_data.title_en))
    except:
        pass

    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
        logging.info("Buyer: {} ".format(notice_data.buyer))
    except:
        pass
    
    try:
        date_text = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.published_date = date_text.split('(')[0].split(" ")[0]
        logging.info("Published date: " + notice_data.published_date) 
    except:
        pass
    
    try:
        supplier = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
    except:
        pass
    
    if (supplier == '' or supplier == ' '):
        
        try:
            WebDriverWait(tender_html_element, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(11) a'))).click()
        except:
            pass

        try:
            award_company = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td:nth-child(5)'))).text
            notice_data.award_company = GoogleTranslator(source='auto', target='en').translate(award_company)
            logging.info("supplier: " + notice_data.award_company)
        except:
            pass
        
        try:
            notice_data.awarding_final_value = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text.replace(",", '')
            logging.info("award amount: " + notice_data.awarding_final_value)
        except:
            pass
        
        try:
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div[1]/table'))).get_attribute('outerHTML')
            notice_data.notice_url = page_main.current_url
            logging.info('notice_url: '+notice_data.notice_url)
        except:
            pass
        
        try:
            page_main.find_element(By.XPATH, '//*[@id="container"]/div[2]/div/a').click()    
        except:
            pass

    else:
        try:
            notice_data.award_company = GoogleTranslator(source='auto', target='en').translate(supplier)
            logging.info("supplier: " + notice_data.award_company)
        except:
            pass
        
        try:
            notice_data.awarding_final_value = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9)').text.replace(",", '')
            logging.info("award amount: " + notice_data.awarding_final_value)
        except:
            pass
    
        try:
            notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) > div > a').get_attribute('href')
            notice_url = notice_url.split('wbidderInfoPopup(')[1]
            bizRegNo = notice_url[1:11]                               
            tbidno = notice_url[15:26]                            
            bidseq =notice_url[30:32]   
            rebidno = notice_url[36:37]
            notice_data.notice_url = 'https://www.g2b.go.kr:8101/ep/co/selectCompInfo.do?bizRegNo='+bizRegNo+'&tbidno='+tbidno+'&bidseq='+bidseq+'&rebidno='+rebidno
            logging.info("notice_url : " + notice_data.notice_url)  
            fn.load_page(page_details, notice_data.notice_url )
            notice_data.notice_text = WebDriverWait(page_details, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="searchForm"]/div/table/tbody'))).get_attribute('outerHTML')
        except:
            pass
            
        
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------') 

# # _____________________________________________Method2__End__________________________________________
    
def extract_and_save_notice_3(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    global wait
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'spn'
    
    try:
        WebDriverWait(tender_html_element, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'tr:nth-child(2) a'))).click()
    except:
        pass
    
    try:
        notice_data.reference = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '견적요청번호')]//following::td"))).text
        logging.info("Reference: " + notice_data.reference)
    except:
        pass
   
    try:
        title = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '견적건명')]//following::td"))).text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title)
        logging.info("Title: " + notice_data.title_en)
    except:
        pass

    try:
        buyer = page_main.find_element(By.XPATH, "//*[contains(text(), '기관명')]//following::td").text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info("Buyer: " + notice_data.buyer)
    except:
        pass
    
    try:
        notice_data.published_date = page_main.find_element(By.XPATH, "//*[contains(text(), '요청일자')]//following::td").text
        notice_data.published_date = notice_data.published_date.split(' ')[0].split(" ")[0]
        logging.info("Published_date: " + notice_data.published_date)
    except:
        pass
    
    try:
        notice_data.end_date = page_main.find_element(By.XPATH, '//*[@id="container"]/div[3]/table/tbody/tr[4]/td[1]').text
        notice_data.end_date = notice_data.end_date.split(' ')[0]
        logging.info("End date: " + notice_data.end_date)
    except:
        try:
            notice_data.end_date = page_main.find_element(By.XPATH, "//*[contains(text(), '견적마감일')]//following::td").text
            notice_data.end_date = notice_data.end_date.split(' ')[0]
            logging.info("End date: " + notice_data.end_date)
        except:
            pass
           
    try:
        notice_data.notice_url = 'https://www.g2b.go.kr:8402/gtob/all/pr/estimate/reqEstimateOpenG2BDtl.do?estmtReqNo='+notice_data.reference+'&userGubun=Y'
        logging.info("notice_url : " + notice_data.notice_url)    
    except:
        pass

    try:
        notice_data.notice_text = page_main.find_element(By.ID, 'content_wrap').get_attribute('outerHTML')
    except:
        pass

    try:
        page_main.execute_script("window.history.go(-1)")
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  
# # _____________________________________________Method3__End__________________________________________

def extract_and_save_notice_4(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'rei'

    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.reference = GoogleTranslator(source='auto', target='en').translate(notice_data.reference)
        logging.info("reference: {} ".format(notice_data.reference))
    except:
        pass

    try:
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info("title_en: {} ".format(notice_data.title_en))
    except:
        pass
    
    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
        logging.info("buyer: {} ".format(notice_data.buyer))
    except:
        pass
    
    try:
        date_text = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        notice_data.published_date =  date_text.split(' ')[0]
        logging.info("Published date: " + notice_data.published_date)
    except:
        pass
    
    try:
        tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').click()
    except:
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]'))).get_attribute('outerHTML')  
    except:
        pass
    
    try:
        notice_data.notice_url = page_main.current_url
        logging.info('notice_url: '+notice_data.notice_url)
    except:
        pass
    
    try:   
        page_main.execute_script("window.history.go(-1)") 
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  


# # _____________________________________________Method4__End__________________________________________

def extract_and_save_notice_5(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'spn'
    
    try:
        notice_data.reference = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        logging.info("Reference: " + notice_data.reference)
    except:
        pass
     
    try:
        notice_data.published_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.published_date = notice_data.published_date.split(" ")[0]
        logging.info("Published_date: " + notice_data.published_date)
    except:
        pass
    
    try:
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info("Title: " + notice_data.title_en)
    except:
        pass

    try:
        notice_data.buyer = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(notice_data.buyer)
        logging.info("Buyer: " + notice_data.buyer)
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  

# # _____________________________________________Method5__End__________________________________________

def extract_and_save_notice_6(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    global wait
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'pp'
    
    try:
        est_cost = tender_html_element.find_element(By.CSS_SELECTOR, 'tr:nth-child(2)  td.tr').text
        notice_data.est_cost = est_cost.replace(",","") 
        try:
            notice_data.est_cost = notice_data.est_cost.replace("￦","")
        except:
            pass
        logging.info( "est_cost "+notice_data.est_cost)
    except:
        pass
  
    try:                
        notice_data.title_en = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(notice_data.title_en)
        logging.info('title_en '+notice_data.title_en)
    except:
        pass
    
    try:
        details = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').click()
    except:
        pass
    
    try:
        buyer = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'발주기관')]//following::td"))).text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info("buyer_en "+notice_data.buyer)  
    except:
        pass
    
    try:
        notice_data.published_date = page_main.find_element(By.XPATH, "//*[contains(text(), '공개일시')]//following::td").text
        notice_data.published_date = notice_data.published_date.split(" ")[0]
        logging.info("published_date "+notice_data.published_date)
    except:
        pass
    
    try:
        notice_data.notice_url = page_main.current_url
        logging.info('notice_url: '+notice_data.notice_url)
    except:
        pass
    
    try:
        notice_data.notice_text = page_main.find_element(By.ID, 'content_wrap').get_attribute('outerHTML')
    except:
        pass
    
    try:
        page_main.execute_script("window.history.go(-1)")
    except:
        pass
    
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------') 

# # _____________________________________________Method6__End__________________________________________

def extract_and_save_notice_7(tender_html_element):
    global script_name
    global notice_count
    global notice_data
    global wait
    notice_data = NoticeData()
    notice_data.performance_country = 'South Korea'
    notice_data.contact_country = 'South Korea'
    notice_data.procurement_method = "Other"
    notice_data.language = "KR"
    notice_data.notice_type = 'pp'
    
    try:    
        WebDriverWait(tender_html_element, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a'))).click()
    except:
        return
    
    try:
        notice_data.reference = WebDriverWait(page_main, 20).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '계약참조번호')]//following::td"))).text     
        logging.info("reference: "+notice_data.reference)
    except:
        pass

    try:
        notice_data.published_date = page_main.find_element(By.XPATH, "//*[contains(text(), '계약체결일자')]//following::td").text
        logging.info("published_date: "+notice_data.published_date)
    except:
        try:
            notice_data.published_date = page_main.find_element(By.XPATH, "//*[contains(text(), '계약일자')]//following::td").text
            logging.info("published_date: "+notice_data.published_date)
        except:
            pass            
    
    try:
        title = page_main.find_element(By.XPATH, '//*[@id="st_form"]/div[1]/table/tbody/tr[2]/td').text
        notice_data.title_en = GoogleTranslator(source='auto', target='en').translate(title)
        logging.info("title_en: "+notice_data.title_en)
    except:
        pass

    try:
        buyer = page_main.find_element(By.XPATH, '//*[@id="st_form"]/div[3]/table/tbody/tr/td[4]').text
        notice_data.buyer = GoogleTranslator(source='auto', target='en').translate(buyer)
        logging.info("buyer: "+notice_data.buyer)
    except:
        pass
    
    try:
        notice_data.est_cost = page_main.find_element(By.XPATH, "//*[contains(text(),'금차계약금액')]//following::td").text
        notice_data.est_cost = notice_data.est_cost.split("(")[0]
        logging.info("est_cost:  "+notice_data.est_cost)
    except:
        pass  
    
    try:
        notice_data.notice_url = url
        logging.info('notice_url: '+notice_data.notice_url)
    except:
        pass

    try:
        notice_data.notice_text = page_main.find_element(By.ID, 'content_wrap').get_attribute('outerHTML')
    except:
        pass
        
    notice_data.cleanup()
    
    if notice_data.cpvs == [] and notice_data.title_en is not None:
        notice_data.cpvs = fn.assign_cpvs_from_title(notice_data.title_en.lower(),notice_data.category) 
        logging.info(notice_data.cpvs)
        
    try:
        page_main.execute_script("window.history.go(-1)")
        WebDriverWait(tender_html_element, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td.tl > a')))
    except:
        pass

    if notice_data.published_date is not None and notice_data.published_date < threshold:
            return

    output_xml_file.writeNoticeToXMLFile(notice_data)
    notice_count += 1
    logging.info('----------------------------------')  
# # _____________________________________________Method7__End__________________________________________

# ............................................MAIN BLOCK.....................................................
page_main = fn.init_chrome_driver()
page_details = fn.init_chrome_driver()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    url_dt = str(th).replace ("-","%2F")
    th2 = date.today()
    url_dt2 = str(th2).replace ("-","%2F")

#     METHOD 1
    print('METHOD 1')
    for page_number in range(1,50):
        url = 'https://www.g2b.go.kr:8101/ep/tbid/tbidList.do?area=&areaNm=&bidNm=&bidSearchType=1&budgetCompare=&detailPrdnm=&detailPrdnmNo=&downBudget=&fromBidDt='+str(url_dt)+'&fromOpenBidDt=&industry=&industryCd=&instNm=&instSearchRangeType=&intbidYn=&orgArea=&procmntReqNo=&radOrgan=1&recordCountPerPage=100&refNo=&regYn=Y&searchDtType=1&searchType=1&strArea=&taskClCds=&toBidDt='+str(url_dt2)+'&toOpenBidDt=&upBudget=&currentPageNo='+ str(page_number)
        fn.load_page(page_main, url)
        logging.info(url)
        for tender_html_element in WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="resultForm"]/div[2]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr'):
            extract_and_save_notice_1(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break

                
#     METHOD 2
    print('METHOD 2')
    for page_number in range(1,50):
        url = 'https://www.g2b.go.kr:8101/ep/tbid/integrationWbidderList.do?searchType=1&bidSearchType=3&taskClCds=&bidNm=&searchDtType=2&fromBidDt=&toBidDt=&fromOpenBidDt='+str(url_dt)+'&toOpenBidDt='+str(url_dt2)+'&radOrgan=1&instNm=&instSearchRangeType=&refNo=&area=&areaNm=&strArea=&orgArea=&industry=&industryCd=&upBudget=&downBudget=&budgetCompare=&detailPrdnmNo=&detailPrdnm=&procmntReqNo=&intbidYn=&regYn=Y&recordCountPerPage=100&currentPageNo=' + str(page_number)
        fn.load_page(page_main, url)
        logging.info(url)
        rows = page_main.find_element(By.XPATH, '//*[@id="container"]/div/table/tbody').find_elements(By.CSS_SELECTOR, 'tr')
        length = len(rows)
        for k in range(0,(length-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[k]
            extract_and_save_notice_2(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break


#     METHOD 3
    print('METHOD 3')
    url = 'https://www.g2b.go.kr:8402/gtob/all/pr/estimate/fwdReqEstimateOpenCond.do'
    fn.load_page(page_main, url)
    logging.info(url)
    per_page = Select(page_main.find_element(By.ID, 'recordCountPerPage'))
    per_page.select_by_visible_text('100')
    WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="content"]/table/tbody/tr[5]/td[2]/div[2]/span[1]/a'))).click()  # search button
    rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="content_wrap"]/div[4]/table'))).find_elements(By.CSS_SELECTOR, 'tbody')
    length_rows = len(rows)
    for k in range(0, (length_rows - 1)):
        tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="content_wrap"]/div[4]/table'))).find_elements(By.CSS_SELECTOR, 'tbody')[k]
        extract_and_save_notice_3(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break


#     METHOD 4
    print('METHOD 4')
    for page_number in range(1,50):
        url = 'https://www.g2b.go.kr:8081/ep/preparation/prestd/preStdPublishList.do?dminstCd=&fromRcptDt='+str(url_dt)+'&instCl=&instNm=&instSearchRange=&listPageCount=&myProdSearchYn=&orderbyItem=1&preStdRegNo=&prodNm=&pubYn=Y&recordCountPerPage=100&referNo=&searchDetailPrdnm=&searchDetailPrdnmNo=&srchCl=&srchNo=&swbizTgYn=&taskClCd=&toRcptDt='+str(url_dt2)+'&currentPageNo='+ str(page_number)
        fn.load_page(page_main, url)
        logging.info(url)
        rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')
        length_rows = len(rows)
        for k in range(0,(length_rows-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[k]
            extract_and_save_notice_4(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break


#     METHOD 5 
    print('METHOD 5')
    url = 'https://www.g2b.go.kr:8101/ep/invitation/delay/listPagePstpBid.do'
    fn.load_page(page_main, url)
    logging.info(url)
    per_page = Select(page_main.find_element(By.ID, 'recordCountPerPage'))
    per_page.select_by_visible_text('100')
    WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bt_search"]'))).click()  # search button
    rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="frmList"]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')
    length_rows = len(rows)
    for page_number in range(1,50):
        for k in range(0, (length_rows-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="frmList"]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[k]
            extract_and_save_notice_5(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
        
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break


#     METHOD 6
    print('METHOD 6')
    url = 'https://www.g2b.go.kr:8101/ep/preparation/orderplan/orderplanPubList.do'
    fn.load_page(page_main, url)
    
    for page_number in range(1,50):
        url = page_main.current_url + '?currentPageNo=' + str(page_number) 
        fn.load_page(page_main, url)
        logging.info(url)
        per_page = Select(page_main.find_element(By.ID, 'recordCountPerPage'))
        per_page.select_by_visible_text('100')
        postdate = page_main.find_element(By.ID, 'fromReleaseDt').clear()
        WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.ID, 'fromReleaseDt'))).send_keys(threshold)
        WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.ID, 'bt_search'))).click()  # search button
        rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div[1]/table'))).find_elements(By.CSS_SELECTOR, 'tbody')
        length_rows = len(rows)
        
        for k in range(0, (length_rows-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="container"]/div[1]/table'))).find_elements(By.CSS_SELECTOR, 'tbody')[k]
            extract_and_save_notice_6(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break
                
        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break


#     METHOD 7
    print('METHOD 7')
    for page_number in range(1,50):
        url = 'https://www.g2b.go.kr:8067/contract/contList.jsp?go_page=&contType=0&from_date='+str(url_dt) +'&giguan_chk_code=1&yocungnumber=&upche_name=&temp=&userid=zGUEST0000000&upmu_code=10&showTotalRecordCountYn=N&bu_name=TcontSearchCall&giguan_name=&geyak_way=&upmu_gubun=%B9%B0%C7%B0&to_date='+str(url_dt2) +'&contOrgCode=&upche_kind=&balzu_code=&geyak_konggonumber=&instSearchRangeCd=N&v_pagesize=100&currMonthRadioVal=&searchType=1&geyak_number=&whakjung_bnumber=&pummung_name=&orderbychk=B&giguan_code=1&page_no='+ str(page_number)
        fn.load_page(page_main, url)
        logging.info(url)
        WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#st_form > div.button_wrap > div > a'))).click()
        per_page = Select(page_main.find_element(By.ID, 'v_pagesize'))
        per_page.select_by_visible_text('100')
        WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="TcontSearch_form"]/div[3]/div/a[1]'))).click()  # search button
        rows = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="st_form"]/div[2]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[0::2]
        length_rows = len(rows)
        for k in range(0,(length_rows-1)):
            tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="st_form"]/div[2]/table/tbody'))).find_elements(By.CSS_SELECTOR, 'tr')[0::2][k]
            extract_and_save_notice_7(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

        if notice_data.published_date is not None and notice_data.published_date < threshold:
            break
 
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    fn.session_log('kr_g2b', notice_count, 0, 'XML uploaded')
    
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
