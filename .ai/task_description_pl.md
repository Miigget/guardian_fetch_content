# Projekt Streaming Data

**Dla Skills Bootcamp: Absolwenci Software Developer/Coding Skills - Data Engineering**

## Kontekst

Od czasu do czasu Northcoders może chcieć przeszukiwać media w poszukiwaniu istotnych treści. Istotne treści mogą być zapisywane do wykorzystania przez nasze zespoły marketingowe i kariery. Niepotrzebne artykuły byłyby odrzucane.

## Wysokopoziomowy Pożądany Rezultat

Jako proof of concept, zostaniesz poproszony o stworzenie aplikacji do pobierania artykułów z Guardian API i publikowania ich do brokera wiadomości, aby mogły być konsumowane i analizowane przez inne aplikacje.

Narzędzie będzie przyjmować termin wyszukiwania (np. "machine learning"), opcjonalne pole "date_from" oraz referencję do brokera wiadomości. Będzie używać terminów wyszukiwania do przeszukiwania artykułów w Guardian API. Następnie opublikuje szczegóły do dziesięciu trafień do brokera wiadomości.

Na przykład, przy podanych danych wejściowych:
- "machine learning"
- "date_from=2023-01-01"
- "Guardian_content"

Pobierze wszystkie treści zwrócone przez API i opublikuje do dziesięciu najnowszych elementów w formacie JSON na broker wiadomości z ID "guardian_content".

## Założenia i Wymagania Wstępne

1. Dla tego proof of concept będziesz używać tylko darmowego klucza API dostarczonego przez Guardian i przestrzegać związanych z nim limitów szybkości.
2. Biblioteka musi być zdolna do użycia w aplikacjach wdrożonych w AWS.

## Minimalny Wykonalny Produkt

Narzędzie będzie publikować dane do brokera wiadomości w następującym formacie JSON:

```json
{
    "webPublicationDate": "str",
    "webTitle": "str",
    "webUrl": "str"
}
```

Te pola są minimalnie wymagane. Inne mogą być dodane według uznania.

## Wymagania Niefunkcjonalne

- Narzędzie powinno być napisane w Pythonie, być testowane jednostkowo, zgodne z PEP-8 i testowane pod kątem luk bezpieczeństwa.
- Kod powinien zawierać dokumentację.
- Żadne dane uwierzytelniające nie mogą być zapisane w kodzie.
- Całkowity rozmiar modułu nie powinien przekraczać limitów pamięci dla zależności Python Lambda.

## Kryteria Wydajności

Narzędzie nie jest oczekiwane do obsługi więcej niż 50 żądań dziennie do API. Dane nie powinny być przechowywane w brokerze wiadomości dłużej niż trzy dni.

## Możliwe Rozszerzenia

Byłoby pomocne włączenie pola zwanego (na przykład) "content_preview" w wiadomości, które wyświetla pierwsze kilka linii treści artykułu, być może pierwsze 1000 znaków lub tak.

## Niewiążące Sugestie Techniczne

Oczekuje się, że broker wiadomości będzie AWS Kinesis. Jeśli zdecydujesz się użyć alternatywy takiej jak Kafka lub RabbitMQ, będzie musiała być uwzględniona w ramach AWS Free Tier.

Ta aplikacja ma być wdrożona jako komponent w platformie danych. Jednak dla celów demonstracyjnych możesz chcieć móc wywołać ją z lokalnej linii poleceń.

## Termin

Do ustalenia, ale nie później niż cztery tygodnie od rozpoczęcia.
