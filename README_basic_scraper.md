# Basic LinkedIn Job Scraper

A lightweight Python script that extracts only the essential information from LinkedIn job listings:
- Job title
- Company name
- Company LinkedIn URL

This scraper is optimized for speed by skipping the time-consuming step of fetching individual job description pages.

## Features

- Fast scraping by only parsing search results pages
- Configurable search parameters (keywords, location, job type)
- Duplicate removal based on job title and company
- Export to CSV and JSON formats
- Retry logic with exponential backoff
- Proxy support

## Installation

Install the required packages:

```bash
pip install requests beautifulsoup4 pandas
```

## Usage

### Method 1: Using a configuration file

1. Create a configuration file (see `basic_scraper_config.json` for example)
2. Run the scraper with the config file:

```bash
python basic_linkedin_scraper.py basic_scraper_config.json
```

### Method 2: Using default configuration

Simply run the script without arguments:

```bash
python basic_linkedin_scraper.py
```

## Configuration Options

- `keywords`: Job search keywords (default: "software developer")
- `location`: Job location (default: "United States")
- `job_type`: Job type filter (0=onsite, 1=hybrid, 2=remote, empty=any)
- `timespan`: Time filter (r84600 = 24 hours, r604800 = 1 week)
- `pages_to_scrape`: Number of pages to scrape (default: 5)
- `headers`: HTTP headers for requests
- `proxies`: Proxy configuration (optional)

## Output

The scraper generates two files:
- `basic_linkedin_jobs.csv`: CSV format with job information
- `basic_linkedin_jobs.json`: JSON format with job information

Each job entry contains:
- `title`: Job title
- `company`: Company name
- `company_url`: LinkedIn URL for the company
- `scraped_at`: Timestamp when the job was scraped

## Example Output

```json
[
  {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "company_url": "https://www.linkedin.com/company/tech-corp",
    "scraped_at": "2023-11-15T14:30:22.123456"
  },
  {
    "title": "Backend Engineer",
    "company": "StartupXYZ",
    "company_url": "https://www.linkedin.com/company/startupxyz",
    "scraped_at": "2023-11-15T14:30:22.123456"
  }
]
```

## Performance

This scraper is significantly faster than full-featured scrapers because:
- It only makes requests to search results pages (not individual job pages)
- It extracts minimal information from each page
- It avoids processing large job description texts

Typical performance: 5 pages of results (125 jobs) in under 30 seconds.

## Notes

- LinkedIn may implement rate limiting. The scraper includes delays between requests.
- For large-scale scraping, consider rotating user agents and using proxies.
- The scraper targets specific HTML elements that may change if LinkedIn updates their layout.