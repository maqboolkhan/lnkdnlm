import re
import time

import httpx
from bs4 import BeautifulSoup as bs
from markdownify import markdownify as md


def fetch_linkedin_page_jobs(job_title, location, time_option, page):
    start = "0" if page == 1 else f"{page-1}{page-1}"
    duration = {
        "Past week": "r604800",
        "Past month": "r2592000",
        "Past 24 hours": "r86400"
    }

    # &f_E={level}
    EXP_Internship = 1
    EXP_Entry = 2
    EXP_level = 3
    EXP_Associate = 4
    EXP_Mid_Senior = 5
    EXP_level = 6
    EXP_Director = 7

    # f_WT={}
    COND_ON_SITE = 1
    COND_HYBRID = 2
    COND_REMOTE = 3

    URL_JOBS = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={title}&location={location}&f_TPR={time_posted}"

    job_title = re.sub(r'\s', '+', job_title)
    query_url = URL_JOBS.replace("{title}", job_title).replace("{location}", location).replace('{time_posted}', duration[time_option])

    if page > 1:
        query_url += f"&start={start}"

    print(query_url)
    response = httpx.get(query_url)

    if response.status_code == 200:
        print("All good with requests!", end=" ")
    else:
        print(f"Linkedin API request was not successful, status code {response.status_code}", end=" ")
        return None

    soup = bs(response.text, 'html.parser')
    page_jobs = soup.find_all("li")
    return page_jobs


def parse_linkedin_jobs_to_dictionary_list(page_jobs):
    job_ids = []
    job_list = []
    for job in page_jobs:
        base_card_div = job.select(".base-card")[0]
        job_id = base_card_div.get("data-entity-urn").split(":")[3]
        job_ids.append(job_id)

    print(f"found {len(job_ids)} Jobs id!")

    # Loop through the list of job IDs and get each URL
    for job_id in job_ids:
        # Construct the URL for each job using the job ID
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        print("Getting job details: ", job_url)

        # Send a GET request to the job URL and parse the reponse
        fetch_url = True
        while fetch_url:
            job_response = httpx.get(job_url)
            job_soup = bs(job_response.text, "html.parser")
            if not job_soup.find("section"):
                # Fetching job details was not successful
                print("Will have to retry!")
                time.sleep(0.5)
            else:
                # Fetching job details was successful
                fetch_url = False
                # Create a dictionary to store job details
                job_url_a = job_soup.find("a", {"class": "topcard__link"})
                job_post = {"job_url": job_url_a.attrs["href"]}

                # Try to extract and store the job title
                try:
                    job_post["job_title"] = job_soup.find("h2", {
                        "class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"}).text.strip()
                except:
                    job_post["job_title"] = None

                # Try to extract and store the company name
                try:
                    job_post["company_name"] = job_soup.find("a", {
                        "class": "topcard__org-name-link topcard__flavor--black-link"}).text.strip()
                except:
                    job_post["company_name"] = None

                try:
                    job_post["city"] = job_soup.find("span", {
                        "class": "topcard__flavor topcard__flavor--bullet"}).text.strip()
                except:
                    job_post["city"] = None

                try:
                    job_desc_html = job_soup.find("div", {"class": "description__text description__text--rich"})
                    for e in job_desc_html.find_all(class_="show-more-less-html__button"):
                        e.decompose()
                    job_post["job_description"] = md(str(job_desc_html)).strip()
                except Exception as e:
                    print(e)
                    job_post["job_description"] = None

                # Try to extract and store the time posted
                try:
                    job_post["time_posted"] = job_soup.find("span", {
                        "class": "posted-time-ago__text topcard__flavor--metadata"}).text.strip()
                except:
                    job_post["time_posted"] = None

                # Try to extract and store the number of applicants
                try:
                    job_post["num_applicants"] = job_soup.find("span", {
                        "class": "num-applicants__caption topcard__flavor--metadata topcard__flavor--bullet"}).text.strip()
                except:
                    job_post["num_applicants"] = None

                # Append the job details to the job_list
                job_list.append(job_post)

    return job_list

