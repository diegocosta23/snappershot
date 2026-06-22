from __future__ import annotations

from ..models.company import Company


class CompanyService:
    """
    Hanterar sökning och uppslag av företag.
    """

    def __init__(self) -> None:
        self._companies = [
            Company("Investor", "INVE B"),
            Company("Volvo", "VOLV B"),
            Company("Evolution", "EVO"),
            Company("Atlas Copco", "ATCO A"),
            Company("Atlas Copco B", "ATCO B"),
            Company("ABB", "ABB"),
            Company("Hexagon", "HEXA B"),
            Company("Saab", "SAAB B"),
            Company("Ericsson", "ERIC B"),
            Company("Swedbank", "SWED A"),
            Company("SEB", "SEB A"),
            Company("Handelsbanken", "SHB A"),
            Company("Nordea", "NDA SE"),
            Company("Boliden", "BOL"),
            Company("Securitas", "SECU B"),
            Company("Assa Abloy", "ASSA B"),
            Company("AstraZeneca", "AZN"),
        ]

    def search(self, text: str) -> list[Company]:
        """
        Söker företag efter namn eller ticker.
        """

        text = text.lower().strip()

        return [
            company
            for company in self._companies
            if text in company.name.lower()
            or text in company.ticker.lower()
        ]


if __name__ == "__main__":

    service = CompanyService()

    while True:

        query = input("\nSök företag (Enter för att avsluta): ").strip()

        if not query:
            break

        results = service.search(query)

        if not results:
            print("Inga träffar.")
            continue

        print()

        for company in results:
            print(f"{company.name} ({company.ticker})")