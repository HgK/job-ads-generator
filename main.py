import openai
import streamlit as st


def main():
    st.title("Générateur d'annonces")

    with st.form("my_form"):
        qualification = st.text_input("Qualification")
        contrat_type = st.selectbox('Type de contrat', ('Intérim', 'CDD', 'CDI'))
        secteur = st.text_input("Secteur d'activité")
        profil_recherche = st.text_input("Profil recherché")
        caracteristique = st.text_input("Caractéristiques du poste")

        submitted = st.form_submit_button("Générer")

        if submitted:
            content = format_content(qualification, contrat_type, secteur, profil_recherche, caracteristique)
            completion = call_chat(content)

            st.caption(completion.choices[0].message.content)


def format_content(qualification: str, contrat_type: str,
                   secteur: str, profil_recherche: str, caracteristique: str) -> str:
    content = "Rédige moi une annonce d'emploi attractive pour un poste de "

    qualification = qualification.strip()
    if qualification == "":
        return "Error - Qualification is empty"

    content = content + qualification + " en " + contrat_type

    secteur = secteur.strip()
    if secteur != "":
        content = content + " dans le domaine de " + secteur

    caracteristique = caracteristique.strip()
    if caracteristique != "":
        content = content + " avec les caractéristiques de poste suivantes : " + caracteristique + "."

    profil_recherche = profil_recherche.strip()
    if profil_recherche != "":
        content = content + "Le profil recherché doit posséder les compétences suivantes : " + profil_recherche + "."

    content = content + "En faisant apparaître les missions principales sous forme de bullet point puis une section dediee pour le profil recherche."

    content = content + """En mentionnant des bénéfices offerts par l'agence d'interim parmi les suivants :
        - Acomptes 2 fois par semaine les mardis et jeudis
        - 10% d’indemnité de fin de mission
        - 10% d’indemnité congés payés
        - Avances de trésorerie jusqu’à 100% de vos Indemnités de Fin de Mission et Indémnités Congés Payés
        - Votre épargne rémunérée à 5% par an en 2023
        - Une prime de fidélité pouvant aller jusqu’à 200€ en janvier 2024
        - Accédez à notre partenaire Couleur CE dès la 1ère heure de mission (billetterie, parcs et loisirs, art et culture…).
        - Bénéficiez d’une mutuelle d’entreprise et d’un accès au FASTT : accédez à des formations, des réductions sur vos locations de voiture, un accès prioritaire aux gardes d’enfant…"""

    return content


def call_chat(content):
    openai.api_key = st.secrets.api_key

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un consultant d'une agence Aquila RH"},
            {"role": "user", "content": content}
        ]
    )

    return completion


# If in local, trigger main function
if __name__ == "__main__":
    main()
