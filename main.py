import json
from datetime import date
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth
from openai import OpenAI

FOLDER = str(Path(__file__).parent)

DEFAULT_OPENAI_MODEL = "gpt-6-luna"
DEFAULT_OPENAI_REASONING_EFFORT = "none"

# SMIC horaire brut (arrêté du 22/05/2026): update it at each revaluation
SMIC_HOURLY_GROSS = {"value": 12.31, "since": "2026-06-01"}

BRANDS = ("Aquila RH", "Lynx RH", "Vitalis Médical", "Mistertemp'")
ITALIA_BRAND = "Mistertemp' Italia"


def main():
    global TRANSLATION, ADVANTAGES
    TRANSLATION = load_json("translation.json")
    ADVANTAGES = load_json("advantages.json")

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
    cookie = st.secrets.cookie

    credentials = dict(
        usernames=dict(
            mistertemp=dict(email=beta.email, name=beta.name, password=beta.password)
        )
    )
    authenticator = stauth.Authenticate(
        credentials, cookie.name, cookie.key, cookie.expiry_days
    )
    authenticator.login(location="main")

    return st.session_state["authentication_status"]


def format_ads_generator_container():
    tab_france, tab_italia = st.tabs(["🇫🇷 France", "🇮🇹 Italia"])

    with tab_france:
        format_ads_generator_form("France")

    with tab_italia:
        format_ads_generator_form("Italia")


