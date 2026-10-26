"""Guard tests for MT-87331: model fix and redesign of the job ads generator page.

They drive main.py through Streamlit's AppTest, log in with a test credential set on
AppTest.secrets and replace openai.OpenAI with a recording stub that streams real
ChatCompletionChunk objects: no test reads .streamlit/secrets.toml or reaches OpenAI.
Set JAG_MAIN to run them against another copy of the app.
"""

import datetime
import os
import re
from types import SimpleNamespace

import openai
import pytest
import streamlit as st
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
from streamlit.testing.v1 import AppTest
from streamlit_authenticator.utilities.hasher import Hasher

MAIN = os.environ.get("JAG_MAIN", "../main.py")
API_KEY = "sk-test-not-a-real-key"
USERNAME = "mistertemp"
PASSWORD = "test-password-123"
PASSWORD_HASH = Hasher.hash(PASSWORD)

TAB = {"fr": "🇫🇷 France", "it": "🇮🇹 Italia"}
SUBMIT = {"fr": "Générer l'annonce", "it": "Genera l'annuncio"}
COPY_EXPANDER = {"fr": "Texte à copier", "it": "Testo da copiare"}
REGENERATE = {"fr": "Régénérer", "it": "Rigenera"}
TITLE_SUFFIX = {"fr": "H/F", "it": "(m/f)"}
SOCIAL = {"fr": "réseaux sociaux", "it": "social"}
BRANDS = ["Aquila RH", "Lynx RH", "Vitalis Médical", "Mistertemp'"]
CONTRACTS = {
    "fr": ["Intérim", "CDI", "CDD", "Vacation"],
    "it": [
        "Somministrazione",
        "Contratto a tempo indeterminato",
        "Contratto a tempo determinato",
    ],
}
OPEN_ENDED = {"fr": "CDI", "it": "Contratto a tempo indeterminato"}
EXPERIENCE = {
    "fr": ["Débutant accepté", "1 à 3 ans", "Confirmé (3 ans et plus)"],
    "it": ["Principiante accettato", "Da 1 a 3 anni", "Esperto (3 anni e più)"],
}
TONE = {
    "fr": ["Professionnel et énergique", "Chaleureux", "Sobre et factuel"],
    "it": ["Professionale ed energico", "Cordiale", "Sobrio e fattuale"],
}
LENGTH = {
    "fr": ["Courte", "Standard", "Détaillée"],
    "it": ["Breve", "Standard", "Dettagliato"],
}
REQUIRED = {
    "fr": {"qualification": "Cariste", "industry": "Logistique"},
    "it": {"qualification": "Carrellista", "industry": "Logistica"},
}
FILLED = {
    "fr": {
        "tasks": "Charger les camions",
        "prerequirement": "CACES R489",
        "competencies": "Rigueur et ponctualité",
        "location": "   Villepinte (93)   ",
        "schedule": "Du lundi au vendredi, 6h-13h",
        "duration": "6 mois renouvelables",
        "client_advantages": "Tickets restaurant et prime de panier",
        "start_date": datetime.date(2026, 11, 16),
        "positions": 7,
        "experience": "1 à 3 ans",
        "hourly_pay": 15.5,
        "tone": "Chaleureux",
        "length": "Détaillée",
    },
    "it": {
        "tasks": "Caricare i camion",
        "prerequirement": "Patentino del muletto",
        "competencies": "Precisione e puntualità",
        "location": "   Bologna (BO)   ",
        "schedule": "Dal lunedì al venerdì, 6-13",
        "duration": "6 mesi rinnovabili",
        "client_advantages": "Buoni pasto e premio di produzione",
        "start_date": datetime.date(2026, 11, 16),
        "positions": 7,
        "experience": "Da 1 a 3 anni",
        "hourly_pay": 9.5,
        "tone": "Cordiale",
        "length": "Breve",
    },
}
FILLED_IN_PROMPT = {
    "fr": [
        "Charger les camions",
        "CACES R489",
        "Rigueur et ponctualité",
        "Villepinte (93)",
        "Du lundi au vendredi, 6h-13h",
        "6 mois renouvelables",
        "Tickets restaurant et prime de panier",
        "16/11/2026",
        "1 à 3 ans",
        "15,50",
        "chaleureux",
        "détaillée",
    ],
    "it": [
        "Caricare i camion",
        "Patentino del muletto",
        "Precisione e puntualità",
        "Bologna (BO)",
        "Dal lunedì al venerdì, 6-13",
        "6 mesi rinnovabili",
        "Buoni pasto e premio di produzione",
        "16/11/2026",
        "Da 1 a 3 anni",
        "9,50",
        "cordiale",
        "breve",
    ],
}

