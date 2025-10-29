# Basic LinkedIn Job Scraper

A lightweight Python script that extracts only the essential information from LinkedIn job listings:
- Job title
- Company name
- Company LinkedIn URL
- Job posting URL (for unique identification)
- Category and search title (for multi-category searches)

This scraper is optimized for speed by skipping the time-consuming step of fetching individual job description pages.

## Features

- Fast scraping by only parsing search results pages
- Configurable search parameters (keywords, location, job type)
- Support for multiple job categories with multiple titles per category
- Smart page skipping (stops after 2 consecutive pages with no jobs)
- Duplicate removal based on job URL (most reliable)
- Export to CSV and JSON formats
- Retry logic with exponential backoff
- Proxy support
- Automatic URL cleaning (removes tracking parameters)

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

- `categories`: Dictionary of job categories with arrays of job titles (see example config)
- `locations`: Array of job locations to search in (supports multiple countries)
- `job_type`: Job type filter (0=onsite, 1=hybrid, 2=remote, empty=any)
- `timespan`: Time filter (r84600 = 24 hours, r604800 = 1 week)
- `pages_to_scrape`: Number of pages to scrape (default: 5)
- `headers`: HTTP headers for requests
- `proxies`: Proxy configuration (optional)

### Multi-Country Support

The scraper now supports searching across multiple countries simultaneously:

```json
{
  "locations": [
    "United States",
    "Saudi Arabia",
    "United Arab Emirates",
    "Australia",
    "Canada",
    "Bahrain",
    "Qatar"
  ]
}
```

The scraper will search for all job titles in all specified locations, automatically removing duplicates across all countries and categories.

### Category Configuration

The scraper supports multiple job categories, each with multiple job titles:

```json
{
  "categories": {
    "devops": [
      "DevOps Engineer",
      "Platform Engineer",
      "Cloud Engineer",
      "Site Reliability Engineer",
      "AWS Cloud Engineer",
      "Azure Cloud Engineer",
      "GCP Cloud Engineer",
      "Cloud Infrastructure Engineer"
    ],
    "developer": [
      "Software Developer",
      "Python Developer",
      "Backend Engineer",
      "Full Stack Developer"
    ]
  }
}
```

The scraper will search for each title in each category, automatically removing duplicates across all categories.

## Output

The scraper generates two files:
- `basic_linkedin_jobs.csv`: CSV format with job information
- `basic_linkedin_jobs.json`: JSON format with job information

Each job entry contains:
- `title`: Job title
- `company`: Company name
- `company_url`: Clean LinkedIn URL for the company (tracking parameters removed)
- `job_url`: Direct URL to the job posting (unique identifier)
- `category`: Category name the job was found under
- `search_title`: Specific job title that was searched for
- `location`: Location where the job was found
- `scraped_at`: Timestamp when the job was scraped

## Example Output

```json
[
  {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "company_url": "https://www.linkedin.com/company/tech-corp",
    "job_url": "https://www.linkedin.com/jobs/view/123456789/",
    "category": "developer",
    "search_title": "Python Developer",
    "location": "United States",
    "scraped_at": "2023-11-15T14:30:22.123456"
  },
  {
    "title": "DevOps Engineer",
    "company": "CloudTech Inc",
    "company_url": "https://www.linkedin.com/company/cloudtech",
    "job_url": "https://www.linkedin.com/jobs/view/987654321/",
    "category": "devops",
    "search_title": "DevOps Engineer",
    "location": "Saudi Arabia",
    "scraped_at": "2023-11-15T14:30:22.123456"
  }
]
```

Note: The scraper automatically removes tracking parameters from company URLs, converting URLs like:
`https://www.linkedin.com/company/tech-corp?trk=public_jobs_jserp-result_job-search-card-subtitle`
to clean URLs like:
`https://www.linkedin.com/company/tech-corp`

## Performance

This scraper is significantly faster than full-featured scrapers because:
- It only makes requests to search results pages (not individual job pages)
- It extracts minimal information from each page
- It avoids processing large job description texts
- It intelligently skips pages when no jobs are found

Typical performance: 5 pages of results (125 jobs) in under 30 seconds.

### Smart Page Skipping

The scraper includes intelligent page skipping to improve efficiency:
- Stops searching for a specific job title after 2 consecutive pages with no results
- Prevents unnecessary requests for titles that have limited job postings
- Significantly reduces scraping time for niche job titles
- Example: If "GCP Cloud Engineer" returns no jobs for 2 consecutive pages, the scraper moves to the next title

## Notes

- LinkedIn may implement rate limiting. The scraper includes delays between requests.
- For large-scale scraping, consider rotating user agents and using proxies.
- The scraper targets specific HTML elements that may change if LinkedIn updates their layout.