def format_ads_generator_form(country: str):
    country_code = "fr" if country == "France" else "it"
    contract_type_codes = ["interim", "cdi", "cdd"]
    if country == "France":
        contract_type_codes.append("vacation")
    contract_types = {t(country_code, code): code for code in contract_type_codes}

    # Brand and contract type stay outside the form: the advantages follow them
    column_left, column_right = st.columns(2)
    if country == "France":
        brand = column_left.selectbox(
            t(country_code, "brand") + " *", BRANDS, key="brand_" + country_code
        )
        contract_type_column = column_right
    else:
        brand = ITALIA_BRAND
        contract_type_column = column_left

    contract_type = contract_type_column.selectbox(
        t(country_code, "contract_type") + " *",
        list(contract_types),
        key="contract_type_" + country_code,
    )
    contract_type_code = contract_types[contract_type]
    advantage_options = (
        ADVANTAGES.get(country_code, {}).get(brand, {}).get(contract_type_code, [])
    )

    with st.form("job_ads_generator_form_" + country_code):
        st.markdown("#### " + t(country_code, "section_job"))
        column_left, column_right = st.columns(2)

        qualification = column_left.text_input(
            t(country_code, "qualification") + " *",
            key="qualification_" + country_code,
            placeholder=t(country_code, "qualification_placeholder"),
        )

        industry = column_right.text_input(
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

        st.markdown("#### " + t(country_code, "section_conditions"))
        column_left, column_right = st.columns(2)

        location = column_left.text_input(
            t(country_code, "location"),
            key="location_" + country_code,
            placeholder=t(country_code, "location_placeholder"),
        )

        schedule = column_right.text_input(
            t(country_code, "schedule"),
            key="schedule_" + country_code,
            placeholder=t(country_code, "schedule_placeholder"),
        )

        start_date = column_left.date_input(
            t(country_code, "start_date"),
            value=None,
            format="DD/MM/YYYY",
            key="start_date_" + country_code,
        )

        duration = ""
        if contract_type_code != "cdi":
            duration = column_right.text_input(
                t(country_code, "duration"),
                key="duration_" + country_code,
                placeholder=t(country_code, "duration_placeholder"),
            )

        positions = column_left.number_input(
            t(country_code, "positions"),
            min_value=1,
            value=1,
            step=1,
            key="positions_" + country_code,
        )

        experience = column_right.selectbox(
            t(country_code, "experience"),
            t(country_code, "experience_options"),
            index=None,
            placeholder=t(country_code, "experience_placeholder"),
            key="experience_" + country_code,
        )

        hourly_pay = column_left.number_input(
            t(country_code, "hourly_pay"),
            min_value=0.0,
            value=None,
            step=0.01,
            format="%.2f",
            key="hourly_pay_" + country_code,
            help=t(country_code, "hourly_pay_help").format(**format_smic()),
        )

        st.markdown("#### " + t(country_code, "section_advantages"))

        advantages = []
        if advantage_options:
            # The key carries brand and contract type, so a switch resets the defaults
            advantages = st.multiselect(
                t(country_code, "advantages"),
                advantage_options,
                default=advantage_options,
                key=f"advantages_{country_code}_{brand}_{contract_type_code}",
                help=t(country_code, "advantages_help"),
            )

        client_advantages = st.text_input(
            t(country_code, "client_advantages"),
            key="client_advantages_" + country_code,
            placeholder=t(country_code, "client_advantages_placeholder"),
        )

        st.markdown("#### " + t(country_code, "section_writing"))

        tone = st.radio(
            t(country_code, "tone"),
            t(country_code, "tone_options"),
            horizontal=True,
            key="tone_" + country_code,
        )

        length = st.radio(
            t(country_code, "length"),
            list(t(country_code, "length_options")),
            index=1,
            horizontal=True,
            key="length_" + country_code,
        )

        social_version = st.toggle(
            t(country_code, "social_version"), key="social_version_" + country_code
        )

        submit_button = st.form_submit_button(
            t(country_code, "form_submit_button"), type="primary"
        )

    generate = st.session_state.pop("regenerate_requested_" + country_code, False)

    if submit_button:
        error = check_form(country, qualification, industry, hourly_pay)

        if error != "":
            st.error(error)
        else:
            st.session_state["prompt_" + country_code] = format_chat_message(
                country,
                dict(
                    brand=brand,
                    contract_type=contract_type,
                    qualification=qualification,
                    industry=industry,
                    tasks=tasks,
                    prerequirement=prerequirement,
                    competencies=competencies,
                    location=location,
                    schedule=schedule,
                    start_date=start_date,
                    duration=duration,
                    positions=positions,
                    experience=experience,
                    hourly_pay=hourly_pay,
                    advantages=advantages,
                    client_advantages=client_advantages,
                    tone=tone,
                    length=length,
                    social_version=social_version,
                ),
            )
            generate = True

    format_ad(country_code, generate)


def format_ad(country_code: str, generate: bool):
    ad_key = "ad_" + country_code

    if generate:
        agent, question = st.session_state["prompt_" + country_code]
        st.session_state[ad_key] = st.write_stream(call_chat(agent, question))
    elif ad_key in st.session_state:
        st.markdown(st.session_state[ad_key])

    if ad_key not in st.session_state:
        return

    ad = st.session_state[ad_key]

    with st.expander(t(country_code, "copy_text")):
        st.code(ad, language=None, wrap_lines=True)

    column_left, column_right = st.columns(2)

    # A flag read on the next run, so the new ad replaces the old one in its slot
    column_left.button(
        t(country_code, "regenerate"),
        key="regenerate_" + country_code,
        on_click=request_regeneration,
        args=(country_code,),
    )

    column_right.download_button(
        t(country_code, "download"),
        ad,
        file_name=t(country_code, "download_file_name"),
        mime="text/plain",
        key="download_" + country_code,
    )


def request_regeneration(country_code: str):
    st.session_state["regenerate_requested_" + country_code] = True


def check_form(
    country: str, qualification: str, industry: str, hourly_pay: float | None
) -> str:
    country_code = "fr" if country == "France" else "it"

    if qualification.strip() == "":
        return t(country_code, "qualification_error")

    if industry.strip() == "":
        return t(country_code, "industry_error")

    if (
        country == "France"
        and hourly_pay is not None
        and round(hourly_pay, 2) < SMIC_HOURLY_GROSS["value"]
    ):
        return t(country_code, "hourly_pay_error").format(**format_smic())

    return ""


def format_chat_message(country: str, form: dict) -> tuple[str, str]:
    country_code = "fr" if country == "France" else "it"
    form = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in form.items()
    }

    agent = t(country_code, "prompt_agent") + form["brand"]
    request_list = [
        t(country_code, "prompt_question_job_request"),
        t(country_code, "prompt_question_qualification").format(
            qualification=form["qualification"],
            contract_type=form["contract_type"],
            industry=form["industry"],
        ),
    ]

    details = dict(
        tasks=form["tasks"],
        prerequirement=form["prerequirement"],
        competencies=form["competencies"],
        location=form["location"],
        schedule=form["schedule"],
        start_date=(
            form["start_date"].strftime("%d/%m/%Y") if form["start_date"] else ""
        ),
        duration=form["duration"],
        positions=str(form["positions"]) if form["positions"] > 1 else "",
        experience=form["experience"] or "",
        hourly_pay=(
            format_amount(form["hourly_pay"]) if form["hourly_pay"] is not None else ""
        ),
        client_advantages=form["client_advantages"],
    )

    for key, value in details.items():
        if value != "":
            request_list.append(
                t(country_code, "prompt_question_" + key).format(**{key: value})
            )

    writing_list = [
        t(country_code, "prompt_question_format"),
        t(country_code, "prompt_question_tone").format(tone=form["tone"].lower()),
        t(country_code, "prompt_question_length").format(
            length=form["length"].lower(),
            words=t(country_code, "length_options")[form["length"]],
        ),
        t(country_code, "prompt_question_title"),
        t(country_code, "prompt_question_non_discrimination"),
        t(country_code, "prompt_question_no_invention"),
    ]

    paragraph_list = [" ".join(request_list), " ".join(writing_list)]

    if form["advantages"]:
        paragraph_list.append(
            "\n".join(
                [t(country_code, "prompt_question_advantage_title")]
                + ["- " + advantage for advantage in form["advantages"]]
            )
        )

    if form["social_version"]:
        paragraph_list.append(t(country_code, "prompt_question_social_version"))

    paragraph_list.append(t(country_code, "prompt_question_diversity"))

    return agent, "\n\n".join(
        paragraph for paragraph in paragraph_list if paragraph != ""
    )


def call_chat(agent: str, question: str):
    client = OpenAI(api_key=st.secrets.api_key)

    return client.chat.completions.create(
        model=st.secrets.get("openai_model", DEFAULT_OPENAI_MODEL),
        reasoning_effort=st.secrets.get(
            "openai_reasoning_effort", DEFAULT_OPENAI_REASONING_EFFORT
        ),
        messages=[
            {"role": "system", "content": agent},
            {"role": "user", "content": question},
        ],
        stream=True,
    )


def format_smic() -> dict:
    return dict(
        smic=format_amount(SMIC_HOURLY_GROSS["value"]),
        since=date.fromisoformat(SMIC_HOURLY_GROSS["since"]).strftime("%d/%m/%Y"),
    )


def format_amount(amount: float) -> str:
    return f"{amount:.2f}".replace(".", ",")


def load_json(file_name: str):
    with open(f"{FOLDER}/{file_name}", encoding="utf-8") as json_file:
        return json.load(json_file)


def t(language: str, key: str):
    return TRANSLATION[language][key]


# If in local, trigger main function
if __name__ == "__main__":
    main()