# The advantage lines the base code (fc6fbc2) put in its France + Intérim prompt.
ADVANCE = "- Acomptes 2 fois par semaine les mardis et jeudis"
IFM = "- 10% d’indemnité de fin de mission"
ICP = "- 10% d’indemnité congés payés"
ADVANCE_IFM_ICP = (
    "- Avances de trésorerie jusqu’à 100% de vos Indemnités de Fin de Mission et "
    "Indémnités Congés Payés"
)
SAVING = "- Votre épargne rémunérée à 5% par an en 2025"
FIDELITY_BONUS = "- Une prime de fidélité pouvant aller jusqu’à 200€ en janvier 2026"
COULEUR_CE = (
    "- Accédez à notre partenaire Couleur CE dès la 1ère heure de mission "
    "(billetterie, parcs et loisirs, art et culture…)."
)
INSURANCE = (
    "- Bénéficiez d’une mutuelle d’entreprise et d’un accès au FASTT : accédez à des "
    "formations, des réductions sur vos locations de voiture, un accès prioritaire "
    "aux gardes d’enfant…"
)
SHORT_ADVANTAGES = [ADVANCE, IFM, ICP, COULEUR_CE, INSURANCE]
LONG_ADVANTAGES = [
    ADVANCE,
    IFM,
    ICP,
    ADVANCE_IFM_ICP,
    SAVING,
    FIDELITY_BONUS,
    COULEUR_CE,
    INSURANCE,
]
INTERIM_ADVANTAGES = {
    "Aquila RH": LONG_ADVANTAGES,
    "Lynx RH": SHORT_ADVANTAGES,
    "Vitalis Médical": SHORT_ADVANTAGES,
    "Mistertemp'": LONG_ADVANTAGES,
}

CALLS = []
CLIENTS = []


def ad_text(n):
    """The text the stub streams for the n-th OpenAI call."""
    return f"Annonce AD#{n} H/F\n\nTexte de l'annonce numéro AD#{n}, à publier."


def chunk(content, finish_reason=None, role=None):
    return ChatCompletionChunk(
        id="chatcmpl-stub",
        created=0,
        model="stub",
        object="chat.completion.chunk",
        choices=[
            Choice(
                index=0,
                delta=ChoiceDelta(content=content, role=role),
                finish_reason=finish_reason,
            )
        ],
    )


def fake_stream(text):
    """A streamed completion as OpenAI sends it: role, content pieces, empty stop."""
    yield chunk("", role="assistant")
    for start in range(0, len(text), 12):
        end = start + 12
        yield chunk(text[start:end])
    yield chunk(None, finish_reason="stop")


class FakeCompletions:
    def create(self, **kwargs):
        CALLS.append(kwargs)
        return fake_stream(ad_text(len(CALLS)))


class FakeOpenAI:
    def __init__(self, **kwargs):
        CLIENTS.append(kwargs)
        self.chat = SimpleNamespace(completions=FakeCompletions())


@pytest.fixture(autouse=True)
def stub_openai(monkeypatch):
    """Every OpenAI client the app builds is the recording stub, never the real API."""
    CALLS.clear()
    CLIENTS.clear()
    st.cache_data.clear()
    st.cache_resource.clear()
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:9/unreachable")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def make_app(preauthorized=True, **extra_secrets):
    at = AppTest.from_file(MAIN, default_timeout=30)
    at.secrets["api_key"] = API_KEY
    at.secrets["beta"] = {
        "email": "beta@example.com",
        "name": "Beta Tester",
        "password": PASSWORD_HASH,
    }
    at.secrets["cookie"] = {
        "name": "jag_test_cookie",
        "key": "jag-test-cookie-signing-key-0123456789",
        "expiry_days": 1,
    }
    if preauthorized:
        at.secrets["preauthorized"] = {"emails": []}
    for name, value in extra_secrets.items():
        at.secrets[name] = value
    return at


