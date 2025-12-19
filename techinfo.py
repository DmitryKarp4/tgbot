from log_event import log_event
from config import SHODAN_TOKEN
import shodan
import requests

def shodan_info(ip: str, user_id: int) -> str:
    log_event(f"Shodan-запрос от пользователя {user_id} для IP {ip}")
    api = shodan.Shodan(SHODAN_TOKEN)
    try:
        host = api.host(ip)
    except shodan.APIError as e:
        if "403" in str(e):
            log_event(f"Ошибка Shodan API для пользователя {user_id}: {e}")
            return "Ошибка Shodan API: Доступ к этому IP ограничен Shodan."
        else:
            log_event(f"Ошибка Shodan API для пользователя {user_id}: {e}")
            return f"Ошибка Shodan API: {e}"
    except Exception as e:
        log_event(f"Общая ошибка при запросе Shodan для пользователя {user_id}: {e}")
        return f"Произошла ошибка при получении данных с Shodan: {e}"

    lines = []

    # ===== БАЗОВАЯ ИНФОРМАЦИЯ =====
    lines.append("Shodan report")
    lines.append(f"IP: {host.get('ip_str', 'N/A')}")
    lines.append(f"Country: {host.get('country_name', 'N/A')}")
    lines.append(f"City: {host.get('city', 'N/A')}")
    lines.append(f"ASN: {host.get('asn', 'N/A')}")
    lines.append(f"Org: {host.get('org', 'N/A')}")
    lines.append(f"OS: {host.get('os', 'N/A')}")
    lines.append(f"CVE: {', '.join(host.get('vulns', [])) if host.get('vulns') else 'N/A'}")
    lines.append(f"Tags : " + (', '.join(host.get('tags', [])) if host.get('tags') else 'N/A'))
    lines.append(f"Last Seen: {host.get('last_seen', 'N/A')}") 
    lines.append("")  # Пустая строка для разделения секций

    # ===== ПОРТЫ И СЕРВИСЫ =====
    lines.append("Open ports:")

    for entry in host.get('data', []):
        port = entry.get('port', 'N/A')
        transport = entry.get('transport', 'tcp')
        product = entry.get('product', '')
        version = entry.get('version', '')

        service = f"- {port}/{transport}"
        if product:
            service += f" | {product}"
        if version:
            service += f" {version}"

        # HTTP доп. инфа
        if 'http' in entry:
            http = entry['http']
            title = http.get('title')
            server = http.get('server')
            if title:
                service += f" | title: {title}"
            if server:
                service += f" | server: {server}"

        # SSL инфа
        if 'ssl' in entry:
            ssl = entry['ssl']
            cn = ssl.get('cert', {}).get('subject', {}).get('CN')
            if cn:
                service += f" | SSL CN: {cn}"

        lines.append(service)

    result = "\n".join(lines)
    log_event(f"Shodan-запрос от пользователя {user_id} для IP {ip} завершен.")
    return result

def crtsh_info(ip: str, user_id: int) -> str:
    log_event(f"crt.sh-запрос от пользователя {user_id} для IP {ip}")
    
    url = "https://crt.sh/"
    params = {"q": ip, "output": "json"}
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            log_event(f"Ошибка crt.sh для пользователя {user_id}: HTTP {r.status_code}")
            return f"Ошибка crt.sh: HTTP {r.status_code}"
        data = r.json()
    except Exception as e:
        log_event(f"Общая ошибка при запросе crt.sh для пользователя {user_id}: {e}")
        return f"Произошла ошибка при получении данных с crt.sh: {e}"
    
    if not data:
        log_event(f"crt.sh-запрос от пользователя {user_id} для IP {ip} не нашел данных.")
        return "crt.sh не нашел данных для этого IP-адреса."
    
    domains = set()

    for entry in data:
        name_value = entry.get("common_name", "")
        for name in name_value.split("\n"):
            name = name.strip().lower()
            if name:
                domains.add(name)

    if not domains:
        log_event(f"crt.sh-запрос от пользователя {user_id} для IP {ip} не нашел доменов.")
        return "crt.sh: домены не найдены"
    
    result = "crt.sh найденные домены:\n" + "\n".join(sorted(domains))
    log_event(f"crt.sh-запрос от пользователя {user_id} для IP {ip} завершен.")

    return result


def techinfo(ip: str, user_id: int) -> str:
    shodan_data = shodan_info(ip, user_id)
    crtsh_data = crtsh_info(ip, user_id)
    return f"{shodan_data}\n\n{crtsh_data}\n"