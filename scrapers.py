import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor
from cat import Cat
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def scrape_aspca_cat_detail(id):
    """
        Given the id of a cat, scrape all details for that cat and return
        the details.
    """

    if id is None:
        print("Meow! This cat doesn't have an ID.")
        return

    url = "https://toolkit.rescuegroups.org/j/3/pet1_layout.php?toolkitIndex"\
          "=0&toolkitKey=6REv6Spa&petfocus_0=562&page_0=1&breed_0=&sex_0=&dis"\
          "tance_0=25&location_0=10023&petIndex=2&animalID={id}"
    page = requests.get(url.format(id=id))
    soup = BeautifulSoup(page.text, 'html.parser')

    cat = Cat()
    cat.static_url = url.format(id=id)
    cat.pet_name = soup.find(id="rgtkPetTitleName_0").text\
        if soup.find(id="rgtkPetTitleName_0") else None
    cat.breed = soup.find(id="rgtkPetDetailsBreed_0").text\
        if soup.find(id="rgtkPetDetailsBreed_0") else None
    cat.pet_size = soup.find(id="rgtkPetDetailsGeneralSizePotential_0").text\
        if soup.find(id="rgtkPetDetailsGeneralSizePotential_0") else None
    cat.age = soup.find(id="rgtkPetDetailsAge_0").text\
        if soup.find(id="rgtkPetDetailsAge_0") else None
    cat.sex = soup.find(id="rgtkPetDetailsSex_0").text\
        if soup.find(id="rgtkPetDetailsSex_0") else None
    cat.image = soup.find(id="rgtkPetPicturePrimaryImg_0")["src"]\
        if soup.find(id="rgtkPetPicturePrimaryImg_0") else None
    cat.description = soup.find("div", {"class": "rgDescription"}).text\
        if soup.find("div", {"class": "rgDescription"}) else None
    cat.adoption_status = soup.find(id="rgtkPetFieldStatus_0").text\
        if soup.find(id="rgtkPetFieldStatus_0") else None
    cat.adoption_center["name"] = soup.find(id="gtkPetFieldOrgName_0").text\
        if soup.find(id="gtkPetFieldOrgName_0") else None
    cat.adoption_center["contact_info"] = soup.find(
        id="rgtkPetFieldOrgEmail_0").find("a").text\
        if soup.find(id="rgtkPetFieldOrgEmail_0") else None

    if soup.find(id="rgtkPetFieldOrgCitystatezip_0"):
        if len(soup.find(id="rgtkPetFieldOrgCitystatezip_0").text
               .split(", ")) > 0:
            cat.adoption_center["city"] = soup.find(
                id="rgtkPetFieldOrgCitystatezip_0").text.split(", ")[0]
        if len(soup.find(id="rgtkPetFieldOrgCitystatezip_0").text
               .split(", ")) > 1 and\
           len(soup.find(id="rgtkPetFieldOrgCitystatezip_0").text
               .split(", ")[1].split(" ")) > 1:
            cat.adoption_center["state"] = soup.find(
                id="rgtkPetFieldOrgCitystatezip_0").text.split(", ")[1]\
                .split(" ")[0]
            cat.adoption_center["zip"] = soup.find(
                id="rgtkPetFieldOrgCitystatezip_0").text.split(", ")[1]\
                .split(" ")[1]

    if soup.find(id="rgtkPetInfoIndented_0"):
        qualities = [qual.text for qual in soup.find(
            id="rgtkPetInfoIndented_0").find_all("li")]

        if any("Color: " in q for q in qualities):
            cat.color = [q for q in qualities if "Color: " in q][0]\
                .split(": ")[1]

        if "Good with cats" in qualities:
            cat.is_good_with_cats = True
        elif "Not good with cats" in qualities:
            cat.is_good_with_cats = False

        if "Good with dogs" in qualities:
            cat.is_good_with_dogs = True
        elif "Not good with dog" in qualities:
            cat.is_good_with_dogs = False

        if "Good with kids" in qualities:
            cat.is_good_with_kids = True
        elif "Not good with children" in qualities:
            cat.is_good_with_kids = False

        if "Declawed" in qualities:
            cat.is_declawed = True
        if "House trained" in qualities:
            cat.is_house_trained = True
        if "Up-to-date with vaccinations" in qualities:
            cat.has_shots = True
        if "Spayed" in qualities and "Neutered" in qualities:
            cat.is_spayed_neutered = True

    return cat


