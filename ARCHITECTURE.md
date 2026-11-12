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

### 2026-11-11 — фактическое состояние после аудита
- Host: Windows 10 Pro 22H2 x64; существующие WSL2/Docker/VBS сохранены.
- Cage не обнаружен. Linux guest ещё не создан. Host Desktop/Code уже присутствуют.
- Для Linux Cage нужен QEMU/WHPX: HypervisorPlatform выключен, Gate 1 не пройден.
- Полный Hyper-V для Linux-схемы не требуется; VMP не заменяет HypervisorPlatform.
- Добавлен docs/environment-audit.md с фактами, upstream и ограничениями проверки.
- Требуется согласование порядка proxy/onboarding до установки; архитектура остаётся целевой.

### 2026-11-12 — Cage установлен, WHPX проверен

- HypervisorPlatform включён; DISM не потребовал перезагрузку.
- WHPX API и пустая тестовая QEMU VM проверены; Gate 1 закрыт.
- Cage 0.1.7 установлен на C: в пользовательском Programs\Cage.
- Постоянного Linux guest и настроенного proxy ещё нет; Gate 2 открыт.
- Подробности и ограничения: docs/cage-install.md.

### 2026-11-12 — выделенный прокси приобретён, проверена репутация

- IPRoyal ISP Dedicated, Poland, 1 IP на 24 часа, Premium / Scamalytics; SOCKS5 12324.
- На скриншотах пользователя: Proxy Tester OK/200, Scamalytics 0, AbuseIPDB 0% без жалоб; AS35179 / Korbank S. A., organization Hosting RS, Wroclaw.
- Проверки выполнены веб-сервисами; подключение с ПК и маршрутизация Cage ещё не подтверждены. Целевая схема пока не реализована полностью.
- Результаты и повторяемая инструкция: docs/proxy-validation.md. Секреты и исходные скриншоты в Git не сохранялись.