def run(node):
    """Run the app, or the interaction queued on a widget, and fail on any exception."""
    at = node.run()
    assert not at.exception, "app raised: " + " | ".join(e.value for e in at.exception)
    return at


def submit_login(at, password):
    run(at)
    inputs = at.text_input
    assert len(inputs) == 2, f"no login form: {[w.label for w in inputs]}"
    inputs[0].input(USERNAME)
    inputs[1].input(password)
    assert len(at.button) == 1, f"no login button: {[b.label for b in at.button]}"
    return run(at.button[0].click())


def logged_in(**extra_secrets):
    at = submit_login(make_app(**extra_secrets), PASSWORD)
    assert at.session_state["authentication_status"] is True
    return at


def tab(at, cc):
    tabs = [t for t in at.tabs if t.label == TAB[cc]]
    assert len(tabs) == 1, f"tab {TAB[cc]!r} not in {[t.label for t in at.tabs]}"
    return tabs[0]


def select(at, key, option):
    """Pick an option in a selectbox that sits above the form (reruns the page)."""
    run(at.selectbox(key=key).select(option))


def fill_form(at, cc, values):
    for name, value in values.items():
        at.get_by_key(f"{name}_{cc}").set_value(value)


def submit(at, cc):
    buttons = [b for b in tab(at, cc).button if b.label == SUBMIT[cc]]
    assert len(buttons) == 1, f"no {SUBMIT[cc]!r} button in tab {TAB[cc]!r}"
    run(buttons[0].click())


def user_prompt(call):
    contents = [m["content"] for m in call["messages"] if m["role"] == "user"]
    assert len(contents) == 1, f"expected one user message, got {len(contents)}"
    assert contents[0].strip(), "empty prompt"
    return contents[0]


def generate(at, cc, values=None):
    """Fill the required fields (plus `values`), submit, return the prompt sent."""
    before = len(CALLS)
    fill_form(at, cc, {**REQUIRED[cc], **(values or {})})
    submit(at, cc)
    made = len(CALLS) - before
    assert made == 1, f"expected 1 OpenAI call, got {made}"
    return user_prompt(CALLS[-1])


def advantage_lines(prompt):
    return [line for line in prompt.splitlines() if line in LONG_ADVANTAGES]


def advantages_widget(at):
    found = [m for m in at.multiselect if (m.key or "").startswith("advantages_fr")]
    assert len(found) <= 1, f"several advantages multiselects: {[m.key for m in found]}"
    return found[0] if found else None


def bare(lines):
    return [line.removeprefix("- ") for line in lines]


def ads(block):
    return [m.value for m in block.markdown if "AD#" in m.value]


def assert_one_ad(block, n):
    """Exactly one ad is on screen in `block`, as Markdown, and it is the n-th."""
    shown = ads(block)
    assert len(shown) == 1, f"{len(shown)} ads on screen: {shown}"
    assert ad_text(n) in shown[0], f"expected AD#{n}, got {shown[0]!r}"


def copy_boxes(block, cc):
    expanders = [e for e in block.expander if e.label == COPY_EXPANDER[cc]]
    assert len(expanders) == 1, f"no {COPY_EXPANDER[cc]!r} expander"
    return [c.value for c in expanders[0].code]


def texts(block):
    elements = [*block.markdown, *block.code, *block.caption, *block.text]
    return [e.value for e in elements]


def assert_clean_prompt(prompt):
    for token in ("None", "{", "}"):
        assert token not in prompt, f"{token!r} in prompt"


def assert_advantage_lines(prompt, expected):
    lines = advantage_lines(prompt)
    missing = [line for line in expected if line not in lines]
    unexpected = [line for line in lines if line not in expected]
    order = "" if missing or unexpected else " (same lines, other order or repeated)"
    assert lines == expected, f"missing lines {missing}, unexpected {unexpected}{order}"


def count_number(text, number):
    """How many times `number` stands alone in `text` (not inside 12,31 or 2026)."""
    return len(re.findall(rf"(?<![\d.,/]){number}(?![\d]|[.,/]\d)", text))


