import openai
import streamlit as st
import streamlit_authenticator as stauth


def main():
    st.title("Générateur d'annonces")

    # Format login form
    authentication_status = format_login_form()

    if authentication_status is None:
        st.warning("Veuillez saisir votre nom d'utilisateur et mot de passe")
    elif authentication_status is False:
        st.error("Nom d'utilisateur et/ou mot de passe incorrect")
    elif authentication_status:
        format_ads_generator_form()


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


def format_ads_generator_form():
    with st.form("job_ads_generator_form"):
        brand = st.selectbox("Marque *", ("Aquila RH", "Lynx RH", "Vitalis Médical", "Mistertemp'"), key="brand")

        contrat_type = st.selectbox("Type de contrat *", ("Intérim", "CDI", "CDD", "Vacation"), key="contrat_type")

        qualification = st.text_input(
            "Qualification *",
            key="qualification",
            placeholder="Exemple : Cariste, aide-soignant, comptable, ...",
        )

        industry = st.text_input(
            "Secteur d'activité *",
            key="industry",
            placeholder="Exemple : Logistique, santé, immobilier, ...",
            help="Le secteur d'activité donne un contexte pour la rédaction d'annonce, en choisir un seul pour de meilleurs résultats",
        )

        prerequirement = st.text_input(
            "Pré-requis du poste",
            key="prerequirement",
            placeholder="Exemple : CACES, travail de nuit, 3x8, port de charge lourde, logiciel comptable SAGE, ...",
            help="Indiquez ici les prérequis souhaités pour le poste séparés par des virgules",
        )

        competencies = st.text_input(
            "Profil recherché",
            key="competencies",
            placeholder="Exemple : Rigoureux, travail en équipe, CAP/BEP, ...",
            help="Indiquez ici les compétences clés, savoir-être, savoir-faire, diplôme, séparés par des virgules",
        )

        submit_button = st.form_submit_button("Générer l'annonce")

        if submit_button:
            if brand.strip() == "":
                st.error("La marque est obligatoire.")
            elif contrat_type.strip() == "":
                st.error("Le type du contrat est obligatoire.")
            elif qualification.strip() == "":
                st.error("La qualification est obligatoire.")
            elif industry.strip() == "":
                st.error("Le secteur d'activité est obligatoire.")
            else:
                with st.spinner("En cours d'écriture..."):
                    agent, question = format_chat_message(
                        brand, contrat_type, qualification, industry, competencies, prerequirement
                    )
                    completion = call_chat(agent, question)
                    st.caption(completion.choices[0].message.content)


def format_chat_message(
    brand: str, contrat_type: str, qualification: str, industry: str, competencies: str, prerequirement: str
) -> str:
    brand = brand.strip()
    contrat_type = contrat_type.strip()
    qualification = qualification.strip()
    industry = industry.strip()
    competencies = competencies.strip()
    prerequirement = prerequirement.strip()

    agent = "Tu es un consultant d'une agence d'intérim et de recrutement de la marque " + brand

    question = "Rédige moi une annonce d'emploi attractive pour un poste de " + qualification

    question = question + " en " + contrat_type

    question = question + " dans le secteur d'activité suivant : " + industry + ". "

    if prerequirement != "":
        question = question + " avec les pré-requis de poste suivants : " + prerequirement + ". "

    if competencies != "":
        question = question + "Le profil recherché doit posséder les compétences suivantes : " + competencies + ". "

    question = (
        question
        + "Utilise des titres pour formater ta réponse en 5 sections en allant à la ligne après chaque titre : titre de l'annonce, descriptif du poste, missions principales du poste (sous forme de bullet points), profil recherché, pré-requis. "
    )

    question = question + "Ecris dans un style professionnel mais néanmoins énergique. "

    question = (
        question
        + """En mentionnant des bénéfices offerts par l'agence d'interim parmi les suivants :
        - Acomptes 2 fois par semaine les mardis et jeudis
        - 10% d’indemnité de fin de mission
        - 10% d’indemnité congés payés
        - Accédez à notre partenaire Couleur CE dès la 1ère heure de mission (billetterie, parcs et loisirs, art et culture…).
        - Bénéficiez d’une mutuelle d’entreprise et d’un accès au FASTT : accédez à des formations, des réductions sur vos locations de voiture, un accès prioritaire aux gardes d’enfant…"""
    )

    if brand == "Aquila RH" or brand == "Mistertemp'":
        question = (
            question
            + """
        - Avances de trésorerie jusqu’à 100% de vos Indemnités de Fin de Mission et Indémnités Congés Payés
        - Votre épargne rémunérée à 5% par an en 2023
        - Une prime de fidélité pouvant aller jusqu’à 200€ en janvier 2024"""
        )

    return agent, question


def call_chat(agent, question):
    openai.api_key = st.secrets.api_key

    print(agent)
    print(question)

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": agent},
            {"role": "user", "content": question},
        ],
    )

    return completion


# If in local, trigger main function
if __name__ == "__main__":
    main()
