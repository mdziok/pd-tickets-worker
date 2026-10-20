# RabbitMQ Worker (Python)

Aplikacja 
* pobiera zgłoszenia w formacie JSON z kolejki RabbitMQ (DONE)
* przetwarza zgłoszenia i nadaje im kategorie (TODO)
* publikuje gotowe zgłoszenia do drugiej kolejki RabbitMQ (albo do REST - TODO)

## Uruchomienie

W katalogu projektu:

```bash
docker compose up --build -d
docker compose logs -f worker
```

Compose uruchamia dwie niezależne instancje RabbitMQ oraz worker.

Interfejsy administracyjne:
- źródłowy: http://localhost:15672
- docelowy: http://localhost:15673

Dane logowania w przykładowym środowisku:
- źródłowy: `user` / `user`
- docelowy: `user` / `user`


## Wysłanie testowej wiadomości

W konsoli RabbitMQ źródłowego:
1. Otwórz `http://localhost:15672` i zaloguj się.
2. Wejdź w Queues and Streams → `incoming`.
3. W sekcji Publish message ustaw payload:

```json
{
  "event_type": "order.created",
  "order_id": 123,
  "amount": 49.99
}
```

4. Kliknij Publish message.
5. Otwórz docelowy panel `http://localhost:15673`, wybierz kolejkę `processed`
   i odczytaj wiadomość w sekcji Get messages.

Oczekiwany wynik ma postać zbliżoną do:

```json
{
  "event_type": "order.created",
  "data": {
    "event_type": "order.created",
    "order_id": 123,
    "amount": 49.99
  },
  "processing": {
    "status": "processed",
    "fields_count": 3,
    "processed_at": "2026-10-20T07:00:00+00:00"
  }
}
```

`processed_at` będzie zawierać rzeczywisty czas przetworzenia.

## Zatrzymanie i usunięcie środowiska

```bash
docker compose down
```

Usunięcie kontenerów wraz z danymi kolejek:

```bash
docker compose down -v
```