@pytest.mark.parametrize("brand", BRANDS)
def test_interim_advantage_lines_match_base(brand):
    """France + Intérim: each of the brand's advantages is its own prompt line, as in
    the base prompt, and the other brands' advantages are absent."""
    at = logged_in()
    select(at, "brand_fr", brand)
    select(at, "contract_type_fr", "Intérim")
    prompt = generate(at, "fr")
    expected = INTERIM_ADVANTAGES[brand]
    assert expected
    assert_advantage_lines(prompt, expected)
    for line in LONG_ADVANTAGES:
        if line not in expected:
            assert line.removeprefix("- ") not in prompt


@pytest.mark.parametrize(
    ("brand", "contract"), [("Aquila RH", "CDI"), ("Vitalis Médical", "Vacation")]
)
def test_no_advantage_line_outside_interim(brand, contract):
    """A non-Intérim contract sends no advantage, even after Intérim pre-selected
    some for the brand."""
    at = logged_in()
    select(at, "brand_fr", brand)
    select(at, "contract_type_fr", "Intérim")
    widget = advantages_widget(at)
    assert widget is not None and widget.value, "Intérim pre-selected no advantage"
    select(at, "contract_type_fr", contract)
    prompt = generate(at, "fr")
    assert contract in prompt
    assert_advantage_lines(prompt, [])
    for line in LONG_ADVANTAGES:
        assert line.removeprefix("- ") not in prompt


def test_advantages_preselection_follows_brand_and_contract():
    """The pre-selected advantages are the brand's Intérim list, follow a brand
    change, and empty out for a non-Intérim contract; Italia has none."""
    at = logged_in()
    assert at.selectbox(key="brand_fr").options == BRANDS
    widget = advantages_widget(at)
    assert widget is not None, "no advantages_fr multiselect for Aquila RH + Intérim"
    assert widget.value == bare(INTERIM_ADVANTAGES["Aquila RH"]), "Aquila RH"
    select(at, "brand_fr", "Lynx RH")
    widget = advantages_widget(at)
    assert widget is not None, "no advantages_fr multiselect for Lynx RH + Intérim"
    assert widget.value == bare(INTERIM_ADVANTAGES["Lynx RH"]), "Lynx RH kept Aquila's"
    select(at, "contract_type_fr", "CDI")
    widget = advantages_widget(at)
    assert widget is None or widget.value == [], "CDI kept advantages selected"
    italia = [m.key for m in tab(at, "it").multiselect]
    assert not [key for key in italia if (key or "").startswith("advantages")]


def test_france_pay_below_smic_blocks_generation():
    """France: a gross hourly pay below the 12.31 € SMIC shows an error and calls no
    model; 12.31 itself generates."""
    at = logged_in()
    fill_form(at, "fr", {**REQUIRED["fr"], "hourly_pay": 12.30})
    submit(at, "fr")
    assert at.number_input(key="hourly_pay_fr").value == pytest.approx(12.30)
    assert tab(at, "fr").error, "no error for a pay below the SMIC"
    assert CALLS == []
    prompt = generate(at, "fr", {"hourly_pay": 12.31})
    assert not tab(at, "fr").error
    assert "12,31" in prompt


def test_italia_pay_has_no_floor():
    """Italia: a low hourly pay still generates, with no error."""
    at = logged_in()
    prompt = generate(at, "it", {"hourly_pay": 5.00})
    assert at.number_input(key="hourly_pay_it").value == pytest.approx(5.00)
    assert not tab(at, "it").error
    assert "5,00" in prompt


