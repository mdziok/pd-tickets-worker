# RabbitMQ Worker (Python)

Aplikacja 
* pobiera zgłoszenia w formacie JSON z kolejki RabbitMQ (DONE - ustalic tylko schemat zgłoszenia)
* przetwarza zgłoszenia i nadaje im kategorie (TODO)
* publikuje gotowe zgłoszenia do drugiej kolejki RabbitMQ (albo do REST - TODO)

## Uruchomienie samego workera

W katalogu projektu:

```bash
docker compose up --build -d
docker compose logs -f worker
```

Compose uruchamia RabbitMQ oraz worker.

Interfejsy administracyjne:
- rabbitmq: http://localhost:15672

Dane logowania w przykładowym środowisku:
- rabbitmq: `user` / `user`


## Wysłanie testowej wiadomości

1. Otwórz `http://localhost:15672` i zaloguj się.
2. Wejdź w `Queues and Streams` → `incoming`.
3. W sekcji `Publish message` ustaw payload:

```json
{
  "message": "Przykładowa treść wiadomości",
  "user": "user",
  "send_time": "2026-10-20T07:00:00+00:00"
}
```

4. Kliknij `Publish message`.
5. Wybierz kolejkę `processed` i odczytaj wiadomość w sekcji `Get messages`.


## Zatrzymanie i usunięcie środowiska

```bash
docker compose down
```

Usunięcie kontenerów wraz z danymi kolejek:

```bash
docker compose down -v
```

Można też ręcznie usunąć dane z kolejek:  `Queues and Streams` → `incoming` \ `processed` →  `Purge messages` 