def scrape_aspca(zip_code):
    """
        Find all cats within 25 miles of the zip code.
        Returns a list of Cats.
    """

    print("Scraping ASPCA...")

    ids = []
    page_num = 1
    url = "https://toolkit.rescuegroups.org/j/3/grid1_layout.php?toolkitIndex"\
          "=0&toolkitKey=6REv6Spa&petfocus_0=&page_0={page}&breed_0=&sex_0="\
          "&distance_0=25&location_0={zip_code}"

    while True:
        page = requests.get(url.format(page=page_num, zip_code=zip_code))
        soup = BeautifulSoup(page.text, 'html.parser')

        if soup.find("div", {"class": "rgtkSearchNoResults"}):
            break

        for entry in soup.find_all("td", {"class": "rgtkSearchResultsCell"}):
            click_script = entry.find_all("a")[0]["onclick"]
            cat_id = (click_script.split(", ")[1]
                      if len(click_script.split(", ")) > 0
                      else None)
            if cat_id:
                ids.append(cat_id)

        page_num += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(scrape_aspca_cat_detail, ids)

    cats = []
    for value in results:
        cats.append(value)

    print("Found {} cats on ASPCA.".format(len(cats)))
    return cats


def scrape_one_petfinder_page(page, zip_code):
    """
        Returns a JSON object from one paginated call to the Petfinder API.
    """

    url = "https://www.petfinder.com/search/?page={page}&limit[]=100&"\
          "status=adoptable&token=Pm0Y0EZu2rnQl1TIg7kVRPsUFoFt6CPlOD8Age"\
          "W11cw&distance[]=25&type[]=cats&sort[]=nearest&location_slug"\
          "[]=us%2Fny%2F{zip_code}".format(page=page, zip_code=zip_code)
    # TODO: this is hard-coded for NY state

    headers = {
        "x-requested-with": "XMLHttpRequest",
        "Referer": "https://www.petfinder.com/search/cats-for-adoption/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1)"
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
                      "71.0.3578.98 Safari/537.36"
    }

    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        print("Meow! Could not get data from Petfinder (status code {})."
              .format(page.status_code))
        return

    return page.json()


def scrape_petfinder(zip_code):
    """
        Scrapes the cat listings on Petfinder.com within 25 miles of a given
        zip code.
        Returns a list of Cat objects.
    """
    print("Scraping Petfinder...")
    data = scrape_one_petfinder_page(page=1, zip_code=zip_code)
    if data is None:
        return

    cats = []
    total_pages = data["result"]["pagination"]["total_pages"]
    for i in range(total_pages):
        if i > 0:
            # We already have the data for the first page, so only need to get
            # new data when the page is > 1.
            data = scrape_one_petfinder_page(page=i + 1, zip_code=zip_code)

        for entry in data["result"]["animals"]:
            cat = Cat()
            animal_data = entry.get("animal")
            if animal_data:
                cat.image = animal_data.get("primary_photo_url")
                cat.pet_name = animal_data.get("name")
                cat.description = animal_data.get("description")
                cat.static_url = (animal_data.get("social_sharing")
                                  .get("email_url")
                                  if animal_data.get("social_sharing")
                                  else None)
                cat.breed = animal_data.get("breeds_label")
                cat.pet_size = animal_data.get("size")
                cat.color = animal_data.get("primary_color")
                cat.age = animal_data.get("age")
                cat.sex = animal_data.get("sex")
                cat.adoption_status = entry["animal"]["adoption_status"]
            location = entry.get("location")
            if location:
                cat.adoption_center["address"] = (location["address"]
                                                  .get("address1")
                                                  if location.get("address")
                                                  else None)
                cat.adoption_center["city"] = location.get("city")
                cat.adoption_center["state"] = location.get("state")
                cat.adoption_center["zip"] = location.get("postal_code")
            cat.adoption_center["name"] = (entry["organization"].get("name")
                                           if entry.get("organization")
                                           else None)

            contact = entry["contact"][0] if isinstance(
                entry["contact"], list) and len(entry["contact"]) > 0\
                else entry["contact"]
            cat.adoption_center["contact_info"] = contact.get("email")\
                if isinstance(contact, dict) else None
            cats.append(cat)
    print("Found {} cats on Petfinder.".format(len(cats)))
    return cats


