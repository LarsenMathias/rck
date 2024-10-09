import csv
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
class RCKongenCrawler:
    def __init__(self):
        options = Options()
        # ****************** Use this for server hosting ***********************
        # options.add_argument("--headless") 
        # options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # **********************************************************************
        
        self.driver = webdriver.Chrome(options=options)
        
        # self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 10)
        self.links = []
        self.nested_sub_links = []

    def load_cookies(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                cookies = json.load(file)
                self.driver.get("https://rckongen.dk/en/")
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.refresh()
                time.sleep(5)

    def crawl(self, option):
        self.load_cookies('cookies.json')
        
        if option == 1:
            self.get_all_product_links()
        elif option == 2:
            self.get_product_details_from_links()
        else:
            print("Invalid option provided.")

    def get_all_product_links(self):
        self.navigate_to_category_and_select_option()

    def get_product_details_from_links(self):
        product_links = self.read_product_links_from_csv('product_links.csv')
        processed_links = set()  # Set to keep track of processed links

        for link in product_links:
            try:
                self.extract_product_details(link)
                processed_links.add(link)  # Add processed link to the set

                # Write the remaining links back to the CSV, excluding processed links
                with open('product_links.csv', mode='w', newline='') as file:
                    fieldnames = ['Href']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    for remaining_link in product_links:
                        if remaining_link not in processed_links:
                            writer.writerow({'Href': remaining_link})

            except Exception as e:
                print(f"Error processing link {link}: {e}")
                
    def crawl_pages(self):
        try:
            pagination = self.driver.find_element(By.CSS_SELECTOR, 'div.pagination')
            next_button = pagination.find_element(By.CLASS_NAME, 'pagination__next')

            if next_button:
                print(f"Navigating to next page")
                next_button.click()
                time.sleep(4)
                return True
            else:
                print("No more pages to navigate")
                return False
                
        except NoSuchElementException:
            print("Pagination not found or no more pages to navigate")
            return False
            
        except Exception as e:
            print(f"Error navigating pages")
            return False
            
    def navigate_to_category_and_select_option(self):
        try:
            option_names = self.read_options_from_csv('category_options.csv')
            
            for option_name in option_names:
                dropdown = self.driver.find_element(By.XPATH, '//select[@id="search-product-type"]')
                select = Select(dropdown)
                
                try:
                    select.select_by_visible_text(option_name)
                    time.sleep(2) 
                    search_button = self.driver.find_element(By.XPATH, '//button[@class="search-bar__submit"]')
                    search_button.click()
                    time.sleep(5)
                    while True:
                        self.crawl_and_extract_products()
                        next=self.crawl_pages()
                        if next == False:
                            break
                        
                except NoSuchElementException as e:
                    print(f"Error selecting option '{option_name}': {e}")
            
            # Optionally save the list of option names to CSV again
            # self.save_options_to_csv(option_names, 'category_options.csv')
            
        except NoSuchElementException as e:
            print(f"Error: {e}")
    
    def crawl_and_extract_products(self):
        try:
            product_items = self.driver.find_elements(By.CSS_SELECTOR, 'div.product-item')

            data = []
            for product_item in product_items:
                product_link = product_item.find_element(By.CSS_SELECTOR, 'a.product-item__title')
                href = product_link.get_attribute('href')
                name = product_link.text.strip()

                data.append({'Href': href})

            self.save_to_csv(data, 'product_links.csv')

        except NoSuchElementException as e:
            print(f"Error: {e}")

# get product details function***************************
# *********************************************************************************************
# *******************************************************
    def extract_product_details(self, link):
        try:
            self.driver.get(link)
            
            # Extract product details
            product_title = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-meta__title'))).text.strip()
            try:
                parts = product_title.split(' - ')
                if len(parts) >= 2:
                    sku_name = parts[1].strip()
                    
                else:
                    sku_name = 'N/A'
            except:
                sku_name = 'N/A'
            product_brand = self.driver.find_element(By.CSS_SELECTOR, 'a.product-meta__vendor').text.strip()
            product_price_element = self.driver.find_element(By.CSS_SELECTOR, 'span.price')
            product_stock = self.driver.find_element(By.CSS_SELECTOR, 'div.product-form__info-item span.inventory').text.strip()
            product_price = product_price_element.text.strip().replace('\n', ' ')
            # Print or process the extracted details
            # print(f"Product Title: {product_title}")
            # print(f"SKU Name: {sku_name}")
            # print(f"Product Brand: {product_brand}")
            # print(f"Product Price: {product_price}")
            # print(f"Product Stock: {product_stock}")
            # print("")
            if product_stock == 'In stock':
                product_stock_status = 'Yes'
            else:
                product_stock_status = "No"
            data = {
                    'Product Title': product_title,
                    'Product Brand': product_brand,
                    'SKU Name': sku_name,
                    'Product Price': product_price,
                    'Product Stock': product_stock,
                    'Product Stock Status': product_stock_status,
                    'Product Link': link
                }

            # Save data to CSV file
            self.product_detail_save_to_csv(data, 'product_details.csv')
            
            
        except NoSuchElementException as e:
            print(f"Error extracting product details from {link}: {e}")
            self.save_error_to_csv(link, str(e))
            
    def save_error_to_csv(self, link, error_message):
        try:
            with open('error_log.csv', 'a', newline='', encoding='utf-8') as error_file:
                fieldnames = ['Link', 'Error Message']
                writer = csv.DictWriter(error_file, fieldnames=fieldnames)

                # Write header only if file is empty
                if error_file.tell() == 0:
                    writer.writeheader()

                # Write error details to CSV
                writer.writerow({'Link': link, 'Error Message': error_message})

            print(f"Error details saved to error_log.csv")

        except IOError as e:
            print(f"Error saving error details to error_log.csv: {e}")        
    def product_detail_save_to_csv(self, data, filename):
        try:
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Product Title', 'Product Brand', 'SKU Name', 'Product Price', 'Product Stock', 'Product Stock Status','Product Link']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header only if file is empty
                if csvfile.tell() == 0:
                    writer.writeheader()

                # Write data to CSV
                writer.writerow(data)

            print(f"Data saved to {filename}")

        except IOError as e:
            print(f"Error saving data to {filename}: {e}")        

    def save_to_csv(self, data, filename):
        try:
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Href']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if csvfile.tell() == 0:
                    writer.writeheader()
                for row in data:
                    writer.writerow(row)
            with open('product_links_backup.csv', 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Href']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if csvfile.tell() == 0:
                    writer.writeheader()
                for row in data:
                    writer.writerow(row)

            print(f"Data saved to {filename}")

        except IOError:
            print(f"Error: Could not write to {filename}")
            
    def read_options_from_csv(self, filename):
        options = []
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                for row in reader:
                    options.append(row[0].strip())
        except IOError:
            print(f"Error: Could not read from {filename}")
        
        return options

    def read_product_links_from_csv(self, filename):
        links = []
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    links.append(row['Href'].strip())
        except IOError:
            print(f"Error: Could not read from {filename}")
        
        return links

    def save_options_to_csv(self, options, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Option Name'])
                for option in options:
                    writer.writerow([option])
            print(f"Options saved to {filename}")
            
        except IOError:
            print(f"Error: Could not write to {filename}")

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    print("Select an option:")
    print("1. Get all product links")
    print("2. Get product details from links")
    option = int(input("Enter option number: "))
    
    crawler = RCKongenCrawler()
    crawler.crawl(option)
    crawler.close()