@pytest.mark.parametrize("cc", ["fr", "it"])
def test_prompt_with_only_required_fields(cc):
    """Optional fields start empty and, left empty, add nothing: the prompt keeps the
    required values, the title suffix and the default tone and length only."""
    at = logged_in()
    assert at.date_input(key=f"start_date_{cc}").value is None
    positions = at.number_input(key=f"positions_{cc}")
    assert positions.value == 1 and isinstance(positions.value, int)
    assert positions.min == 1
    pay = at.number_input(key=f"hourly_pay_{cc}")
    assert pay.value is None and pay.step == pytest.approx(0.01)
    experience = at.selectbox(key=f"experience_{cc}")
    assert experience.value is None and experience.options == EXPERIENCE[cc]
    assert at.radio(key=f"tone_{cc}").options == TONE[cc]
    assert at.radio(key=f"tone_{cc}").value == TONE[cc][0]
    assert at.radio(key=f"length_{cc}").options == LENGTH[cc]
    assert at.radio(key=f"length_{cc}").value == "Standard"
    assert at.toggle(key=f"social_version_{cc}").value is False
    prompt = generate(at, cc)
    lowered = prompt.lower()
    for value in [*REQUIRED[cc].values(), CONTRACTS[cc][0]]:
        assert value in prompt
    assert TITLE_SUFFIX[cc] in prompt
    other_suffix = TITLE_SUFFIX["it" if cc == "fr" else "fr"]
    assert other_suffix not in prompt
    assert TONE[cc][0].lower() in prompt and "standard" in prompt
    for label in [*TONE[cc][1:], LENGTH[cc][0], LENGTH[cc][2], *EXPERIENCE[cc]]:
        assert label.lower() not in lowered, f"{label!r} in prompt"
    assert SOCIAL[cc] not in lowered
    assert_clean_prompt(prompt)
    two_positions = generate(at, cc, {"positions": 2})
    assert count_number(two_positions, 2) > count_number(prompt, 2)
    assert count_number(prompt, 1) <= count_number(two_positions, 1), "1 position"


@pytest.mark.parametrize("cc", ["fr", "it"])
def test_filled_optional_fields_reach_prompt(cc):
    """Each filled optional field adds its value (trimmed text, dd/mm/yyyy date,
    positions, experience, comma pay, lowercased tone and length)."""
    at = logged_in()
    prompt = generate(at, cc, FILLED[cc])
    lowered = prompt.lower()
    for value in FILLED_IN_PROMPT[cc]:
        assert value in prompt, f"{value!r} not in prompt"
    assert count_number(prompt, 7), "positions not in prompt"
    location = FILLED[cc]["location"].strip()
    assert "  " + location not in prompt and location + "  " not in prompt, "untrimmed"
    chosen = {FILLED[cc]["tone"], FILLED[cc]["length"], FILLED[cc]["experience"]}
    for label in [*TONE[cc], *LENGTH[cc], *EXPERIENCE[cc]]:
        if label not in chosen:
            assert label.lower() not in lowered, f"{label!r} in prompt"
    assert SOCIAL[cc] not in lowered
    assert_clean_prompt(prompt)


@pytest.mark.parametrize("cc", ["fr", "it"])
def test_social_version_toggle(cc):
    """The social toggle adds a sentence on the short social-media version; off adds
    none."""
    at = logged_in()
    toggle = at.toggle(key=f"social_version_{cc}")
    assert toggle.value is False
    prompt_off = generate(at, cc)
    at.toggle(key=f"social_version_{cc}").set_value(True)
    prompt_on = generate(at, cc)
    assert SOCIAL[cc] not in prompt_off.lower()
    assert SOCIAL[cc] in prompt_on.lower()
    assert_clean_prompt(prompt_on)


@pytest.mark.parametrize("cc", ["fr", "it"])
def test_duration_hidden_for_open_ended_contract(cc):
    """The mission duration field shows for every contract but the open-ended one."""
    at = logged_in()
    assert at.selectbox(key=f"contract_type_{cc}").options == CONTRACTS[cc]
    for contract in CONTRACTS[cc]:
        select(at, f"contract_type_{cc}", contract)
        keys = [w.key for w in tab(at, cc).text_input]
        assert f"qualification_{cc}" in keys
        shown = f"duration_{cc}" in keys
        assert shown == (contract != OPEN_ENDED[cc]), f"{contract}: duration {shown=}"


def test_login_gates_the_ad_form():
    """Before login only the login form shows; the test credential logs in and both
    tabs render their form."""
    at = run(make_app())
    assert len(at.text_input) == 2, "no login form"
    assert at.warning, "no login warning"
    assert not at.tabs
    assert "qualification_fr" not in [w.key for w in at.text_input]
    assert CALLS == []
    at.text_input[0].input(USERNAME)
    at.text_input[1].input(PASSWORD)
    run(at.button[0].click())
    assert at.session_state["authentication_status"] is True
    assert tab(at, "fr").text_input(key="qualification_fr")
    assert tab(at, "it").text_input(key="qualification_it")


