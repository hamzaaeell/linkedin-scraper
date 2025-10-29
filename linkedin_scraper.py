import requests
import json
import time as tm
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote
import pandas as pd

class LinkedInJobScraper:
    def __init__(self, config=None, config_file=None):
        """
        Initialize the LinkedIn Job Scraper
        
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
            "pages_to_scrape": 5,
            "days_to_scrape": 7,
            "description_keywords_exclude": [],
            "title_keywords_include": [],
            "title_keywords_exclude": [],
            "company_exclude": [],
            "languages": ["en"],
            "remote_only": true
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
    
    def extract_job_cards(self, soup):
        """
        Extract job card information from search results page
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of job dictionaries
        """
        joblist = []
        try:
            divs = soup.find_all('div', class_='base-search-card__info')
        except AttributeError:
            print("No job cards found on page")
            return joblist
            
        for item in divs:
            try:
                # Extract basic job information
                title_element = item.find('h3')
                title = title_element.text.strip() if title_element else ''
                
                company_element = item.find('a', class_='hidden-nested-link')
                company = company_element.text.strip().replace('\n', ' ') if company_element else ''
                company_url = company_element.get('href', '') if company_element else ''
                
                location_element = item.find('span', class_='job-search-card__location')
                location = location_element.text.strip() if location_element else ''
                
                # Extract job URL from parent div
                parent_div = item.parent
                entity_urn = parent_div.get('data-entity-urn', '')
                job_posting_id = entity_urn.split(':')[-1] if entity_urn else ''
                job_url = f'https://www.linkedin.com/jobs/view/{job_posting_id}/' if job_posting_id else ''
                
                # Extract posting date
                date_tag_new = item.find('time', class_='job-search-card__listdate--new')
                date_tag = item.find('time', class_='job-search-card__listdate')
                date = (date_tag.get('datetime') if date_tag else 
                       date_tag_new.get('datetime') if date_tag_new else '')
                
                job = {
                    'title': title,
                    'company': company,
                    'company_url': company_url,
                    'location': location,
                    'date': date,
                    'job_url': job_url,
                    'job_description': '',
                    'scraped_at': datetime.now().isoformat()
                }
                joblist.append(job)
                
            except Exception as e:
                print(f"Error extracting job card: {e}")
                continue
                
        return joblist
    
    def extract_job_description(self, job_url):
        """
        Extract full job description from individual job page
        
        Args:
            job_url (str): URL of the job posting
            
        Returns:
            str: Job description text
        """
        if not job_url:
            return "No job URL available"
            
        soup = self.get_with_retry(job_url)
        if not soup:
            return "Failed to fetch job page"
            
        try:
            description_div = soup.find('div', class_='description__text description__text--rich')
            if description_div:
                # Remove unwanted elements for cleaner text
                for element in description_div.find_all(['span', 'a']):
                    element.decompose()
                
                # Format bullet points
                for ul in description_div.find_all('ul'):
                    for li in ul.find_all('li'):
                        li.insert(0, '-')
                
                text = description_div.get_text(separator='\n').strip()
                # Clean up text
                text = text.replace('\n\n', '\n')
                text = text.replace('::marker', '-')
                text = text.replace('-\n', '- ')
                text = text.replace('Show less', '').replace('Show more', '')
                return text
            else:
                return "Job description not found"
        except Exception as e:
            print(f"Error extracting description from {job_url}: {e}")
            return "Error extracting job description"
    
    def filter_jobs(self, joblist):
        """
        Filter jobs based on configured criteria
        
        Args:
            joblist (list): List of job dictionaries
            
        Returns:
            list: Filtered list of jobs
        """
        filtered_jobs = []
        
        for job in joblist:
            # Skip if job is too old
            if job['date']:
                try:
                    job_date = datetime.strptime(job['date'], '%Y-%m-%d').date()
                    if job_date < datetime.now().date() - timedelta(days=self.config['days_to_scrape']):
                        continue
                except ValueError:
                    pass
            
            # Filter by title keywords (include)
            if self.config['title_keywords_include']:
                if not any(word.lower() in job['title'].lower()
                          for word in self.config['title_keywords_include']):
                    continue
            
            # Filter by title keywords (exclude)
            if self.config['title_keywords_exclude']:
                if any(word.lower() in job['title'].lower()
                      for word in self.config['title_keywords_exclude']):
                    continue
            
            # Filter by company exclude list
            if self.config['company_exclude']:
                if any(word.lower() in job['company'].lower()
                      for word in self.config['company_exclude']):
                    continue
            
            # Filter for remote jobs only if specified
            if self.config.get('remote_only', False):
                location_lower = job['location'].lower()
                if not any(remote_indicator in location_lower for remote_indicator in ['remote', 'united states', 'worldwide', 'global', 'anywhere']):
                    continue
            
            filtered_jobs.append(job)
        
        return filtered_jobs
    
    def remove_duplicates(self, joblist):
        """
        Remove duplicate jobs based on title, company, and date
        
        Args:
            joblist (list): List of job dictionaries
            
        Returns:
            list: Deduplicated list of jobs
        """
        seen = set()
        unique_jobs = []
        
        for job in joblist:
            # Create a unique identifier for the job
            identifier = (job['title'].lower(), job['company'].lower(), job['date'])
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def scrape_jobs(self):
        """
        Main method to scrape jobs based on configuration
        
        Returns:
            list: List of job dictionaries with descriptions
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
                jobs = self.extract_job_cards(soup)
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
        
        # Filter jobs
        all_jobs = self.filter_jobs(all_jobs)
        print(f"Jobs after filtering: {len(all_jobs)}")
        
        # Get detailed job descriptions
        print("Fetching job descriptions...")
        for i, job in enumerate(all_jobs):
            print(f"Getting description for job {i+1}/{len(all_jobs)}: {job['title']}")
            job['job_description'] = self.extract_job_description(job['job_url'])
            tm.sleep(1)  # Delay between description requests
        
        return all_jobs
    
    def save_to_csv(self, jobs, filename='linkedin_jobs.csv'):
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
    
    def save_to_json(self, jobs, filename='linkedin_jobs.json'):
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
    """Example usage of the LinkedIn Job Scraper"""
    import sys
    
    # Check if config file is provided as command line argument
    config_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if config_file:
        print(f"Loading configuration from: {config_file}")
        # Initialize scraper with config file
        scraper = LinkedInJobScraper(config_file=config_file)
    else:
        print("Using default configuration")
        # Configuration inline
        config = {
            "keywords": "python developer",
            "location": "United States",
            "job_type": "2",  # 2 = remote
            "timespan": "r84600",  # Last 24 hours
            "pages_to_scrape": 3,
            "days_to_scrape": 7,
            "title_keywords_include": ["python", "developer", "backend"],
            "title_keywords_exclude": ["senior", "lead", "manager"],
            "company_exclude": [],
            "languages": ["en"],
            "remote_only": true,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }
        # Initialize scraper with inline config
        scraper = LinkedInJobScraper(config)
    
    # Scrape jobs
    jobs = scraper.scrape_jobs()
    
    # Save results
    scraper.save_to_csv(jobs)
    scraper.save_to_json(jobs)
    
    # Print summary
    print(f"\nScraping completed!")
    print(f"Total jobs found: {len(jobs)}")
    print("\nSample job:")
    if jobs:
        job = jobs[0]
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Company URL: {job['company_url']}")
        print(f"Location: {job['location']}")
        print(f"Date: {job['date']}")
        print(f"Job URL: {job['job_url']}")
        print(f"Description: {job['job_description'][:200]}...")


if __name__ == "__main__":
    main()