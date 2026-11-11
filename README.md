# Claude Cage Setup

> Воспроизводимая изолированная среда для Claude Desktop и Claude Code на Windows 10 через Claude Cage и выделенный статический ISP proxy.

## Статус

**Planning / bootstrap.** Архитектура согласована, реализация ещё не подтверждена реальными Gate-проверками.

## Цель

См. [GOAL.md](GOAL.md).

## План

См. [PLAN.md](PLAN.md).

## Принятый процесс разработки

- Язык общения и документации: русский.
- Контекст: `MEMORY.md`, `ARCHITECTURE.md`, `README.md`.
- Git/GitHub: да; push после завершённых проверяемых этапов.
- Karpathy principles: да.
- Superpowers-процесс: да.
- Накопительные правила: нет.
- Humanizer: нет.
- Constitution: да.
- fewer-permission-prompts: отложить до первых 1–2 полноценных сессий.
- Claude official plugins: проверять актуальный upstream перед выбором; устанавливать только по необходимости.
- README: подробный/визуальный.
- architecture-map HTML+JSON: да, но после появления фактической архитектуры.
- ub-mode: нет.
- Playwright: нет на старте.
- OpenAI/Codex plugins/skills: проверять актуальный каталог по мере необходимости; сейчас ничего не устанавливать.
- Matt Pocock Skills: выборочно.
- Replica: нет.

## Skills, которые стоит оценивать по задаче

Из Matt Pocock Skills в первую очередь:
- requirements/grill-me — при неоднозначных требованиях;
- to-spec — для превращения этапа в проверяемую спецификацию;
- implement-spec — для исполнения согласованной спецификации;
- diagnosing-bugs — для Cage/VM/network/proxy проблем;
- code-review — для скриптов и конфигурации;
- handoff — для передачи работы между сессиями.

Перед использованием проверять актуальные upstream README/SKILL.md. Не считать список зафиксированной версией.

## Архитектура

```text
Windows 10
│
├── обычные приложения → обычная сеть
│
└── Claude Cage
    └── Linux guest
        ├── Claude Desktop
        ├── Claude Code
        ├── Browser
        └── Cage/Mihomo
            └── dedicated static ISP SOCKS5
                └── Internet
```

## Безопасность

Репозиторий публичный. Никогда не коммитить:
- proxy credentials;
- Claude/Anthropic tokens;
- cookies/session data;
- API keys;
- SSH/private keys;
- иные секреты.

Конкретные IP при необходимости маскировать в документации.

## Локальный путь

Использовать латинские символы:

```text
C:\claude_code_projects\claude_cage
```

## Следующий шаг

Codex начинает с этапа 0 из `PLAN.md`: клонирование/проверка репозитория, создание контекстных файлов и безопасного `.gitignore`, затем Gate 0.
