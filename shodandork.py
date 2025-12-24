from log_event import log_event
import urllib.parse

def shodan_dork_parser(dork: str, user_id: int) -> dict:
    log_event(f"Shodan dork от пользователя {user_id}: {dork}")

    parts = dork.split()
    args = {}

    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            args[key.lower()] = value

    if not args:
        return {"error": "Не удалось распознать аргументы. Используйте формат key=value"}

    log_event(f"Shodan dork аргументы от {user_id}: {args}")
    return args

def build_shodan_dork(args: dict, user_id: int) -> str:
    if "error" in args:
        return ""

    mapping = {
        "ip": "ip",
        "port": "port",
        "service": "service",
        "product": "product",
        "country": "country",
        "asn": "asn",
        "org": "org",
        "title": "title",
        "hostname": "hostname",
    }

    dork_parts = []

    for key, value in args.items():
        if key in mapping:
            dork_parts.append(f'{mapping[key]}:"{value}"')

    dork_query = " ".join(dork_parts)
    log_event(f"Построен Shodan dork для {user_id}: {dork_query}")

    return dork_query

def shodan_dork_search(dork: str, user_id) -> str:
    args = shodan_dork_parser(dork, user_id)

    if "error" in args:
        return args["error"]

    dork_string = build_shodan_dork(args, user_id)

    shodan_url = (
        "https://www.shodan.io/search?query="
        + urllib.parse.quote(dork_string)
    )

    report = (
        "Shodan Dork Builder\n\n"
        f"Сформированный запрос:\n"
        f"{dork_string}\n\n"
        f"Открыть в Shodan:\n"
        f"{shodan_url}"
    )

    log_event(f"User {user_id} создал Dork: {dork_string}")
    return report
