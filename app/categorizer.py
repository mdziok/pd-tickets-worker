def categorize_ticket(description: str) -> str:
    description = description.lower()

    categories = {
        "ACCOUNT": ["zalogow", "hasł", "kont", "logowa"],
        "HARDWARE": ["drukark", "komput", "monitor", "mysz", "klawiatur"],
        "SOFTWARE": ["oprogramowan", "aplikacj", "system", "program"],
        "NETWORK": ["sieci", "internet", "router", "wifi", "połączen"],
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in description:
                return category
    return "OTHER"

if __name__ == "__main__":
    print(categorize_ticket("Nie mogę się zalogować"))
    print(categorize_ticket("Zapomniałem hasła"))
    print(categorize_ticket("Moje konto zostało zablokowane"))
    print(categorize_ticket("Drukarka nie działa"))