def scrape_adoptapet_cat_detail(cat):
    """
        Given an AdoptAPet.com cat ID, scrape the details for that cat
        and update its Cat object.
    """

    url = cat.static_url
    if url is None:
        print("Meow! Cat {} doesn't have a static URL.".format(cat.pet_name))
        return

    page = requests.get(url)
    if page.status_code != 200:
        print("Meow! Could not access details for cat {} "
              "(status code {} for {}).".format(cat.pet_name, page.status_code,
                                                url))
        return
    soup = BeautifulSoup(page.text, 'html.parser')

    # Find the script tag on the details page that contains more data
    # on the cat in JSON format
    scripts = [script.text for script in soup.body.find_all("script")
               if "petDetailData.petDetail" in script.text]
    if len(scripts) == 0:
        print("Meow! Could not load details for cat {}.".format(cat.pet_name))
        return

    regex = r"petDetailData\.petDetail \=(.+)\;"
    data = json.loads(re.search(regex, scripts[0]).group(1))

    cat.color = data.get("colorName")
    cat.breed = data.get("primaryBreedName")
    cat.adoption_status = data.get("status")
    cat.is_declawed = data.get("declawed")
    cat.is_good_with_birds = data.get("goodWithBirds")
    cat.is_good_with_cats = data.get("goodWithCats")
    cat.is_good_with_dogs = data.get("goodWithDogs")
    cat.is_good_with_kids = data.get("goodWithKids")
    cat.is_good_with_small_animals = data.get("goodWithSmallAnimals")
    cat.is_house_trained = data.get("houseTrained")
    cat.is_microchipped = data.get("microchipped")
    cat.has_shots = data.get("shots")
    cat.is_spayed_neutered = data.get("spayedNeutered")

    if data.get("description"):
        # TODO: This is in HTML, may need additional parsing
        # (could use BeautifulSoup .text)
        cat.description = unquote(data.get("description"))

    if data.get("shelter"):
        shelter = data.get("shelter")
        cat.adoption_center["name"] = shelter.get("name")
        cat.adoption_center["contact_info"] = shelter.get("email")
        cat.adoption_center["address"] = shelter.get("address1")
        if shelter.get("address1") and shelter.get("address2"):
            cat.adoption_center["address"] += ", " + shelter.get("address2")
        cat.adoption_center["city"] = shelter.get("city")
        cat.adoption_center["state"] = shelter.get("state")
        cat.adoption_center["zip"] = shelter.get("postalCode")


def scrape_adoptapet(zip_code):
    """
        Scrape AdoptAPet.com for cats within 25 miles of a given zipcode.
        Returns a list of cat objects.
    """

    print("Scraping AdoptAPet...")

    base_url = "https://ra-api.adoptapet.com/v1/pet-search/location/"\
               "{zip_code}/georange/25/clan/2/?start={start}&limit=100"

    cats = []

    # The API's max allowed `start` value is 481 and max `limit` is 100, hence
    # this list of starting indices
    for start_idx in [1, 101, 201, 301, 401, 481]:
        page = requests.get(base_url.format(zip_code=zip_code,
                                            start=start_idx))
        data = page.json()
        if (not data.get('body') or not data['body'].get('pets')
                or not isinstance(data['body']['pets'], list)):
            print("Meow! Error in getting data fmor the adoptapet API.")
            return

        for entry in data["body"]["pets"]:
            cat = Cat()
            cat.age = entry.get("age")
            cat.pet_name = entry.get("petName")
            cat.sex = entry.get("sex")
            cat.image = entry.get("image")
            cat.hair_length = entry.get("hairLength")
            cat.pet_size = entry.get("size")
            cat.breed = entry.get("primaryFamilyName")
            if entry.get("detailsUrl"):
                cat.static_url = "https://adoptapet.com"\
                                 + entry.get("detailsUrl")
            cats.append(cat)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(scrape_adoptapet_cat_detail, cats)

    print("Found {} cats on AdoptAPet.".format(len(cats)))
    return cats


