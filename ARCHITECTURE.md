# ARCHITECTURE

## Назначение

Изолированная среда Claude Desktop + Claude Code на Windows 10 через Claude Cage и dedicated static ISP SOCKS5 без системного VPN Windows.

## Текущая целевая схема

```text
Windows 10 host
└── Claude Cage
    └── Linux guest
        ├── Claude Desktop
        ├── Claude Code
        ├── Browser
        └── Cage/Mihomo
            └── dedicated static ISP SOCKS5
                └── Internet
```

Схема пока целевая, а не полностью подтверждённая. По мере Gate-проверок заменять предположения фактическими данными.

## Структура репозитория

- `GOAL.md` — цель и acceptance criteria.
- `PLAN.md` — staged implementation plan.
- `README.md` — входная инструкция и статус.
- `MEMORY.md` — журнал сессий и открытые вопросы.
- `ARCHITECTURE.md` — фактическая архитектура и changelog.
- `docs/constitution.md` — инварианты проекта.
- `docs/` — результаты аудитов и Gate-проверок.

## Команды

Будут добавляться только после фактической проверки в соответствующей среде.

## Changelog

### 2026-11-11
- Зафиксирована целевая архитектура.
- Завершён project-starter checklist.
- Выбраны Karpathy principles, Superpowers, Constitution и выборочные Matt Pocock Skills.
- Replica, Humanizer, ub-mode и Playwright на старте отклонены.

### 2026-11-11 — этап 0
- Локальная копия связана с origin konicaRu/claude_cage, ветка main.
- Сохранён project-starter.md, дополнены исключения приватных данных/образов VM.
- Среда Cage ещё не установлена; схема остаётся целевой.
