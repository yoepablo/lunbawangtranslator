import json
from flask import Flask, render_template, request

app = Flask(__name__)


def load_data():
    try:
        with open("lun_bawang.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR loading lun_bawang.json: {e}")
        return {}


DATA = load_data()

LANG_NAMES = {
    "lun_bawang": "Lun Bawang",
    "english": "English",
    "malay": "Malay",
}

# These are real multi-word/question entries from the JSON.
EXAMPLE_KEYS = [
    "anun bala?",
    "anun ruen mu?",
    "anun ineh?",
    "ide ngadan mu?",
    "me' yapeh ko",
    "rat yapeh ko",
    "maya' negku",
    "mo umak",
    "ame tunge",
    "ame dei",
    "le miud pa kabing",
    "le miud pa tinueh",
    "lawe siri siri",
    "do pekak",
    "bala do'",
    "napeh atun",
    "takep rudap",
]


def normalize(value):
    return " ".join(value.strip().lower().split())


def split_values(value):
    if not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def find_exact_in_field(text, field):
    clean = normalize(text)
    matches = []

    for lb_word, translations in DATA.items():
        value = translations.get(field, "")
        if not isinstance(value, str):
            continue

        # Match the whole stored value first.
        if normalize(value) == clean:
            matches.append(lb_word)
            continue

        # Also support comma-separated meanings such as "cheap, difficult".
        for item in split_values(value):
            if normalize(item) == clean:
                matches.append(lb_word)
                break

    return matches


def translate(text, source_lang, target_lang):
    clean = normalize(text)

    if not clean:
        return ""

    if source_lang == target_lang:
        return text.strip()

    # Lun Bawang -> English/Malay
    if source_lang == "lun_bawang":
        entry = DATA.get(clean)
        if entry:
            result = entry.get(target_lang, "")
            if result:
                return result

        # Try case-insensitive exact key matching.
        for lb_word, entry in DATA.items():
            if normalize(lb_word) == clean:
                result = entry.get(target_lang, "")
                if result:
                    return result

        return f"No {LANG_NAMES[target_lang]} translation found."

    # English/Malay -> Lun Bawang
    if target_lang == "lun_bawang":
        matches = find_exact_in_field(clean, source_lang)
        if matches:
            return ", ".join(matches)
        return "No Lun Bawang translation found."

    # English <-> Malay
    matches = []
    for lb_word, entry in DATA.items():
        source_value = entry.get(source_lang, "")
        target_value = entry.get(target_lang, "")

        if not source_value or not target_value:
            continue

        if normalize(source_value) == clean:
            matches.append(target_value)
            continue

        if any(normalize(item) == clean for item in split_values(source_value)):
            matches.append(target_value)

    # Remove duplicates while keeping original order.
    unique = list(dict.fromkeys(matches))
    if unique:
        return ", ".join(unique)

    return f"No {LANG_NAMES[target_lang]} translation found."


def build_examples():
    examples = []

    for key in EXAMPLE_KEYS:
        entry = DATA.get(key)
        if not entry:
            continue

        # Keep examples where the JSON contains a multi-word phrase/question.
        examples.append({
            "lun_bawang": key,
            "english": entry.get("english", ""),
            "malay": entry.get("malay", ""),
        })

    return examples


@app.route("/", methods=["GET", "POST"])
def home():
    original_text = ""
    translated_text = ""
    source_lang = "lun_bawang"
    target_lang = "english"

    if request.method == "POST":
        original_text = request.form.get("text", "")
        source_lang = request.form.get("source_lang", "lun_bawang")
        target_lang = request.form.get("target_lang", "english")

        if source_lang not in LANG_NAMES:
            source_lang = "lun_bawang"
        if target_lang not in LANG_NAMES:
            target_lang = "english"

        translated_text = translate(
            original_text,
            source_lang,
            target_lang
        )

    return render_template(
        "index.html",
        original_text=original_text,
        translated_text=translated_text,
        source_lang=source_lang,
        target_lang=target_lang,
        examples=build_examples(),
        word_count=len(DATA),
    )


if __name__ == "__main__":
    app.run(debug=True)
