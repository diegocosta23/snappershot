from __future__ import annotations

from ..models.company import Company


class CompanyService:
    """
    Laddar och söker bolag.
    """

    def __init__(self) -> None:

        self._companies = [
            Company("Investor B", "INVE B"),
            Company("Investor A", "INVE A"),
            Company("Swedbank A", "SWED A"),
            Company("Sandvik", "SAND"),
            Company("Lifco B", "LIFCO B"),
            Company("Ratos B", "RATO B"),
            Company("ABB", "ABB"),
            Company("Atlas Copco A", "ATCO A"),
            Company("Atlas Copco B", "ATCO B"),
            Company("Volvo B", "VOLV B"),
            Company("SEB A", "SEB A"),
            Company("Handelsbanken A", "SHB A"),
            Company("Handelsbanken B", "SHB B"),
            Company("Evolution", "EVO"),
            Company("Ericsson B", "ERIC B"),
            Company("Saab B", "SAAB B"),
            Company("Nibe B", "NIBE B"),
            Company("Assa Abloy B", "ASSA B"),
            Company("Hexagon", "HEXA B"),
        ]

    @staticmethod
    def _normalize(text: str) -> str:

        return "".join(
            char
            for char in text.lower()
            if char.isalnum()
        )

    def search(self, text: str) -> list[Company]:
        """
        Returnerar alla matchande bolag.
        """

        query = self._normalize(text)

        if not query:
            return list(self._companies)

        matches: list[tuple[int, int, Company]] = []

        for index, company in enumerate(self._companies):

            name = self._normalize(company.name)
            ticker = self._normalize(company.ticker)

            if query == name or query == ticker:
                score = 0

            elif name.startswith(query) or ticker.startswith(query):
                score = 1

            elif query in name or query in ticker:
                score = 2

            else:
                continue

            matches.append((score, index, company))

        matches.sort(key=lambda item: (item[0], item[1]))

        return [company for _, _, company in matches]

    def find(self, text: str) -> Company | None:
        """
        Returnerar bästa träffen.
        """

        results = self.search(text)

        if not results:
            return None

        return results[0]


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