def scrape_one_petango_page(zip_code, token, page_num):
    """
        Returns a list of Cat objects from one Petango search results page.
    """
    url = "https://www.petango.com/DesktopModules/Pethealth.Petango/Pethealth"\
          ".Petango.DnnModules.AnimalSearchResult/API/Main/Search"
    data = {
        "location": zip_code,
        "distance": "25",
        "speciesId": "2",
        "goodWithDogs": False,
        "goodWithCats": False,
        "goodWithChildren": False,
        "mustHavePhoto": False,
        "mustHaveVideo": False,
        "happyTails": False,
        "lostAnimals": False,
        "moduleId": 843,
        "recordOffset": (page_num - 1) * 50,
        "recordAmount": 50
    }

    headers = {
        "Host": "www.petango.com",
        "Connection": "keep-alive",
        "Content-Length": "252",
        "TabId": "260",
        "RequestVerificationToken": token,
        "Origin": "https://www.petango.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) Apple "
                      "WebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 "
                      "Safari/537.36",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "ModuleId": "843",
        "Referer": "https://www.petango.com/pet_search_results?speciesId=2&"
                   "breedId=undefined&location=10019&distance=50",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8"
    }
    page = requests.post(url, json=data, headers=headers, verify=False)

    if page.status_code != 200:
        print("Meow! Could not page {} from Petango.".format(page_num))

    data = page.json()
    cats = []
    for entry in data.get("items"):
        cat = Cat()
        cat.pet_name = entry.get("name")
        cat.image = entry.get("photo")
        cat.age = entry.get("age")
        cat.sex = entry.get("gender")
        cat.breed = entry.get("breed")
        cat.is_good_with_dogs = not entry.get("noDogs")\
            if entry.get("noDogs") is not None else None
        cat.is_good_with_cats = not entry.get("noCats")\
            if entry.get("noCats") is not None else None
        cat.is_good_with_kids = not entry.get("noKids")\
            if entry.get("noKids") is not None else None
        cat.static_url = entry.get("url")
        cats.append(cat)
    return cats


def crawl_petango_search_results(zip_code):
    """
        Iterate through all Petango search result pages to collect cat info.
        Returns a list of Cat objects.
    """
    token = retrieve_petango_token()
    if token is None:
        print("Meow! Could not get auth token for Petango.")
        return

    cats = []
    page_num = 1
    while True:
        new_cats = scrape_one_petango_page(zip_code, token, page_num=page_num)
        if len(new_cats) == 0:
            # If this is beyond the last page of results
            break
        cats.extend(new_cats)
        page_num += 1

    return cats


def retrieve_petango_token():
    """
        Get a request API token from the Petango homepage.
        Returns the token as a string.
    """
    url = "https://www.petango.com/"
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup.find("input",
                     {"name": "__RequestVerificationToken"}).get("value")


def scrape_petango_cat_detail(cat):
    """
        Scrape additional cat details for a given cat.
        Updates the Cat object for this cat.
        Returns None.
    """

    if cat.static_url is None:
        print("Meow! This cat has no Petango static url.")
        return

    token = retrieve_petango_token()
    id = cat.static_url.split("-")[-1]

    headers = {
        'TabId': '261',
        'RequestVerificationToken': token,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578"
                      ".98 Safari/537.36",
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': cat.static_url,
        'X-Requested-With': 'XMLHttpRequest',
        'ModuleId': '849',
        'Connection': 'keep-alive',
    }

    params = (
        ('moduleId', '849'),
        ('animalId', id),
        ('clientZip', 'null'),
    )

    url = "https://www.petango.com/DesktopModules/Pethealth.Petango/Pethealth"\
          ".Petango.DnnModules.AnimalDetails/API/Main/GetAnimalDetails"
    page = requests.get(url, headers=headers, params=params, verify=False)

    data = page.json()

    cat.is_declawed = data.get("declawed")
    cat.details = data.get("memo")
    cat.pet_size = data.get("size")
    cat.is_spayed_neutered = data.get("spayedNeutered")
    cat.adoption_center["name"] = data.get("shelterName")
    if (data.get("shelterCityState") and
            len(data.get("shelterCityState").split(", ")) > 0):
        cat.adoption_center["city"] = data.get("shelterCityState")\
            .split(", ")[0]
        cat.adoption_center["state"] = data.get("shelterCityState")\
            .split(", ")[1]


def scrape_petango(zip_code):
    """
        Scrapes Petango for cats within 25 miles of a given zip code.
        Returns a list of Cats.
    """
    print("Scraping Petango...")

    cats = crawl_petango_search_results(zip_code)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(scrape_petango_cat_detail, cats)

    print("Found {} cats on Petango.".format(len(cats)))
    return cats


def scrape_all_sites(zip_code):
    """
        Scrapes all four cat adoption websites for cats located near a given
        zip code. This is the main scraper function to call.

        Returns a list of Cat objects.
    """

    print("Scraping all sites for cats near {}.".format(zip_code))
    cats = []
    cats.extend(scrape_aspca(zip_code))
    cats.extend(scrape_adoptapet(zip_code))
    cats.extend(scrape_petfinder(zip_code))
    cats.extend(scrape_petango(zip_code))

    print("Done scraping.")
    print("Found {} total cats.".format(len(cats)))
    return cats
