import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd


def extract_startup_urls(url):
    # Request the content of the webpage
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
    html_content = response.text
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all the <a> tags with href attributes
    a_tags = soup.find_all('a', href=True)
    
    # Define a list of unwanted substrings
    unwanted_substrings = ['index.cfm', '#', '/events', '/search', '/programs', '/news', '/partners', '/about', '/businessdevelopment', '/fundraising', "/Datenschutz"]
    
    # Filter URLs that match the pattern "https://www.venturelab.swiss/<name>"
    startup_urls = []
    base_url = "https://www.venturelab.swiss"
    for a in a_tags:
        href = a['href']
        # Check if href starts with "/" and does not contain any unwanted substrings
        if href.startswith('/') and not any(unwanted in href for unwanted in unwanted_substrings):
            full_url = base_url + href
            if full_url not in startup_urls:  # Avoid duplicates
                startup_urls.append(full_url)
    
    return startup_urls

def extract_all_startup_urls(branch_urls_dict):
    result = {}
    lenList = len(branch_urls_dict)
    for i, (branch, urls) in enumerate(branch_urls_dict.items()):
        branch_startup_urls = []
        for url in urls:
            time.sleep(3)
            try:
                print(f"brancht {i}/{lenList}, url {url}", end="\r")
                startup_urls = extract_startup_urls(url)
                branch_startup_urls.extend(startup_urls)
            except Exception as err:
                continue
        # Remove duplicates
        branch_startup_urls = list(set(branch_startup_urls))
        result[branch] = branch_startup_urls
    return result


#====================================================================
def scrape_startup_info(startup_name):
    # Format the URL with the startup name
    url = f"https://www.venturelab.swiss/{startup_name}"
    
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the title
        h1_tags = soup.find_all('h1')
        title = None
        for h1 in h1_tags:
            if h1.text.strip() != "Venturelab":
                title = h1.text.strip()
                break
        if not title:
            title = None
        
        # Extract the subtitle or tagline
        subtitle = soup.find('h3').text if soup.find('h3') else None
        
        # Extract the description from the p tag
        description = soup.find('div', class_='vl-startup-details-main').find('p').text.strip() if soup.find('div', class_='vl-startup-details-main') and soup.find('div', class_='vl-startup-details-main').find('p') else None
        
        # Extract the incorporation date
        try:
            incorporation_div = soup.find('div', text='Incorporated:').find_next_sibling('div')
        except Exception as err:
            incorporation_div = soup.find('span', text='Incorporated:').find_next_sibling('div')

        incorporation = incorporation_div.text.strip() if incorporation_div else None
        
        # Extract the headquarters location
        try:
            headquarters_div = soup.find('div', text='Headquarter:').find_next_sibling('div')
        except Exception as err:
            headquarters_div = soup.find('span', text='Headquarter:').find_next_sibling('div')

        headquarters = headquarters_div.text.strip() if headquarters_div else None
        
        # Extract the sectors
        sectors_div = soup.find('div', class_='vl-tags')
        sectors = [a.text for a in sectors_div.find_all('a')] if sectors_div else None
        
        # Extract the social links and homepage
        social_links = {}
        social_section = soup.find('ul', class_='vl-news-social')
        if social_section:
            for li in social_section.find_all('li'):
                link_class = li.get('class', [''])[0]
                social_links[link_class] = li.find('a').get('href', '')
        
        # Extract the awards
        awards_section = soup.find('div', class_='vl-startup-sidebar-section-links')
        awards = [a.text for a in awards_section.find_all('a')] if awards_section else None
        
        # Return the extracted information as a dictionary
        return {
            'title': title,
            'subtitle': subtitle,
            'description': description,
            'incorporation': incorporation,
            'headquarters': headquarters,
            'sectors': sectors,
            'social_links': social_links,
            'awards': awards
        }
    else:
        print("nothing found")
        # Return an error message if the request was not successful


def scrape_and_store_info(json_path, sleep=3, outPath = None):
    # Read the JSON file
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    # Prepare a list to hold the rows of the DataFrame
    rows = []
    lenUrls = len(data)
    
    # Iterate through the JSON data
    for i, url in enumerate(data):
        print(f"{i}/{lenUrls}", end="\r")
        # Extract the startup name from the URL
        startup_name = url.split('/')[-1]
        
        # Scrape the startup info
        try:
            time.sleep(sleep)
            startup_info = scrape_startup_info(startup_name)
            # Add the branche to the startup info
            startup_info['url'] = url
            # Append the startup info to the rows list
            rows.append(startup_info)
        except Exception as e:
            print(f"Error scraping {startup_name}: {e}")
    
    # Create a DataFrame from the rows
    df = pd.DataFrame(rows)

    for column in df.columns:
        df[column] = df[column].apply(lambda x: str(x).replace('”', '"').replace('“', '"'))    
    
    # Reorder the columns
    df = df[['title', 'subtitle', 'description', 'incorporation', 'headquarters', 'sectors', 'social_links', 'awards', 'url']]

    if outPath:
        df.to_csv(outPath, index=False, encoding='utf-8')  
    
    return df


