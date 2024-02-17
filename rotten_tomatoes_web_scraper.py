"""
Module for scraping Rotten Tomatoes website for movie and TV show data and updating
a Google Sheet with the scraped information.

Dependencies:
    - bs4 (BeautifulSoup): Library for web scraping.
    - gspread: Python API for Google Sheets.
    - logging: Standard library for logging in Python.
    - oauth2client: Library for OAuth 2.0 authentication.
    - requests: Library for making HTTP requests.

Author: Andrew Wang
Date:   February 16, 2024
"""

from datetime import datetime
import logging
import re
import bs4
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# Configure logging
logging.basicConfig(
    filename='RT_web_scraper.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def check_date_format(value):
    """
    Check if the input value has the format '%b %d, %Y' and return True if it does,
    otherwise return False.

    Parameters:
    value (str): The input value to be checked for date format.

    Returns:
    bool: True if the input value has the correct date format, False otherwise.
    """
    try:
        datetime.strptime(value, '%b %d, %Y')
        return True
    except ValueError:
        return False


def extract_movie_info(soup):
    """
    Extracts movie information from the provided BeautifulSoup object.

    Parameters:
    - soup: BeautifulSoup object containing the movie information HTML.

    Returns:
    - title:          str, the title of the movie.
    - 'Movie':        str, a string indicating that the result is a movie.
    - year:           str, the release year of the movie.
    - genre:          str, the genre(s) of the movie.
    - runtime:        str, the duration of the movie.
    - tomatometer:    float, the tomatometer score of the movie as a percentage.
    - audience_score: float, the audience score of the movie as a percentage.
    - release_date:   str, the release date of the movie in the format mm/dd/yy.
    """
    title_html = soup.find('h1', class_='title')
    title = title_html.get_text(strip=True) if title_html else 'not found'

    info_html = soup.find('p', class_='info')
    info_text = info_html.get_text(strip=True)
    info_text_parts = info_text.split(',')

    year = info_text_parts[0].strip() if len(info_text_parts) > 0 else 'not found'
    runtime = info_text_parts[2].strip() if len(info_text_parts) > 2 else 'not found'

    genre_html = soup.find('span', class_='genre')
    genre = ', '.join([genre.strip() for genre in genre_html.get_text(strip=True).split(',')]) if genre_html else 'not found'

    score_board = soup.find('score-board-deprecated')
    tomatometer = float(score_board.get('tomatometerscore', 'not found')) / 100 if score_board and score_board.get('tomatometerscore') not in ('not found', '') else 'not found'
    audience_score = float(score_board.get('audiencescore', 'not found')) / 100 if score_board and score_board.get('audiencescore') not in ('not found', '') else 'not found'

    release_date_html = soup.find('time')
    release_date = release_date_html.get_text(strip=True) if release_date_html else 'not found'
    release_date = datetime.strptime(release_date, '%b %d, %Y').strftime('%m/%d/%y') if check_date_format(release_date) else 'not found'

    return title, 'Movie', year, genre, runtime, tomatometer, audience_score, release_date


def extract_tv_info(soup, url):
    """
    Extracts TV show information from the provided BeautifulSoup object and URL.

    Parameters:
    - soup: BeautifulSoup object containing the TV show information HTML.
    - url: str, the URL of the TV show.

    Returns:
    - title:          str, the title of the TV show.
    - 'TV':           str, a string indicating that the result is a TV show.
    - year:           str, the release year of the TV show.
    - genre:          str, the genre(s) of the TV show.
    - 'N/A':          str, a placeholder for the runtime as Rotten Tomatoes does not provide runtime data for TV shows.
    - tomatometer:    float, the tomatometer score of the TV show as a percentage.
    - audience_score: float, the audience score of the TV show as a percentage.
    - release_date:   str, the release date of the TV show in the format mm/dd/yy.
    """
    series_url = re.search(r'(https://www\.rottentomatoes\.com/tv/[^/]+)/?', url).group(1)
    series_response = requests.get(series_url, timeout=30)
    series_soup = BeautifulSoup(series_response.text, 'lxml')
    series_year_html = series_soup.find('rt-text', attrs={"slot": "releaseDate"})
    series_year = series_year_html.get_text() if series_year_html else 'not found'

    title_season_html = soup.find('h1')
    title_season_text = title_season_html.get_text() if title_season_html else ''
    title_season_match = re.search(r'Season (\d+) – (.+)', title_season_text)
    season = f'Season {title_season_match.group(1)}' if title_season_match else 'not found'
    title = title_season_match.group(2) if title_season_match else 'not found'
    title = f'{title.strip()} ({season})' if title and season else 'not found'

    genre_html = soup.find_all('rt-link')
    genres = [link.get_text() for link in genre_html if link and 'genres:' in link.get('href', '')]
    genre = ', '.join(genres)

    tomatometer_html = soup.find('rt-text', attrs={"slot": "criticsScore"})
    tomatometer_text = tomatometer_html.get_text(strip=True) if tomatometer_html else ''
    tomatometer = float(tomatometer_text.strip('%')) / 100 if tomatometer_text else 'not found'

    audience_score_html = soup.find('rt-text', attrs={"slot": "audienceScore"})
    audience_score_text = audience_score_html.get_text(strip=True) if audience_score_html else ''
    audience_score = float(audience_score_text.strip('%')) / 100 if audience_score_text else 'not found'

    release_date_html = soup.find('rt-text', attrs={"slot": "airDate"})
    release_date_text = release_date_html.get_text(strip=True) if release_date_html else ''
    release_date_unformatted = release_date_text.replace('Aired', '').strip() if release_date_text else 'not found'
    if release_date_unformatted != 'not found':
        release_date_datetime = datetime.strptime(release_date_unformatted, '%b %d, %Y')
        release_date = release_date_datetime.strftime('%m/%d/%y') if check_date_format(release_date_unformatted) else 'not found'
        year = f'{release_date_datetime.year} ({series_year})' if series_year else 'not found'

    return title, 'TV', year, genre, 'N/A', tomatometer, audience_score, release_date


def load_credentials():
    """
    Loads and returns the Google Sheets API credentials.

    Returns:
        oauth2client.service_account.ServiceAccountCredentials: The loaded credentials.
    """
    credentials_file = 'Rotten-Tomatoes-Web-Scraper/gas-ias-sync-81a804e8a23a.json'
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    try:
        return ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    except FileNotFoundError as e:
        logging.error("Credentials file not found: %s", e, exc_info=True)
        raise
    except Exception as e:
        logging.error("Unexpected error loading credentials: %s", e, exc_info=True)
        raise


def get_google_sheet(sheet_name):
    """
    Fetches and returns the Google Sheet object.

    Args:
        sheet_name (str): The name of the Google Sheets document.

    Returns:
        gspread.models.Worksheet: The Google Sheet object.
    """
    credentials = load_credentials()

    try:
        client = gspread.authorize(credentials)
        return client.open(sheet_name).worksheet('Show List')
    except gspread.exceptions.APIError as e:
        logging.error("Error accessing Google Sheets API: %s", e, exc_info=True)
        raise
    except Exception as e:
        logging.error("Unexpected error: %s", e, exc_info=True)
        raise


def fetch_urls_from_sheet(sheet_name, column_number, start_row, end_row=None):
    """
    Fetches URLs from a Google Sheets document.

    Args:
        sheet_name (str):        The name of the Google Sheets document.
        column_number (int):     The column number from which to fetch the URLs.
        start_row (int):         The starting row index from which to fetch the URLs.
        end_row (int, optional): The ending row index from which to fetch the URLs. If not provided, all rows from the start_row are fetched.

    Returns:
        list: A list of URLs fetched from the specified Google Sheets document.
    """
    try:
        sheet = get_google_sheet(sheet_name)
        rows = sheet.col_values(column_number)[start_row - 1:end_row]
        urls = [url for url in rows if url]
        return urls
    except gspread.exceptions.APIError as e:
        logging.error("Error accessing Google Sheets API: %s", e, exc_info=True)
        raise
    except Exception as e:
        logging.error("Unexpected error: %s", e, exc_info=True)
        raise

def scrape_rotten_tomatoes_and_update_sheet(url, sheet, row_number, header_row, *column_indices):
    """
    A function to scrape data from Rotten Tomatoes and update a Google Sheet with the
    extracted information.

    Args:
        url (str):                  The URL of the Rotten Tomatoes page to scrape.
        sheet (GoogleSheet):        The Google Sheet to update with the extracted information.
        row_number (int):           The row number in the Google Sheet to update.
        header_row (list):          The header row of the Google Sheet.
        title_index (int):          The index of the title column in the Google Sheet.
        type_index (int):           The index of the type column in the Google Sheet.
        year_index (int):           The index of the year column in the Google Sheet.
        genre_index (int):          The index of the genre column in the Google Sheet.
        runtime_index (int):        The index of the runtime column in the Google Sheet.
        tomatometer_index (int):    The index of the tomatometer column in the Google Sheet.
        audience_score_index (int): The index of the audience score column in the Google Sheet.
        release_date_index (int):   The index of the release date column in the Google Sheet.
    """
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'lxml')

        show_type = soup.find('meta', {'property': 'og:type'})['content']
        if 'movie' in show_type:
            title, show_type, year, genre, runtime, tomatometer, audience_score, release_date = extract_movie_info(soup)
        elif 'tv_show' in show_type:
            title, show_type, year, genre, runtime, tomatometer, audience_score, release_date = extract_tv_info(soup, url)
        else:
            logging.warning("Show type not recognized for URL: %s", url)
            return

        data = {header_row[i - 1]: None for i in column_indices}
        data['Title'] = title
        data['Movie or TV'] = show_type
        data['Year'] = year
        data['Genre'] = genre
        data['Runtime'] = runtime
        data['Tomatometer'] = tomatometer
        data['Audience Score'] = audience_score
        data['Release Date'] = release_date

        update_range = f"B{row_number}:{chr(65 + len(header_row))}{row_number}"

        sheet.update(range_name=update_range, values=[list(data.values())])

    except requests.exceptions.RequestException as e:
        logging.error("Error making request for %s: %s", url, e, exc_info=True)
    except bs4.FeatureNotFound as e:
        logging.error("Error parsing HTML for %s: %s", url, e, exc_info=True)
    except Exception as e:
        logging.error("Unexpected error scraping %s: %s", url, e, exc_info=True)


