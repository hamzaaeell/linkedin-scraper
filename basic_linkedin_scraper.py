import requests
import json
import time as tm
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
import pandas as pd


class BasicLinkedInScraper:
    def __init__(self, config=None, config_file=None):
        """
        Initialize the Basic LinkedIn Scraper for extracting only job titles,
        company names, and company LinkedIn URLs
        
        Args:
            config (dict): Configuration dictionary with search parameters
            config_file (str): Path to JSON configuration file
        """
        if config_file and not config:
            config = self.load_config_from_file(config_file)
        
        self.config = config or self.get_default_config()
        self.session = requests.Session()
        self.session.headers.update(self.config.get('headers', {}))
    
    def load_config_from_file(self, config_file):
        """
        Load configuration from JSON file
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            dict: Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found. Using default config.")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}. Using default config.")
            return self.get_default_config()
        
    def get_default_config(self):
        """Get default configuration for the scraper"""
        return {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            "proxies": {},
            "keywords": "software developer",
            "location": "United States",
            "job_type": "2",  # 0=onsite, 1=hybrid, 2=remote, empty=any
            "timespan": "r84600",  # r84600 = 24 hours, r604800 = 1 week
            "pages_to_scrape": 5
        }
    
    def get_with_retry(self, url, retries=3, delay=2):
        """
        Make HTTP request with retry logic
        
        Args:
            url (str): URL to request
            retries (int): Number of retry attempts
            delay (int): Delay between retries in seconds
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for i in range(retries):
            try:
                proxies = self.config.get('proxies', {}) if self.config.get('proxies') else {}
                response = self.session.get(url, headers=self.config['headers'], 
                                          proxies=proxies, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Request failed for URL: {url}, attempt {i+1}/{retries}. Error: {e}")
                if i < retries - 1:
                    tm.sleep(delay)
                    delay *= 2  # Exponential backoff
        return None
    
    def extract_basic_job_info(self, soup):
        """
        Extract only job title, company name, and company LinkedIn URL from search results page
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of job dictionaries with basic information
        """
        joblist = []
        try:
            divs = soup.find_all('div', class_='base-search-card__info')
        except AttributeError:
            print("No job cards found on page")
            return joblist
            
        for item in divs:
            try:
                # Extract job title
                title_element = item.find('h3')
                title = title_element.text.strip() if title_element else ''
                
                # Extract company name and LinkedIn URL
                company_element = item.find('a', class_='hidden-nested-link')
                company = company_element.text.strip().replace('\n', ' ') if company_element else ''
                company_url = company_element.get('href', '') if company_element else ''
                
                job = {
                    'title': title,
                    'company': company,
                    'company_url': company_url,
                    'scraped_at': datetime.now().isoformat()
                }
                joblist.append(job)
                
            except Exception as e:
                print(f"Error extracting job info: {e}")
                continue
                
        return joblist
    
    def remove_duplicates(self, joblist):
        """
        Remove duplicate jobs based on title and company
        
        Args:
            joblist (list): List of job dictionaries
            
        Returns:
            list: Deduplicated list of jobs
        """
        seen = set()
        unique_jobs = []
        
        for job in joblist:
            # Create a unique identifier for the job
            identifier = (job['title'].lower(), job['company'].lower())
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def scrape_jobs(self):
        """
        Main method to scrape basic job information based on configuration
        
        Returns:
            list: List of job dictionaries with basic information
        """
        all_jobs = []
        keywords = quote(self.config['keywords'])
        location = quote(self.config['location'])
        job_type = self.config['job_type']
        timespan = self.config['timespan']
        
        print(f"Scraping jobs for: {self.config['keywords']} in {self.config['location']}")
        
        # Scrape multiple pages
        for page in range(self.config['pages_to_scrape']):
            start = page * 25
            url = (f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                   f"?keywords={keywords}&location={location}&f_TPR=&f_WT={job_type}"
                   f"&geoId=&f_TPR={timespan}&start={start}")
            
            print(f"Scraping page {page + 1}: {url}")
            soup = self.get_with_retry(url)
            
            if soup:
                jobs = self.extract_basic_job_info(soup)
                all_jobs.extend(jobs)
                print(f"Found {len(jobs)} jobs on page {page + 1}")
            else:
                print(f"Failed to fetch page {page + 1}")
            
            # Delay between requests to avoid rate limiting
            tm.sleep(2)
        
        print(f"Total job cards scraped: {len(all_jobs)}")
        
        # Remove duplicates
        all_jobs = self.remove_duplicates(all_jobs)
        print(f"Jobs after removing duplicates: {len(all_jobs)}")
        
        return all_jobs
    
    def save_to_csv(self, jobs, filename='basic_linkedin_jobs.csv'):
        """
        Save jobs to CSV file
        
        Args:
            jobs (list): List of job dictionaries
            filename (str): Output CSV filename
        """
        if not jobs:
            print("No jobs to save")
            return
        
        df = pd.DataFrame(jobs)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(jobs)} jobs to {filename}")
    
    def save_to_json(self, jobs, filename='basic_linkedin_jobs.json'):
        """
        Save jobs to JSON file
        
        Args:
            jobs (list): List of job dictionaries
            filename (str): Output JSON filename
        """
        if not jobs:
            print("No jobs to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jobs)} jobs to {filename}")


def main():
    """Example usage of the Basic LinkedIn Scraper"""
    import sys
    
    # Check if config file is provided as command line argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if config_file:
        print(f"Loading configuration from: {config_file}")
        # Initialize scraper with config file
        scraper = BasicLinkedInScraper(config_file=config_file)
    else:
        print("Using default configuration")
        # Configuration inline
        config = {
            "keywords": "Devops Engineer",
            "location": "United States",
            "job_type": "2",  # 2 = remote
            "timespan": "r84600",  # Last 24 hours
            "pages_to_scrape": 3,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
        # Initialize scraper with inline config
        scraper = BasicLinkedInScraper(config)
    
    # Scrape jobs
    jobs = scraper.scrape_jobs()
    
    # Save results
    scraper.save_to_csv(jobs)
    scraper.save_to_json(jobs)
    
    # Print summary
    print(f"\nScraping completed!")
    print(f"Total jobs found: {len(jobs)}")
    print("\nSample jobs:")
    if jobs:
        for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
            print(f"\nJob {i+1}:")
            print(f"Title: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Company URL: {job['company_url']}")


if __name__ == "__main__":
    main()