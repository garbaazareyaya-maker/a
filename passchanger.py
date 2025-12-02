import sys
import time
import random
import re
import threading
import hashlib
import os
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from PyQt6 import QtCore, QtGui, QtWidgets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

class CPUIntensiveProcessor:
    """CPU intensive operations to maximize CPU usage and minimize GPU usage"""

    @staticmethod
    def hash_operations(data, iterations=10000):
        """Perform CPU-intensive hashing operations"""
        result = data
        for _ in range(iterations):
            result = hashlib.sha256(result.encode()).hexdigest()
        return result

    @staticmethod
    def text_processing(text, iterations=1000):
        """CPU-intensive text processing operations"""
        processed = text
        for i in range(iterations):
            # Complex string operations
            processed = ''.join(reversed(processed))
            processed = processed.upper() if i % 2 == 0 else processed.lower()
            processed = processed.replace('a', '1').replace('1', 'a')
            processed = processed[:len(processed)//2] + processed[len(processed)//2:]
        return processed

    @staticmethod
    def mathematical_operations(base_num=12345, iterations=50000):
        """CPU-intensive mathematical calculations"""
        result = base_num
        for i in range(iterations):
            result = (result * 7) % 1000000
            result = result ** 2 % 999999
            result = int(result ** 0.5)
        return result


class ScraperWorker(QtCore.QObject):
    log_signal = QtCore.pyqtSignal(str)
    initial_setup_completed_signal = QtCore.pyqtSignal(str)
    full_process_completed_signal = QtCore.pyqtSignal(str)
    intermediate_result_signal = QtCore.pyqtSignal(str)
    progress_update_signal = QtCore.pyqtSignal(int, str)

    # New signal for retry mechanism
    ask_retry_signal = QtCore.pyqtSignal()
    # Signal to receive decision from MainWindow
    retry_decision_signal = QtCore.pyqtSignal(bool)

    def __init__(self, account_password):
        super().__init__()
        self.account_password = account_password
        self.first_name = "Not Available"
        self.last_name = "Not Available"
        self.dob = "Not Available"
        self.country = "Not Available"
        self.postal = ""
        self.alt_email = "Recovery_Not_Attempted"
        self.cpu_processor = CPUIntensiveProcessor()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.driver = None
        self.temp_profile_dir = None

        # New: Store collected emails and subjects
        self.collected_emails = []
        self.collected_subjects = []
        
        # Flag for retry decision
        self._retry_response = None
        self.retry_decision_signal.connect(self._set_retry_response)

        # Predefined random subjects and messages for new emails
        self.random_subjects = [
            "Quick Question",
            "Checking In",
            "Regarding Your Account",
            "Important Update",
            "Hello from Bot"
        ]
        self.random_messages = [
            "Hope you are having a great day!",
            "Just wanted to touch base regarding something.",
            "Please disregard if this is not relevant.",
            "This is an automated message.",
            "Wishing you all the best."
        ]

    def _set_retry_response(self, response: bool):
        self._retry_response = response

    def close_browser(self):
        """Closes the browser and cleans up the temporary profile directory."""
        self.log_signal.emit("Closing browser...")
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.log_signal.emit(f"Error quitting driver: {e}")
            self.driver = None
        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            try:
                shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
                self.log_signal.emit("Temporary profile directory cleaned.")
            except Exception as cleanup_error:
                self.log_signal.emit(f"Cleanup warning: {cleanup_error}")
        self.executor.shutdown(wait=True)

    def cpu_intensive_delay(self, min_s=1.0, max_s=2.0):
        """Human-like delay with CPU-intensive background processing"""
        delay_time = random.uniform(min_s, max_s)
        futures = []
        for _ in range(3):
            future = self.executor.submit(self.cpu_processor.mathematical_operations)
            futures.append(future)
        time.sleep(delay_time)
        for future in futures:
            try:
                future.result(timeout=0.1)
            except:
                pass
    
    def _human_like_type(self, element, text, min_char_delay=0.05, max_char_delay=0.15):
        """Types text into an element character by character with human-like delays."""
        # Use ActionChains for reliable character by character typing to the active element
        actions = ActionChains(self.driver)
        for char in text:
            actions.send_keys(char).perform()
            time.sleep(random.uniform(min_char_delay, max_char_delay))
        self.cpu_intensive_delay(0.5, 1.0) # Add a slight pause after typing

    def _initialize_driver(self):
        """Initializes the Selenium WebDriver with stealth options."""
        self.progress_update_signal.emit(5, "Initializing browser...")
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        ]
        random_user_agent = random.choice(user_agents)

        self.temp_profile_dir = tempfile.mkdtemp()
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={random_user_agent}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir={self.temp_profile_dir}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument("--disable-notifications")

        width = random.randint(1024, 1440)
        height = random.randint(700, 900)
        options.add_argument(f"--window-size={width},{height}")

        self.driver = webdriver.Chrome(options=options)
        driver = self.driver
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
           "source": """
              Object.defineProperty(navigator, 'webdriver', {
                 get: () => undefined
              });
              window.chrome = {
                  runtime: {}
              };
              Object.defineProperty(navigator, 'plugins', {
                 get: () => [1, 2, 3, 4, 5],
              });
              Object.defineProperty(navigator, 'languages', {
                 get: () => ['en-US', 'en'],
              });
           """
        })
        stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
                webgl_vendor="Intel Corporation", renderer="Intel UHD Graphics", fix_hairline=True)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.log_signal.emit("WebDriver initialized.")
        self.progress_update_signal.emit(10, "Browser initialized.")

    def _perform_login_check(self):
        """Handles the manual login and waits for confirmation."""
        self.progress_update_signal.emit(15, "Waiting for manual login...")
        self.driver.get("https://login.live.com/")
        self.log_signal.emit("Opened Microsoft login page. Please log in manually...")

        start_time = time.time()
        login_detected = False
        while time.time() - start_time < 240:
            if "login.live.com" not in self.driver.current_url and "account.microsoft.com" in self.driver.current_url:
                login_detected = True
                break
            time.sleep(random.uniform(0.5, 1.5))

        if login_detected:
            self.log_signal.emit("Login detected!")
            self.progress_update_signal.emit(20, "Login successful.")
        else:
            self.log_signal.emit("Login not confirmed (timeout) – proceeding anyway.")
            self.progress_update_signal.emit(20, "Login timed out, proceeding...")

        self.cpu_intensive_delay(random.uniform(2, 4), random.uniform(4, 6))

    def _extract_profile_info(self):
        """Navigates to profile page and extracts user information."""
        self.progress_update_signal.emit(25, "Extracting profile information...")
        self.log_signal.emit("Navigating to profile page...")
        self.driver.get("https://account.microsoft.com/profile?")
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(random.uniform(4, 7))

        full_name = "Not Available"
        dob_local = "Not Available"
        country_local = "Not Available"
        email_addr = "Not Available"

        try:
            full_name = self.driver.find_element(
                By.XPATH, "//span[@id='profile.profile-page.personal-section.full-name']"
            ).text.strip()
        except Exception:
            self.log_signal.emit("Failed to extract Full Name.")

        try:
            dob_local = self.driver.find_element(
                By.XPATH, "//div[contains(@id, 'date-of-birth')]//span[contains(text(),'/')]"
            ).text.strip()
        except Exception:
            self.log_signal.emit("Failed to extract Date of Birth.")

        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            m = re.search(r"Country or region\s*\n\s*([A-Za-z\s]+)", body_text, re.MULTILINE)
            if m:
                country_local = m.group(1).splitlines()[0].strip()
            else:
                raise Exception("Not found")
        except Exception:
            self.log_signal.emit("Failed to extract Country.")

        try:
            email_elem = self.driver.find_element(By.XPATH, "//a[starts-with(@href, 'mailto:')]")
            email_addr = email_elem.text.strip()
            if not email_addr:
                email_addr = email_elem.get_attribute("href").replace("mailto:", "").strip()
            self.email_addr = email_addr
        except Exception:
            pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
            email_matches = re.findall(pattern, self.driver.page_source)
            if email_matches:
                email_addr = email_matches[0]
                self.email_addr = email_addr
            else:
                self.log_signal.emit("Failed to extract Email.")
                email_addr = "Not Available"
                self.email_addr = email_addr

        self.log_signal.emit("Profile info extracted:")
        self.log_signal.emit("  • Full Name: " + full_name)
        self.log_signal.emit("  • DOB: " + dob_local)
        self.log_signal.emit("  • Country: " + country_local)
        self.log_signal.emit("  • Email: " + email_addr)

        self.dob = dob_local
        self.country = country_local

        if full_name != "Not Available":
            name_parts = full_name.split()
            if len(name_parts) > 1:
                self.first_name = " ".join(name_parts[:-1])
                self.last_name = name_parts[-1]
            else:
                self.first_name = full_name
                self.last_name = ""
        else:
            self.first_name = "Not Available"
            self.last_name = "Not Available"
        self.log_signal.emit(f"Assigned for identity form: First Name={self.first_name}, Last Name={self.last_name}, DOB={self.dob}, Country={self.country}")
        self.progress_update_signal.emit(30, "Profile information extracted.")

    def _extract_postal_code(self):
        """Navigates to address book and extracts postal code."""
        self.progress_update_signal.emit(35, "Extracting postal code...")
        self.driver.get("https://account.microsoft.com/billing/addresses")
        self.log_signal.emit("Navigating to Address Book Section (for postal code extraction)...")
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        self.cpu_intensive_delay(random.uniform(5, 7), random.uniform(7, 9))

        postal_codes_str = "Not Found"
        try:
            address_blocks = WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(By.XPATH, "//div[contains(@class, 'ms-StackItem')]")
            )
            extracted_addresses = []
            unwanted_keywords = ["change", "manage", "default", "choose", "all addresses", "add new", "remove", "set as", "preferred", "billing info", "shipping info", "email", "address book"]
            for block in address_blocks:
                text = block.text.strip()
                if text and not any(keyword in text.lower() for keyword in unwanted_keywords) and re.search(r'\d+', text):
                    extracted_addresses.append(text)

            seen = set()
            unique_addresses = [addr for addr in extracted_addresses if addr.lower() not in seen and not seen.add(addr.lower())]

            postal_codes_set = set()
            for addr in unique_addresses:
                codes = re.findall(r'\b\d{4,6}\b', addr)
                if codes:
                    postal_codes_set.add(codes[-1])
            postal_codes_list = list(postal_codes_set)

            self.postal = postal_codes_list[0] if postal_codes_list else ""
            self.log_signal.emit(f"Assigned for identity form: Postal={self.postal}")

            postal_codes_str = ", ".join(postal_codes_list) if postal_codes_list else "Not Found"

        except Exception as e:
            self.log_signal.emit(f"Failed to extract postal code from addresses: {str(e)}")
            self.postal = ""
            postal_codes_str = "Not Found"
        self.progress_update_signal.emit(40, "Postal code extraction complete.")
        return postal_codes_str

    def _process_outlook_sent_items(self):
        """
        Navigates to Outlook, bypasses extraction, and directly composes and sends a new email.
        The details of this sent email (recipients, subject) are collected for the recovery form.
        """
        self.progress_update_signal.emit(42, "Processing Outlook Sent Items...")
        self.log_signal.emit("Navigating to Outlook Sent Items...")
        self.driver.get("https://outlook.live.com/mail/0/sentitems")
        time.sleep(random.uniform(5, 8)) # Give time for page to load

        self.log_signal.emit("Bypassing extraction. Proceeding directly to compose a new email...")
        
        # Initialize collections
        self.collected_emails = [] 
        self.collected_subjects = []

        # Use 'N' key to open new mail box
        try:
            self.log_signal.emit("Pressing 'N' to open new mail composer...")
            ActionChains(self.driver).send_keys("n").perform()
            # Wait for the Send button icon to appear
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Send"]')))
            self.log_signal.emit("New mail composer opened and Send button icon located.")
            time.sleep(1) # Fixed 1 second wait as requested after locating the send mail button
        except Exception as e:
            self.log_signal.emit(f"Failed to open new mail composer with 'N' key or locate Send icon: {e}")
            # Fallback: try to find the "New message" button directly
            try:
                new_message_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='New message'] | //button[contains(@aria-label, 'New mail')]"))
                )
                new_message_button.click()
                # Wait for the Send button icon after fallback button click
                WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Send"]')))
                self.log_signal.emit("New mail composer opened via button click and Send button icon located.")
                time.sleep(1) # Fixed 1 second wait after locating the send mail button
            except Exception as e_fallback:
                self.log_signal.emit(f"Failed to open new mail composer even with fallback: {e_fallback}")
                raise # Cannot proceed if composer fails to open

        # Defined target emails for this single send operation
        target_emails_for_one_send = ["abc@hotmail.com", "abc@outlook.com", "abc@gmail.com"]
        
        try:
            # Assume the caret is already at the 'To' field
            actions = ActionChains(self.driver)

            # Type recipients and add them to self.collected_emails
            self._human_like_type(self.driver.switch_to.active_element, target_emails_for_one_send[0])
            self.log_signal.emit(f"Entered recipient 1: {target_emails_for_one_send[0]}")
            time.sleep(1)

            actions.send_keys(Keys.SPACE).perform()
            self._human_like_type(self.driver.switch_to.active_element, target_emails_for_one_send[1])
            self.log_signal.emit(f"Entered recipient 2: {target_emails_for_one_send[1]}")
            time.sleep(1)

            actions.send_keys(Keys.SPACE).perform()
            self._human_like_type(self.driver.switch_to.active_element, target_emails_for_one_send[2])
            self.log_signal.emit(f"Entered recipient 3: {target_emails_for_one_send[2]}")
            time.sleep(1)
            
            # Set the collected emails directly
            self.collected_emails = target_emails_for_one_send
                    
            self.cpu_intensive_delay(1.0, 1.5)

            # Press TAB twice to move to subject
            self.log_signal.emit("Pressing TAB twice to move to subject...")
            actions.send_keys(Keys.TAB).perform()
            time.sleep(1)
            actions.send_keys(Keys.TAB).perform()
            time.sleep(1)

            # Enter random subject and add it to self.collected_subjects
            subject_text = random.choice(self.random_subjects)
            self._human_like_type(self.driver.switch_to.active_element, subject_text)
            self.collected_subjects.append(subject_text)
            self.log_signal.emit(f"Entered subject: '{subject_text}'")
            time.sleep(1)

            # Press TAB once to move to message field
            self.log_signal.emit("Pressing TAB once to move to message body...")
            actions.send_keys(Keys.TAB).perform()
            
            # Enter random message
            self._human_like_type(self.driver.switch_to.active_element, random.choice(self.random_messages))
            self.log_signal.emit("Entered random message.")
            self.cpu_intensive_delay(1.0, 2.0)

            # Send email
            self.log_signal.emit("Attempting to click 'Send' button...")
            try:
                send_icon_element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'i.fui-Icon-font.rb9zq.___1ggnnpz.f14t3ns0.fne0op0.fg4l7m0.fmd4ok8.f303qgw.f1krtbx5'))
                )
                try:
                    send_button = send_icon_element.find_element(By.XPATH, "./ancestor::button[1]")
                    send_button.click()
                    self.log_signal.emit("Clicked 'Send' button via icon's parent.")
                except Exception as e_parent_click:
                    self.log_signal.emit(f"Could not click icon's parent button ({e_parent_click}). Trying to click the icon directly...")
                    send_icon_element.click()
                    self.log_signal.emit("Clicked 'Send' icon directly.")
            except Exception as e_send_button:
                self.log_signal.emit(f"Failed to find or click 'Send' button ({e_send_button}). Attempting CTRL+ENTER...")
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
                self.log_signal.emit("Pressed CTRL+ENTER to send email.")
                
            time.sleep(random.uniform(3, 5))
            self.log_signal.emit(f"Email sent to {', '.join(target_emails_for_one_send)}")

        except Exception as e:
            self.log_signal.emit(f"Failed during email composition and sending: {e}")
            raise

        # DO NOT re-navigate or re-extract. Data is already collected.
        
        # Finalize the subjects list to have exactly 2 entries.
        if len(self.collected_subjects) >= 1:
            self.collected_subjects.append("Hey! This is Plan B")
            self.collected_subjects = self.collected_subjects[:2] # Ensure exactly 2
        else:
            self.log_signal.emit("Warning: No subject was captured. Using two default subjects.")
            self.collected_subjects = ["Hello! I am automating some things.", "Hey! This is Plan B"]

        # Log final collected data
        self.log_signal.emit(f"Final Collected Emails: {self.collected_emails}")
        self.log_signal.emit(f"Final Collected Subjects: {self.collected_subjects}")
        self.progress_update_signal.emit(45, "Outlook processing complete.")

    def _initialize_recovery_form(self):
        """Navigates to recovery form and enters initial details."""
        self.progress_update_signal.emit(45, "Initializing recovery form...")
        self.log_signal.emit("Navigating to Microsoft Recovery page (account.live.com/acsr)...")
        self.driver.get("https://account.live.com/acsr")

        self.log_signal.emit("Waiting for AccountNameInput field...")
        self.log_signal.emit("Please complete CAPTCHA + email verification in browser. The bot will auto-detect when to proceed.")
        account_name_input_field = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.ID, "AccountNameInput"))
        )
        self.log_signal.emit("AccountNameInput field found.")
        self.progress_update_signal.emit(50, "Recovery form loaded.")
        time.sleep(random.uniform(1.5, 3.0))

        if self.email_addr == "Not Available":
            self.log_signal.emit("Primary email not found, cannot proceed with recovery.")
            raise Exception("Primary email for recovery not available.")

        self._human_like_type(account_name_input_field, self.email_addr)
        self.log_signal.emit(f"Entered primary email for recovery: {self.email_addr}")
        time.sleep(random.uniform(1.0, 2.0))

        ActionChains(self.driver).send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(1.0, 2.0))

        alt_emails_options = ["", ""]
        chosen_alt_email = random.choice(alt_emails_options)
        
        # Per instructions, assuming TAB moved focus correctly, type into the active element without locating it.
        active_field = self.driver.switch_to.active_element
        self._human_like_type(active_field, chosen_alt_email)
        
        self.alt_email = chosen_alt_email
        self.log_signal.emit(f"Entered alternate contact email: {self.alt_email}")
        self.progress_update_signal.emit(55, "Alternate email entered.")

        for _ in range(4):
            time.sleep(random.uniform(0.5, 1.0))
            ActionChains(self.driver).send_keys(Keys.TAB).perform()

    def _wait_for_identity_form_and_fill(self):
        """Waits for the identity verification form to appear and then fills it."""
        self.progress_update_signal.emit(60, "Waiting for identity verification form...")
        dob_field_found = False
        wait_start_time = time.time()
        timeout_duration = 6.9 * 60

        while (time.time() - wait_start_time) < timeout_duration:
           try:
               WebDriverWait(self.driver, 5).until(
                   EC.presence_of_element_located((By.ID, "BirthDate_monthInput"))
               )
               dob_field_found = True
               break
           except:
              time.sleep(random.uniform(3, 6))

        if not dob_field_found:
            self.log_signal.emit("Timeout: Identity form (DOB fields) did not appear within 6.9 minutes. Please manually fill or restart.")
            raise Exception("Identity form did not appear.")
        else:
            self.log_signal.emit("✅ Identity verification form loaded successfully! Auto-filling...")
            self.progress_update_signal.emit(65, "Identity form loaded. Auto-filling details...")
            self._fill_identity_details()

    def _fill_identity_details(self):
        """Fills the identity verification form with scraped data."""
        if not self.driver:
            self.log_signal.emit("❌ Error: WebDriver is not initialized for identity verification. Browser might have been closed prematurely.")
            raise Exception("WebDriver not initialized.")

        self.log_signal.emit("▶️ Identity form filling initiated automatically.")
        self.log_signal.emit("[DEBUG] Current scraped values:")
        self.log_signal.emit(f"  First Name: {self.first_name}")
        self.log_signal.emit(f"  Last Name: {self.last_name}")
        self.log_signal.emit(f"  DOB: {self.dob}")
        self.log_signal.emit(f"  Country: {self.country}")
        self.log_signal.emit(f"  Postal: {self.postal}")

        all_data_missing = (self.first_name == "Not Available" or not self.first_name.strip()) and \
                           (self.last_name == "Not Available" or not self.last_name.strip()) and \
                           (self.dob == "Not Available" or not self.dob.strip()) and \
                           (self.country == "Not Available" or not self.country.strip()) and \
                           (not self.postal.strip())

        if all_data_missing:
            self.log_signal.emit("❌ Error: All critical identity information is missing. Cannot proceed with form filling.")
            raise Exception("All identity data missing.")

        actions = ActionChains(self.driver)
        
        self.progress_update_signal.emit(70, "Entering personal details...")

        try:
            first_name_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='FirstNameInput']"))
            )
            if self.first_name != "Not Available" and self.first_name.strip():
                self._human_like_type(first_name_field, self.first_name)
                self.log_signal.emit(f"Entered First Name: {self.first_name}")
            else:
                self.log_signal.emit("Skipping First Name: data not available.")
        except Exception as e:
            self.log_signal.emit(f"⚠️ First name field not found or input failed: {e}")

        time.sleep(random.uniform(0.8, 1.5))
        
        # Press TAB once to move focus to the Last Name field
        self.log_signal.emit("Tabbing to Last Name field...")
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0))

        # Type the last name into the newly focused (active) element
        if self.last_name != "Not Available" and self.last_name.strip():
            try:
                last_name_field = self.driver.switch_to.active_element
                self._human_like_type(last_name_field, self.last_name)
                self.log_signal.emit(f"Entered Last Name (into active element): {self.last_name}")
            except Exception as e:
                 self.log_signal.emit(f"⚠️ Could not type last name into active element: {e}")
        else:
            self.log_signal.emit("Skipping Last Name: data not available.")

        time.sleep(random.uniform(1.5, 2.5))

        if self.dob and "/" in self.dob and self.dob != "Not Available":
            m, d, y = self.dob.split("/")
            try:
                month_select = Select(WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "BirthDate_monthInput"))))
                month_select.select_by_value(m.lstrip("0"))
                time.sleep(random.uniform(0.5, 1.0))

                day_select = Select(WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "BirthDate_dayInput"))))
                day_select.select_by_value(d.lstrip("0"))
                time.sleep(random.uniform(0.5, 1.0))

                year_select = Select(WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "BirthDate_yearInput"))))
                year_select.select_by_value(y)
                self.log_signal.emit(f"Entered DOB: {m}/{d}/{y}")
            except Exception as e_dob:
                self.log_signal.emit(f"⚠️ Failed to enter DOB parts: {e_dob}")
        else:
            self.log_signal.emit("Skipping DOB: data not available or invalid format.")

        time.sleep(random.uniform(1.0, 2.0))

        country_to_select = self.country if self.country != "Not Available" else "United States"
        if self.country != "Not Available" and self.country.strip():
            try:
                country_select = Select(WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "CountryInput"))))
                country_select.select_by_visible_text(country_to_select)
                self.log_signal.emit(f"Selected Country: {country_to_select}")
            except Exception as e:
                self.log_signal.emit(f"⚠️ Country '{country_to_select}' not selectable or field not found: {e}")
        else:
            self.log_signal.emit("Skipping Country: data not available.")

        time.sleep(random.uniform(1.0, 2.0))
        self.progress_update_signal.emit(75, "Entering country and checking for state...")

        try:
            state_select_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "StateInput"))
            )
            state_select = Select(state_select_element)
            
            options = [option.text for option in state_select.options if option.text and option.text != "Select..."]
            
            if options:
                random_state = random.choice(options)
                state_select.select_by_visible_text(random_state)
                self.log_signal.emit(f"Selected random State: {random_state}")
            else:
                self.log_signal.emit("No selectable states found in the dropdown.")
        except Exception as e_state:
            self.log_signal.emit(f"⚠️ State field not found or could not select state (skipping): {e_state}")
        
        time.sleep(random.uniform(1.0, 2.0))
        self.progress_update_signal.emit(80, "Filling postal code and final steps...")

        if self.postal and self.postal.strip():
            try:
                postal_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@id='PostalCodeInput']"))
                )
                # Click the element, then type the postal code
                postal_field.click()
                self.log_signal.emit("Clicked Postal Code field.")
                self._human_like_type(postal_field, self.postal)
                self.log_signal.emit(f"Entered Postal Code: {self.postal}")
                
                # Wait 1 sec, TAB, then type 'Belgium'
                time.sleep(1)
                actions.send_keys(Keys.TAB).perform()
                self.log_signal.emit("Pressed TAB after postal code.")
                time.sleep(random.uniform(0.5, 1.0))

                # Type "Belgium" into the newly focused field
                self.log_signal.emit("Typing 'Belgium' into active element...")
                active_belgium_field = self.driver.switch_to.active_element
                self._human_like_type(active_belgium_field, "Belgium")
                self.log_signal.emit("Typed 'Belgium'.")
                
            except Exception as e_postal:
                self.log_signal.emit(f"⚠️ Postal field/Belgium entry sequence failed: {e_postal}")
        else:
            self.log_signal.emit("Skipping Postal Code: data not available.")

        time.sleep(random.uniform(1.0, 2.0))
        
        # Continue with the original workflow's Enter press
        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed Enter after Belgium sequence.")
        self.progress_update_signal.emit(85, "Completing final form fields...")

    def _handle_product_option_mail(self):
        """Waits for and interacts with ProductOptionMail checkbox and password field."""
        self.log_signal.emit("Waiting for ProductOptionMail checkbox to appear...")
        self.progress_update_signal.emit(90, "Handling ProductOptionMail and password...")
        try:
            checkbox = WebDriverWait(self.driver, 300).until(  
                EC.presence_of_element_located((By.ID, "ProductOptionMail"))
            )
            self.log_signal.emit("ProductOptionMail checkbox found!")

            time.sleep(random.uniform(1.0, 2.0))

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='password' or @name='Password']"))
            )
            self._human_like_type(password_field, self.account_password)
            self.log_signal.emit("Entered account password")

            time.sleep(random.uniform(0.8, 1.5))

            checkbox.click()
            self.log_signal.emit("Clicked ProductOptionMail checkbox")

            time.sleep(random.uniform(0.8, 1.5))

            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            self.log_signal.emit("Pressed Enter after checkbox")

        except Exception as e_checkbox:
            self.log_signal.emit(f"Error handling ProductOptionMail checkbox or password field: {e_checkbox}")
            raise

    def _perform_final_email_sequence(self):
        """Enters additional email addresses and subjects (replacing messages)."""
        self.log_signal.emit("Starting final email and subject sequence...")
        self.progress_update_signal.emit(95, "Entering final emails and subjects...")
        time.sleep(random.uniform(2.5, 4.0))

        actions = ActionChains(self.driver)

        # Ensure we have at least 3 emails for input, pad if necessary
        emails_to_enter = self.collected_emails[:3] 

        # Enter first email
        try:
            email_field1 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//input[contains(@type, 'email') or contains(@type, 'text')])[1]")))
            self._human_like_type(email_field1, emails_to_enter[0])
            self.log_signal.emit(f"Entered first email: {emails_to_enter[0]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter first email: {e}")
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        # Enter second email
        try:
            email_field2 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//input[contains(@type, 'email') or contains(@type, 'text')])[2]")))
            self._human_like_type(email_field2, emails_to_enter[1])
            self.log_signal.emit(f"Entered second email: {emails_to_enter[1]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter second email: {e}")
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        # Enter third email
        try:
            email_field3 = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//input[contains(@type, 'email') or contains(@type, 'text')])[3]")))
            self._human_like_type(email_field3, emails_to_enter[2])
            self.log_signal.emit(f"Entered third email: {emails_to_enter[2]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter third email: {e}")
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        self.log_signal.emit("Pressing TAB twice to reach first subject field...")
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        # Enter first subject
        # self.collected_subjects is guaranteed to have at least 2 items due to _process_outlook_sent_items logic
        first_subject = self.collected_subjects[0]
        self.log_signal.emit(f"Entering first subject: '{first_subject}'")
        # Assuming the tab action moved focus to the subject field
        try:
            current_active_element = self.driver.switch_to.active_element # Get currently focused element
            self._human_like_type(current_active_element, first_subject) # Type into active element
        except Exception as e:
            self.log_signal.emit(f"Could not find active element for first subject or input failed: {e}")
            actions.send_keys(first_subject).perform() # Fallback
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        # Enter second subject
        # self.collected_subjects is guaranteed to have at least 2 items
        second_subject = self.collected_subjects[1]
        self.log_signal.emit(f"Entering second subject: '{second_subject}'")
        # Assuming the tab action moved focus to the second subject field
        try:
            current_active_element = self.driver.switch_to.active_element # Get currently focused element
            self._human_like_type(current_active_element, second_subject) # Type into active element
        except Exception as e:
            self.log_signal.emit(f"Could not find active element for second subject or input failed: {e}")
            actions.send_keys(second_subject).perform() # Fallback
        time.sleep(random.uniform(0.5, 1.0)) # Existing pause, keeping it

        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed Enter to submit form.")

        self.log_signal.emit("Waiting 3 seconds before final Enter...")
        time.sleep(random.uniform(3.0, 5.0))

        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed final Enter (if any subsequent dialog).")

        self.log_signal.emit("Waiting 5 seconds before closing browser...")
        time.sleep(random.uniform(5.0, 8.0))
        self.progress_update_signal.emit(100, "Finalizing process.")

    def _get_profile_and_address_html_content(self):
        # Helper to generate the HTML content for profile and address, to avoid duplication
        postal_codes_str = self.postal if self.postal else "Not Found"

        # Also include extracted emails and subjects
        emails_html = "<br>".join(self.collected_emails) if self.collected_emails else "<i>None collected</i>"
        subjects_html = "<br>".join(self.collected_subjects) if self.collected_subjects else "<i>None collected</i>"

        return (
            f"""<h2>----- Profile Information -----</h2>
<p>
  <b>Full Name:</b> {self.first_name} {self.last_name}<br>
  <b>First Name:</b> {self.first_name}<br>
  <b>Last Name:</b> {self.last_name}<br>
  <b>DOB:</b> {self.dob}<br>
  <b>Country:</b> {self.country}<br>
  <b>Email:</b> {getattr(self, 'email_addr', 'Not Available')}<br>
  <b>Password:</b> {self.account_password}
</p>
<h2>----- Address Book -----</h2>
<p>
  <b>Postal Codes:</b> {postal_codes_str}
</p>
<h2>----- Outlook Emails & Subjects (for Recovery Form) -----</h2>
<p>
  <b>Collected Emails:</b><br>{emails_html}<br>
  <b>Collected Subjects:</b><br>{subjects_html}
</p>"""
        )

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.log_signal.emit("Starting scraping process with CPU optimization and human-like typing...")
            self.progress_update_signal.emit(0, "Starting bot...")

            self._initialize_driver()
            self._perform_login_check()
            self._extract_profile_info()
            postal_codes_str = self._extract_postal_code() # Get postal codes for the report
            self._process_outlook_sent_items() # New: Process Outlook Sent Items

            profile_and_address_html_content = self._get_profile_and_address_html_content()

            cursor_html = f"""<div style="font-family: Segoe UI; color: white;">
                <h3 style="color: #00BFFF;">📋 Profile & Address Information Extracted</h3>
                {profile_and_address_html_content}
                <hr style="border-color: #444; margin: 20px 0;">
                <p style="color: #66FFFF;"><i>Preparing for account recovery process...This will take a few seconds.</i></p>
            </div>"""
            self.intermediate_result_signal.emit(cursor_html)

            time.sleep(random.uniform(3, 5))
            self.log_signal.emit("✅ Starting RECOVERY block now...")

            # Retry mechanism loop
            recovery_attempts = 0
            max_recovery_attempts = 3 # Limit retries to prevent infinite loops
            
            while recovery_attempts < max_recovery_attempts:
                recovery_attempts += 1
                self.log_signal.emit(f"Starting account recovery automation (Attempt {recovery_attempts})...")
                try:
                    # If it's a retry, we don't need to re-extract profile or outlook data
                    # Just go directly to the recovery form
                    if recovery_attempts == 1:
                        self._initialize_recovery_form()
                    else:
                        self.log_signal.emit("Retrying recovery form with previously gathered info...")
                        self.driver.get("https://account.live.com/acsr") # Navigate back to form
                        WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.ID, "AccountNameInput")))
                        
                        # Re-enter initial email and alt email with human-like typing if needed (form might clear on re-load)
                        account_name_input_field = self.driver.find_element(By.ID, "AccountNameInput")
                        self._human_like_type(account_name_input_field, self.email_addr)
                        time.sleep(random.uniform(1.0, 2.0))
                        ActionChains(self.driver).send_keys(Keys.TAB).perform()
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Assuming the tab action moved focus correctly, type into the active element.
                        alt_email_field = self.driver.switch_to.active_element
                        self._human_like_type(alt_email_field, self.alt_email)
                        time.sleep(random.uniform(1.0, 2.0))
                        for _ in range(4): # Tab to next section
                            ActionChains(self.driver).send_keys(Keys.TAB).perform()
                            time.sleep(random.uniform(0.5, 1.0))


                    self._wait_for_identity_form_and_fill() # This method now includes filling details
                    self._handle_product_option_mail()
                    self._perform_final_email_sequence()

                    # After successful submission, ask for retry decision
                    self.ask_retry_signal.emit()
                    self._retry_response = None # Reset for next decision
                    
                    # Wait for the UI response
                    loop = QtCore.QEventLoop()
                    self.retry_decision_signal.connect(loop.quit)
                    loop.exec()

                    if self._retry_response: # User clicked 'Yes'
                        self.log_signal.emit("User confirmed reset link received. Task successful!")
                        recovery_status_html_info = (f"<b>Status:</b> Account recovery process completed successfully.<br>"
                                                   f"<b>Recovery Email Used:</b> {self.alt_email}<br>"
                                                   f"<b>Form Data:</b> All information filled and submitted automatically.<br>"
                                                   f"<b>Additional Emails Provided:</b> {'<br>'.join(self.collected_emails) if self.collected_emails else 'None'}<br>"
                                                   f"<b>Subjects Provided:</b> {'<br>'.join(self.collected_subjects) if self.collected_subjects else 'None'}")
                        final_result_html = (
                            f"""<html>
                              <body style="font-family: Segoe UI; color: white;">
                                <h2 style="color: #00FF00;">✅ TASK SUCCESSFUL ✅</h2>
                                {self._get_profile_and_address_html_content()}
                                <h2 style="color: #FFA500;">----- Recovery Process -----</h2>
                                <p style="color: #90EE90;">
                                  {recovery_status_html_info}
                                </p>
                              </body>
                            </html>"""
                        )
                        self.full_process_completed_signal.emit(final_result_html)
                        break # Exit the retry loop

                    else: # User clicked 'No, let's do again'
                        self.log_signal.emit("User requested retry. Re-attempting recovery form...")
                        # Loop continues for another attempt
                except Exception as e_recovery_attempt:
                    self.log_signal.emit(f"❌ Error during recovery attempt {recovery_attempts}: {str(e_recovery_attempt)}")
                    # If an error occurs during an attempt, the loop will continue to the next attempt
                    # unless max_recovery_attempts is reached.
                    self.cpu_intensive_delay(3, 5) # Small delay before next attempt
            else: # This 'else' block executes if the while loop completes without a 'break' (i.e., max attempts reached)
                self.log_signal.emit(f"Maximum recovery attempts ({max_recovery_attempts}) reached. Could not confirm success.")
                recovery_status_html_info = (f"<b>Status:</b> Max recovery attempts reached. Please check manually.<br>"
                                           f"<b>Recovery Email Used:</b> {self.alt_email}<br>"
                                           f"<b>Form Data:</b> Information filled and submitted automatically.<br>"
                                           f"<b>Additional Emails Provided:</b> {'<br>'.join(self.collected_emails) if self.collected_emails else 'None'}<br>"
                                           f"<b>Subjects Provided:</b> {'<br>'.join(self.collected_subjects) if self.collected_subjects else 'None'}")
                final_result_html = (
                    f"""<html>
                      <body style="font-family: Segoe UI; color: white;">
                        <h2 style="color: #FF8C00;">⚠️ PROCESS INCOMPLETE ⚠️</h2>
                        {self._get_profile_and_address_html_content()}
                        <h2 style="color: #FFA500;">----- Recovery Process Status -----</h2>
                        <p style="color: #FF6347;">
                          {recovery_status_html_info}
                        </p>
                      </body>
                    </html>"""
                )
                self.full_process_completed_signal.emit(final_result_html)

        except Exception as e:
            error_message = f"❌ Process failed: {str(e)}"
            self.log_signal.emit(error_message)
            recovery_status_html_info = (f"<b>Status:</b> Account recovery process encountered an error.<br>"
                                       f"<b>Error:</b> {str(e)}<br>"
                                       f"<b>Recovery Email (if set before error):</b> {self.alt_email}")
            final_result_html = (
                f"""<html>
                  <body style="font-family: Segoe UI; color: white;">
                    <h2 style="color: #FF0000;">❌ PROCESS FAILED ❌</h2>
                    {self._get_profile_and_address_html_content()}
                    <h2 style="color: #FFA500;">----- Recovery Process Status -----</h2>
                    <p style="color: #FF6347;">
                      {recovery_status_html_info}
                    </p>
                  </body>
                </html>"""
            )
            self.full_process_completed_signal.emit(final_result_html)
        finally:
            self.close_browser()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pass reset BOT")
        self.setFixedSize(1000, 800)
        self.initUI()

    def initUI(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        heading = QtWidgets.QLabel("Microsoft Account Tool", self)
        heading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        layout.addWidget(heading)

        self.scrape_button = QtWidgets.QPushButton("Login and start automating", self)
        self.scrape_button.setFixedHeight(60)
        self.scrape_button.setStyleSheet(
            """
            font-size: 20px;
            padding: 15px;
            background-color: #00BFFF;
            color: white;
            border-radius: 10px;
            """
        )
        self.scrape_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.scrape_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-size: 14px; background-color: #2b2b2b; color: #66FFFF;")
        self.text_edit.setPlaceholderText("Logs and results will appear here...")
        layout.addWidget(self.text_edit)

        credit = QtWidgets.QLabel("Made and developed by H4X Ayaan", self)
        credit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        credit.setStyleSheet("font-size: 12px; color: lightgray;")
        layout.addWidget(credit)

        self.setStyleSheet("background-color: #1e1e1e;")

    def start_scraping(self):
        password, ok = QtWidgets.QInputDialog.getText(
            self,
            "Account Password",
            "Enter the account password:",
            QtWidgets.QLineEdit.EchoMode.Password
        )
        if not ok or not password:
            self.append_log("No password provided. Aborting scraping process.")
            return

        self.text_edit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% - Initializing...")
        self.scrape_button.setEnabled(False)
        self.thread = QtCore.QThread()
        self.worker = ScraperWorker(password)
        self.worker.moveToThread(self.thread)
        self.worker.log_signal.connect(self.append_log)
        
        self.worker.progress_update_signal.connect(self.update_progress_bar)
        self.worker.initial_setup_completed_signal.connect(self.initial_setup_done_slot)
        self.worker.full_process_completed_signal.connect(self.full_process_finished_slot)
        self.worker.intermediate_result_signal.connect(self.insert_html)

        # Connect new retry signals
        self.worker.ask_retry_signal.connect(self.ask_for_retry)
        # Connect MainWindow's decision signal back to worker (worker.retry_decision_signal is defined in worker)
        # This creates a direct connection from MainWindow's UI interaction back to the worker's slot.
        # No need to redefine in MainWindow, just connect to the worker's signal.
        
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @QtCore.pyqtSlot(int, str)
    def update_progress_bar(self, value, text):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"%p% - {text}")

    @QtCore.pyqtSlot(str)
    def initial_setup_done_slot(self, result_html):
        """Slot to handle when initial scraping and recovery form setup is complete."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(result_html)

    @QtCore.pyqtSlot(str)
    def full_process_finished_slot(self, result_html):
        """Slot to handle when the entire process (including identity verification) is complete or failed."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(result_html)
        self.scrape_button.setEnabled(True)
        # Ensure thread is quit and waited for only once, after the final resolution
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100% - Done!")

    @QtCore.pyqtSlot()
    def ask_for_retry(self):
        """Asks the user if they received the reset link and sends decision back to worker."""
        self.append_log("Bot: Did you receive the reset link? Waiting for your response...")
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Link Received?",
            "Did you receive the reset link?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes # Default to Yes
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.append_log("User: Yes, I received the reset link.")
            self.worker.retry_decision_signal.emit(True)
        else:
            self.append_log("User: No, let's do it again.")
            self.worker.retry_decision_signal.emit(False)


    def append_log(self, message):
        self.text_edit.append(message)

    @QtCore.pyqtSlot(str)
    def insert_html(self, html):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertBlock()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    font_hash = hashlib.sha256("Segoe UI".encode()).hexdigest()
    font = QtGui.QFont("Segoe UI", 10)
    app.setFont(font)

    startup_processing = CPUIntensiveProcessor.mathematical_operations(99999)
    window = MainWindow()
    window.show()

    app.exec()