from string import Template
from pathlib import Path


def _build_access_routes_block(cities: list) -> str:
    if not cities:
        return ('[\n\n{\n\n"from": "شهر مبدا",\n\n'
                '"by_car": "فاصله زمانی با ماشین",\n\n'
                '"by_train": "فاصله زمانی با قطار",\n\n'
                '"by_bus": "فاصله زمانی با اتوبوس",\n\n'
                '"by_airplan": "فاصله زمانی با هواپیما"\n\n}\n\n]')

    entries = []
    for city in cities:
        entries.append(
            f'{{\n\n"from": "{city}",\n\n'
            '"by_car": "فاصله زمانی با ماشین",\n\n'
            '"by_train": "فاصله زمانی با قطار",\n\n'
            '"by_bus": "فاصله زمانی با اتوبوس",\n\n'
            '"by_airplan": "فاصله زمانی با هواپیما"\n\n}}'
        )
    return '[\n\n' + ',\n\n'.join(entries) + '\n\n]'


def build_prompt(place_name: str, location: str, about_char_limit: int, access_routes_cities: list = None) -> str:
    prompt_file = Path("prompts/tourism_prompt.txt")
    template_text = prompt_file.read_text(encoding="utf-8")

    template = Template(template_text)
    final_temp = template.substitute(
        place_name=place_name,
        location=location,
        about_lines_limit=about_char_limit,
        access_routes_template=_build_access_routes_block(access_routes_cities or [])
    )
    return final_temp