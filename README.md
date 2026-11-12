# Claude Cage Setup

> Воспроизводимая изолированная среда для Claude Desktop и Claude Code на Windows 10 через Claude Cage и выделенный статический ISP proxy.

## Статус

**Этап 2 выполняется.** Gate 0 и Gate 1 пройдены: HypervisorPlatform включён, WHPX API и пробный запуск комплектного QEMU проверены. Cage 0.1.7 установлен на C:. Куплен IPRoyal ISP Dedicated Poland на сутки: веб-тестер SOCKS5 — OK/200, Scamalytics — 0, AbuseIPDB — 0% без жалоб. Linux guest и маршрут Cage ещё не проверены. См. [аудит окружения](docs/environment-audit.md), [установку Cage](docs/cage-install.md) и [результаты / инструкцию проверки прокси](docs/proxy-validation.md).

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

Проверить первый экран Cage вручную, подтвердить принятие проверенного IP и настроить SOCKS5 локально. В onboarding сначала выбираются система и отдельный каталог данных, затем применяется прокси и только потом создаётся guest. Проверить egress, DNS и отказ прокси; Gate 2 закрывается после повторного запуска guest без ошибок. Суточный заказ продлить до истечения, если решено сохранить IP.