def test_wrong_password_keeps_the_form_hidden():
    """A wrong password leaves the user logged out and the ad form hidden."""
    at = submit_login(make_app(), "not-the-password")
    assert at.session_state["authentication_status"] is False
    assert at.error
    assert not at.tabs
    assert "qualification_fr" not in [w.key for w in at.text_input]


def test_login_works_without_preauthorized_secret():
    """The unused `preauthorized` secret is not required to log in."""
    at = submit_login(make_app(preauthorized=False), PASSWORD)
    assert at.session_state["authentication_status"] is True
    assert tab(at, "fr").text_input(key="qualification_fr")


@pytest.mark.parametrize(
    ("secrets", "model", "effort"),
    [
        ({}, "gpt-6-luna", "none"),
        ({"openai_model": "gpt-test-model"}, "gpt-test-model", "none"),
        ({"openai_reasoning_effort": "low"}, "gpt-6-luna", "low"),
    ],
)
def test_model_and_reasoning_effort_from_secrets(secrets, model, effort):
    """The model and reasoning effort come from the secrets when set, else
    gpt-6-luna and none; the call streams a system + user message."""
    at = logged_in(**secrets)
    generate(at, "fr")
    assert CLIENTS, "no OpenAI client built"
    assert all(client.get("api_key") == API_KEY for client in CLIENTS)
    call = CALLS[0]
    assert call.get("model") == model
    assert call.get("reasoning_effort") == effort
    assert call.get("stream") is True
    assert [m["role"] for m in call["messages"]] == ["system", "user"]
    assert call["messages"][0]["content"].strip()


@pytest.mark.parametrize("cc", ["fr", "it"])
def test_generated_ad_renders_with_copy_download_and_regenerate(cc):
    """A generated ad shows as Markdown, in the copy box, with a download button and
    a regenerate button, and nothing raises."""
    at = logged_in()
    generate(at, cc)
    block = tab(at, cc)
    assert_one_ad(block, 1)
    boxes = copy_boxes(block, cc)
    assert len(boxes) == 1 and ad_text(1) in boxes[0], f"copy box: {boxes}"
    assert [d.key for d in block.download_button] == [f"download_{cc}"]
    regenerate = [b for b in block.button if b.key == f"regenerate_{cc}"]
    assert len(regenerate) == 1 and regenerate[0].label == REGENERATE[cc]
    assert not at.exception


def test_regenerate_restreams_stored_prompt_once():
    """Régénérer makes exactly one call with the stored prompt and replaces the ad;
    a plain rerun calls nothing and keeps the ad; Italia never shows it."""
    at = logged_in()
    prompt = generate(at, "fr")
    assert_one_ad(tab(at, "fr"), 1)
    run(at)
    assert len(CALLS) == 1, "a plain rerun called OpenAI"
    assert_one_ad(tab(at, "fr"), 1)
    run(at.button(key="regenerate_fr").click())
    assert len(CALLS) == 2, f"Régénérer made {len(CALLS) - 1} calls"
    assert user_prompt(CALLS[1]) == prompt
    france = tab(at, "fr")
    assert_one_ad(france, 2)
    boxes = copy_boxes(france, "fr")
    assert len(boxes) == 1 and ad_text(2) in boxes[0], f"copy box: {boxes}"
    assert "AD#1" not in boxes[0]
    run(at)
    assert len(CALLS) == 2, "a plain rerun called OpenAI"
    assert_one_ad(tab(at, "fr"), 2)
    italia = tab(at, "it")
    leaked = [text for text in texts(italia) if "AD#" in text]
    assert not leaked, f"France ad shown in the Italia tab: {leaked}"
    assert not [b.key for b in italia.button if b.key == "regenerate_it"]
    assert not italia.download_button


def test_italia_generation_stays_in_italia_tab():
    """An Italia ad asks for a (m/f) title and shows in the Italia tab only."""
    at = logged_in()
    prompt = generate(at, "it")
    assert "(m/f)" in prompt and "H/F" not in prompt
    assert_one_ad(tab(at, "it"), 1)
    leaked = [text for text in texts(tab(at, "fr")) if "AD#" in text]
    assert not leaked, f"Italia ad shown in the France tab: {leaked}"
