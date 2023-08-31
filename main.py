import json
from pathlib import Path

import openai
import streamlit as st
import streamlit_authenticator as stauth

FOLDER = str(Path(__file__).parent)


def main():
    global TRANSLATION
    TRANSLATION = load_translation()

    st.title(":robot_face::memo: Générateur d'annonces")

    hide_streamlit_style = """
                <style>
                header {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Format login form
    authentication_status = format_login_form()

    if authentication_status is None:
        st.warning("Veuillez saisir votre nom d'utilisateur et mot de passe")
    elif authentication_status is False:
        st.error("Nom d'utilisateur et/ou mot de passe incorrect")
    elif authentication_status:
        format_ads_generator_container()


def format_login_form():
    beta = st.secrets.beta
    cookie_name = st.secrets.cookie.name
    cookie_key = st.secrets.cookie.key
    cookie_expiry_days = st.secrets.cookie.expiry_days
    preauthorized = st.secrets.preauthorized

    credentials = dict(usernames=dict(mistertemp=dict(email=beta.email, name=beta.name, password=beta.password)))
    authenticator = stauth.Authenticate(credentials, cookie_name, cookie_key, cookie_expiry_days, preauthorized)
    name, authentication_status, username = authenticator.login("Connection", "main")

    return authentication_status


def format_ads_generator_container():
    tab_france, tab_italia = st.tabs(["🇫🇷 France", "🇮🇹 Italia"])

    with tab_france:
        format_ads_generator_form("France")

    with tab_italia:
        format_ads_generator_form("Italia")


def format_ads_generator_form(country: str):
    country_code = "fr" if country == "France" else "it"

    with st.form("job_ads_generator_form_" + country_code):
        if country == "France":
            brand = st.selectbox(
                t(country_code, "brand") + " *",
                ("Aquila RH", "Lynx RH", "Vitalis Médical", "Mistertemp'"),
                key="brand_" + country_code,
            )

            contract_type = st.selectbox(
                t(country_code, "contract_type") + " *",
                (
                    t(country_code, "interim"),
                    t(country_code, "cdi"),
                    t(country_code, "cdd"),
                    t(country_code, "vacation"),
                ),
                key="contract_type_" + country_code,
            )
        else:
            brand = "Mistertemp' Italia"

            contract_type = st.selectbox(
                t(country_code, "contract_type") + " *",
                (t(country_code, "interim"), t(country_code, "cdi"), t(country_code, "cdd")),
                key="contract_type_" + country_code,
            )

        qualification = st.text_input(
            t(country_code, "qualification") + " *",
            key="qualification_" + country_code,
            placeholder=t(country_code, "qualification_placeholder"),
        )

        industry = st.text_input(
            t(country_code, "industry") + " *",
            key="industry_" + country_code,
            placeholder=t(country_code, "industry_placeholder"),
            help=t(country_code, "industry_help"),
        )

        tasks = st.text_input(
            t(country_code, "tasks"),
            key="tasks_" + country_code,
            placeholder=t(country_code, "tasks_placeholder"),
            help=t(country_code, "tasks_help"),
        )

        prerequirement = st.text_input(
            t(country_code, "prerequirement"),
            key="prerequirement_" + country_code,
            placeholder=t(country_code, "prerequirement_placeholder"),
            help=t(country_code, "prerequirement_help"),
        )

        competencies = st.text_input(
            t(country_code, "competencies"),
            key="competencies_" + country_code,
            placeholder=t(country_code, "competencies_placeholder"),
            help=t(country_code, "competencies_help"),
        )

        submit_button = st.form_submit_button(t(country_code, "form_submit_button"))

        if submit_button:
            if brand.strip() == "":
                st.error(t(country_code, "brand_error"))
            elif contract_type.strip() == "":
                st.error(t(country_code, "contract_type_error"))
            elif qualification.strip() == "":
                st.error(t(country_code, "qualification_error"))
            elif industry.strip() == "":
                st.error(t(country_code, "industry_error"))
            else:
                agent, question = format_chat_message(
                    country,
                    brand,
                    contract_type,
                    qualification,
                    industry,
                    competencies,
                    prerequirement,
                    tasks,
                )

                res_box = st.empty()
                report = []

                for resp in call_chat(agent, question):
                    if resp.choices[0].finish_reason != "stop":
                        report.append(resp.choices[0].delta.content)
                        result = "".join(report).strip()
                        res_box.caption(f"{result}")


def format_chat_message(
    country: str,
    brand: str,
    contract_type: str,
    qualification: str,
    industry: str,
    competencies: str,
    prerequirement: str,
    tasks: str,
) -> str:
    country_code = "fr" if country == "France" else "it"
    brand = brand.strip()
    contract_type = contract_type.strip()
    qualification = qualification.strip()
    industry = industry.strip()
    competencies = competencies.strip()
    prerequirement = prerequirement.strip()
    tasks = tasks.strip()

    agent = t(country_code, "prompt_agent") + brand
    question_list = [
        t(country_code, "prompt_question_job_request"),
        t(country_code, "prompt_question_qualification").format(
            qualification=qualification, contract_type=contract_type, industry=industry
        ),
    ]

    if tasks != "":
        question_list.append(t(country_code, "prompt_question_tasks").format(tasks=tasks))

    if prerequirement != "":
        question_list.append(t(country_code, "prompt_question_prerequirement").format(prerequirement=prerequirement))

    if competencies != "":
        question_list.append(t(country_code, "prompt_question_competencies").format(competencies=competencies))

    question_list.append(t(country_code, "prompt_question_format"))

    if country == "France" and contract_type == "Intérim":
        advantage_list = [
            t(country_code, "prompt_question_advantage_title"),
            t(country_code, "prompt_question_advantage_advance"),
            t(country_code, "prompt_question_advantage_ifm"),
            t(country_code, "prompt_question_advantage_icp"),
        ]

        if brand == "Aquila RH" or brand == "Mistertemp'":
            advantage_list = advantage_list + [
                t(country_code, "prompt_question_advantage_advance_ifm_icp"),
                t(country_code, "prompt_question_advantage_saving"),
                t(country_code, "prompt_question_advantage_fidelity_bonus"),
            ]

        advantage_list = advantage_list + [
            t(country_code, "prompt_question_advantage_couleur_ce"),
            t(country_code, "prompt_question_advantage_insurance"),
        ]

        question_list.append("\n".join(advantage_list))

    return agent, " ".join(question_list)


def call_chat(agent: str, question: str):
    openai.api_key = st.secrets.api_key

    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": agent},
            {"role": "user", "content": question},
        ],
        stream=True,
    )


def load_translation():
    with open(f"{FOLDER}/translation.json") as json_file:
        return json.load(json_file)


def t(language: str, key: str):
    return TRANSLATION[language][key]


# If in local, trigger main function
if __name__ == "__main__":
    main()
