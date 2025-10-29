# LinkedIn Job Scraper

A simplified, single-file Python script to scrape job postings from LinkedIn with company URL extraction.

## Features

- Scrapes job postings from LinkedIn based on keywords, location, and time filters
- Extracts comprehensive job information including company LinkedIn URLs
- Filters jobs based on title keywords, company exclusions, and posting date
- Removes duplicate job postings
- Saves results in CSV and JSON formats
- Configurable via JSON file or inline parameters

## Requirements

Install the required packages:

```bash
pip install requests beautifulsoup4 pandas
```

## Usage

### Method 1: Using Configuration File

1. Create a configuration file (example: `scraper_config.json`):

```json
{
  "keywords": "python developer",
  "location": "United States",
  "job_type": "2",
  "timespan": "r84600",
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
```

2. Run the scraper with the config file:

```bash
python linkedin_scraper.py scraper_config.json
```

### Method 2: Using Default Configuration

Simply run the script without arguments:

```bash
python linkedin_scraper.py
```

## Configuration Options

- **keywords**: Job search keywords
- **location**: Location to search for jobs
- **job_type**: Job type filter (0=onsite, 1=hybrid, 2=remote, empty=any)
- **timespan**: Time range for job postings (r84600 = 24 hours, r604800 = 1 week)
- **pages_to_scrape**: Number of pages to scrape per search
- **days_to_scrape**: Maximum age of jobs to consider (in days)
- **title_keywords_include**: List of keywords that must be in job title
- **title_keywords_exclude**: List of keywords to exclude from job titles
- **company_exclude**: List of companies to exclude
- **languages**: Allowed languages for job descriptions
- **remote_only**: Filter for remote jobs only (true/false)
- **headers**: HTTP headers for requests

## Output Fields

The scraper extracts the following fields for each job:

- **title**: Job title
- **company**: Company name
- **company_url**: Company LinkedIn URL ⭐
- **location**: Job location
- **date**: Posting date
- **job_url**: Direct link to job posting
- **job_description**: Full job description
- **scraped_at**: Timestamp when job was scraped

## Output Files

- `linkedin_jobs.csv`: Jobs data in CSV format
- `linkedin_jobs.json`: Jobs data in JSON format

## Example Output

```json
[
  {
    "title": "Python Developer",
    "company": "Tech Company",
    "company_url": "https://www.linkedin.com/company/tech-company",
    "location": "San Francisco, CA",
    "date": "2024-01-15",
    "job_url": "https://www.linkedin.com/jobs/view/123456789/",
    "job_description": "We are looking for a skilled Python developer...",
    "scraped_at": "2024-01-15T10:30:00.000000"
  }
]
```

## Important Notes

- LinkedIn does not allow scraping of their website. Use this script at your own risk.
- It's recommended to use proxy servers to avoid getting blocked by LinkedIn.
- The script includes delays between requests to avoid rate limiting.
- Some job postings may not have company URLs available.

## Error Handling

The script includes robust error handling for:
- Network timeouts and connection issues
- HTML parsing errors
- Missing job information
- Rate limiting

## Customization

You can easily customize the scraper by modifying the configuration options or by extending the `LinkedInJobScraper` class with additional methods.