# SIPL Conformance Suite

Набір еталонних тестів відповідності, незалежний від конкретної реалізації мови. Скрипт `runner.py` перевіряє будь-який CLI, що підтримує контракт `<cmd> run|semantics|parse FILE --json`.

## Запуск

```bash
python3 conformance/runner.py
python3 conformance/runner.py --cmd "my-sipl"
```

## Формат файлу `cases.json`

Файл містить JSON-масив об'єктів із такими полями:

- `name` — назва тестового випадку.
- `source` — текст програми мовою SIPL.
- `vars` — словник початкових змінних, наприклад `{"X": 2}` (необов'язково).
- `expect.status` — очікуваний результат: `ok`, `syntax_error` або `runtime_error`.
- `expect.state` — очікуваний кінцевий стан пам'яті.
- `expect.error` — очікувані поля помилки (`code`, `line`, `col`).
- `expect.term` — очікуваний семантичний терм (`semantics --json` → `term`).
- `expect.ast` — очікуване AST без `span` (`parse --json` → `ast`).

Коди помилок: `syntax-error`, `undefined-variable`, `division-by-zero`, `step-limit`.