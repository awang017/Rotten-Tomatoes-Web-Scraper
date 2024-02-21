# Rotten Tomatoes Web Scraper

This Python module scrapes movie and TV show data from the Rotten Tomatoes website and updates a Google Sheet with the scraped information. The module extracts the show type (movie or TV), title, release year, genre, runtime, Tomatometer score, audience score, and release date.

## Dependencies

This module requires the following dependencies:

- **bs4 (BeautifulSoup):** A library for web scraping.
- **gspread:** Python API for Google Sheets.
- **logging:** Standard library for logging in Python.
- **oauth2client:** Library for OAuth 2.0 authentication.
- **requests:** Library for making HTTP requests.

## Author and Date

- **Author:** Andrew Wang
- **Date:** February 20, 2024

## Functions

- `check_date_format(value)`: Checks if the input value has the format '%b %d, %Y' and returns True if it does.
- `extract_movie_info(soup)`: Extracts movie information from the provided BeautifulSoup object.
- `extract_tv_info(soup, url)`: Extracts TV show information from the provided BeautifulSoup object and URL.
- `load_credentials()`: Loads and returns the Google Sheets API credentials.
- `get_google_sheet(sheet_name)`: Fetches and returns the Google Sheet object.
- `fetch_urls_from_sheet(sheet_name, column_number, start_row, end_row=None)`: Fetches URLs from a Google Sheets document.
- `scrape_rotten_tomatoes_and_update_sheet(url, sheet, row_number, header_row, *column_indices)`: Scrapes data from Rotten Tomatoes and updates a Google Sheet with the extracted information.
- `scrape_rotten_tomatoes_and_update_scores(url, sheet, row_number, header_row, *column_indices)`: Scrapes data from Rotten Tomatoes and updates a Google Sheet with only the extracted Tomatometer and audience score.
- `main()`: The main entry point. Sets up credentials, fetches the sheet, fetches URLs from the specified sheet, and iterates through the URLs to scrape Rotten Tomatoes data and update the provided Google Sheet with the results.