if __name__ == "__main__":
# Example usage
    branch_urls_dict = {
        "ICT": [
            "https://www.venturelab.swiss/index.cfm?cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&cfid=199651693&page=137241&form_done=8812#fgFormAnker_8812",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=43&bericht_seite_9735=3&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=64&bericht_seite_9735=4&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=85&bericht_seite_9735=5&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=106&bericht_seite_9735=6&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=127&bericht_seite_9735=7&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=148&bericht_seite_9735=8&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=169&bericht_seite_9735=9&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=190&bericht_seite_9735=10&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=211&bericht_seite_9735=11&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=232&bericht_seite_9735=12&page=137241#fgBerichtAnker_9735"
                ],
        "Biotech": [
            "https://www.venturelab.swiss/index.cfm?cfid=199622093&cftoken=6b0355ba1781bbbe-AEC2C618-C6A3-1F7E-13A979E2BC69DC59&bericht_id=9735&start_liste_9735=1&bericht_seite_9735=1&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199667678&cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735"
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=43&bericht_seite_9735=3&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=64&bericht_seite_9735=4&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=85&bericht_seite_9735=5&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=106&bericht_seite_9735=6&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=127&bericht_seite_9735=7&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=148&bericht_seite_9735=8&page=137241#fgBerichtAnker_9735"
        ],
        "Medtech": [
            "https://www.venturelab.swiss/index.cfm?cfid=199667678&cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&bericht_id=9735&start_liste_9735=1&bericht_seite_9735=1&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=43&bericht_seite_9735=3&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=64&bericht_seite_9735=4&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=85&bericht_seite_9735=5&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=106&bericht_seite_9735=6&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=127&bericht_seite_9735=7&page=137241#fgBerichtAnker_9735"
        ],
        "Cleantech": [
            "https://www.venturelab.swiss/index.cfm?cfid=199667678&cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&bericht_id=9735&start_liste_9735=1&bericht_seite_9735=1&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=43&bericht_seite_9735=3&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=64&bericht_seite_9735=4&page=137241#fgBerichtAnker_9735"
        ],
        "Engineering": [
            "https://www.venturelab.swiss/index.cfm?cfid=199667678&cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&bericht_id=9735&start_liste_9735=1&bericht_seite_9735=1&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=43&bericht_seite_9735=3&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=64&bericht_seite_9735=4&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=85&bericht_seite_9735=5&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=106&bericht_seite_9735=6&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=127&bericht_seite_9735=7&page=137241#fgBerichtAnker_9735"
        ],
        "Fintech": [
            "https://www.venturelab.swiss/index.cfm?cfid=199667678&cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&bericht_id=9735&start_liste_9735=1&bericht_seite_9735=1&page=137241#fgBerichtAnker_9735",
            "https://www.venturelab.swiss/index.cfm?cfid=199651693&cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&bericht_id=9735&start_liste_9735=22&bericht_seite_9735=2&page=137241#fgBerichtAnker_9735"
        ],
        "Foodtech":[
            "https://www.venturelab.swiss/index.cfm?cftoken=e161932a6c5dff40-B4C444A7-9E17-D3AD-CE9BE94FC0E465CD&cfid=199667678&page=137241&form_done=8812#fgFormAnker_8812"
        ],
        "Proptech":[
            "https://www.venturelab.swiss/index.cfm?cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&cfid=199651693&page=137241"
        ],
        "Robotics":[
            "https://www.venturelab.swiss/index.cfm?cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&cfid=199651693&page=137241"
        ],
        "Security":[
            "https://www.venturelab.swiss/index.cfm?cftoken=4453ea12a82bc0b-B2D364D8-A77B-0FBE-64297B39D3DE7422&cfid=199651693&page=137241"
        ]
        # Add more branches and URLs as needed
    }


    startup_urls_by_branch_all = extract_all_startup_urls(branch_urls_dict)

    with open("ventureLab_all.json", "w+") as file:
        json.dump(startup_urls_by_branch_all, file)

    json_path = r'C:\Users\kevin\OneDrive - TrueYouOmics\PERSONAL\_GITHUB\runwayRAG\App\data\ventureLab_all.json'
    with open(json_path, 'r') as file:
        data = json.load(file)

    li = []
    for key, items in data.items():
        for i in items:
            li.append(i)

    finalUrlList = list(set(li))        
    with open("ventureLab_allUrl.json", "w+") as file:
        json.dump(finalUrlList, file)



    #======================
    # Get information
    #======================

    json_path = r'C:\Users\kevin\OneDrive - TrueYouOmics\PERSONAL\_GITHUB\runwayRAG\App\data\ventureLab_allUrl.json'
    #json_path = r'C:\Users\kevin\OneDrive - TrueYouOmics\PERSONAL\_GITHUB\runwayRAG\App\data\test.json'
    df = scrape_and_store_info(json_path, sleep=3, outPath = "ventureLabStartupInfo_clean.csv")

