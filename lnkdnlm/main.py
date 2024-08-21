import os
import sys
import time

import click
from dotenv import load_dotenv
from langchain import hub
import streamlit as st
from streamlit_extras.tags import tagger_component

from langchain_core.output_parsers import JsonOutputParser

from fetcher import parse_linkedin_jobs_to_dictionary_list, fetch_linkedin_page_jobs

from langchain_community.chat_models import ChatOllama


load_dotenv()


if 'clicked' not in st.session_state:
    st.session_state.clicked = False


def click_button():
    st.session_state.clicked = True


@click.command()
def main(args=None) -> int:
    with st.container():
        # Inject custom CSS to set the width of the sidebar
        st.markdown(
            """
            <style>
                section[data-testid="stSidebar"] {
                    width: 50% !important; # Set the width to your desired value
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.sidebar:
            st.header("LNKDNLM")
            st.text("Yours truly!")

            job_title = st.text_input("Job title", "").strip().replace(" ", "+")
            location = st.text_input("Location", "")

            time_option = st.selectbox(
                "Date posted:",
                ("Past 24 hours", "Past week", "Past month"))

            desired_criteria = st.text_area("", placeholder="Describe your ideal job here ..", height=500)
            st.button("Search it ...", type="primary", use_container_width=True, on_click=click_button)

        llm = ChatOllama(
            base_url=os.getenv("OLLAMA_ENDPOINT"),
            model=os.getenv("OLLAMA_MODEL"),
            keep_alive=-1,  # keep the model loaded indefinitely
            temperature=0,
            seed=1234
        )
        # TODO: Check here if Ollama is online and connected
        prompt = hub.pull("jobs")

        # prompt = ChatPromptTemplate.from_template("""    """)
        # hub.push("jobs", prompt, new_repo_is_public=False)
        # exit()

        json_parser = JsonOutputParser()
        # using LangChain Expressive Language chain syntax
        chain = prompt | llm | json_parser

        if st.session_state.clicked:
            fetch_more = True
            # First page
            page = 1
            page_jobs = fetch_linkedin_page_jobs(job_title, location, time_option, page)
            if not len(page_jobs):
                st.error('Could not find any new job at the moment, please make sure if you type your input correctly!', icon="🚨")
                return 0

            while fetch_more:
                linkedin_jobs = parse_linkedin_jobs_to_dictionary_list(page_jobs)
                fetch_more = False
                for job in linkedin_jobs:
                    if job['job_title'] and job['job_url'] and job["job_description"]:
                        st.markdown(f"### [{job['job_title']}]({job['job_url']})")
                        st.markdown(f"##### {job['company_name']}")
                        print("Invoking chain .. ")
                        with st.spinner('Reading it carefully...'):
                            start = time.perf_counter()
                            res = chain.invoke({
                                "job_title": job["job_title"],
                                "job_company": job["company_name"],
                                "job_company_location": job["city"],
                                "job_description": job["job_description"],
                                "criteria": desired_criteria})
                            end = time.perf_counter()
                            elapsed_time = end - start  # Calculate the elapsed time
                            print(f"Time took: {elapsed_time} seconds")
                        if "is_relevant_job" in res and res["is_relevant_job"]:
                            tagger_component(
                                "",
                                ["Matched ✅"],
                            )
                        else:
                            tagger_component(
                                "",
                                ["Did not match ❌"],
                            )
                        r_expander = st.expander("See reason")
                        r_expander.write(res["reason"])
                        jd_expander = st.expander("See job description")
                        jd_expander.write(job["job_description"])
                        st.divider()

                # Checking if more jobs are available to fetch if yes show button to fetch more
                print("END OF A PAGE")
                page += 1
                page_jobs = fetch_linkedin_page_jobs(job_title, location, time_option, page)
                if len(page_jobs):
                    if st.button("Analyze more jobs .."):
                        fetch_more = True

    return 0


if __name__ == "__main__":
    sys.exit(main())
