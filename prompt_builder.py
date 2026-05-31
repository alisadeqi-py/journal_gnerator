from string import Template
from pathlib import Path


def build_prompt(place_name: str, location: str, about_char_limit: int) -> str:
    # خواندن فایل پرامپت از پوشه prompts
    prompt_file = Path("prompts/tourism_prompt.txt")
    template_text = prompt_file.read_text(encoding="utf-8")

    template = Template(template_text)
    print('template of the built prompt', template)
    return template.substitute(
        place_name=place_name, location=location, about_char_limit=about_char_limit
    )