def main():
    """
    This function is the main entry point. It sets up the necessary credentials,
    fetches the sheet, fetches URLs from the specified sheet, and then iterates
    through the URLs to scrape Rotten Tomatoes data and update the provided Google
    Sheet with the results.
    """
    sheet_name = 'Movies & TV'
    column_number = 17
    start_row = 448
    end_row = None
    sheet = get_google_sheet(sheet_name)

    urls = fetch_urls_from_sheet(sheet_name, column_number, start_row, end_row)

    header_row = sheet.row_values(1)
    title_index = header_row.index('Title') + 1
    type_index = header_row.index('Movie or TV') + 1
    year_index = header_row.index('Year') + 1
    genre_index = header_row.index('Genre') + 1
    runtime_index = header_row.index('Runtime') + 1
    tomatometer_index = header_row.index('Tomatometer') + 1
    audience_score_index = header_row.index('Audience Score') + 1
    release_date_index = header_row.index('Release Date') + 1

    for row_number, url in enumerate(urls, start=start_row):
        print(url)
        scrape_rotten_tomatoes_and_update_sheet(url, sheet, row_number, header_row, title_index, type_index, year_index, genre_index, runtime_index, tomatometer_index, audience_score_index, release_date_index)


if __name__ == "__main__":
    main()
