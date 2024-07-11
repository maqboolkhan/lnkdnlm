import sys
import click
from dotenv import load_dotenv
from langchain import hub
import streamlit as st
from streamlit_extras.tags import tagger_component

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from fetcher import get_linkedin_jobs

from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


# Define your desired data structure.
class Joke(BaseModel):
    is_relavant_job: bool = Field(description="boolean value if job description relevant to given user criteria")
    reason: str = Field(description="reason why job description is relevant or not")

json_parser = JsonOutputParser()

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
            model="phi3:mini",
            keep_alive=-1,  # keep the model loaded indefinitely
            temperature=0,
            seed=1234
        )

        prompt = hub.pull("jobs")

        # prompt = ChatPromptTemplate.from_template("""    """)
        # hub.push("jobs", prompt, new_repo_is_public=False)
        # exit()

        # using LangChain Expressive Language chain syntax
        chain = prompt | llm | json_parser

        if st.session_state.clicked:
            linkedin_jobs = get_linkedin_jobs(job_title, location, time_option)
            for job in linkedin_jobs:
                if job['job_title'] and job['job_url'] and job["job_description"]:
                    st.markdown(f"### [{job['job_title']}]({job['job_url']})")
                    st.markdown(f"##### {job['company_name']}")
                    print("Invoking chain .. ")
                    with st.spinner('Reading it carefully...'):
                        res = chain.invoke({
                            "job_title": job["job_title"],
                            "job_company": job["company_name"],
                            "job_company_location": job["city"],
                            "job_description": job["job_description"],
                            "criteria": desired_criteria})
                    print(res)
                    if res["is_relevant_job"]:
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
