# Claude Cage Setup

> Воспроизводимая изолированная среда для Claude Desktop и Claude Code на Windows 10 через Claude Cage и выделенный статический ISP proxy.

## Статус

**Обновление 2026-11-17:** выбран новый прокси США **US ISP**, SOCKS5, порт **12324** (исправлен ошибочный 12323). Проверка выхода Cage показала United States / New York City; браузер Cage и терминал Linux подтвердили одинаковый ожидаемый IP. Claude Desktop/Code через новый узел, отказ нового прокси и cold start ещё не проверены. Подробности — в [MEMORY.md](MEMORY.md).

**Этап 2 выполняется.** Gate 0 и Gate 1 пройдены: HypervisorPlatform включён, WHPX API и пробный запуск комплектного QEMU проверены. Cage 0.1.7 установлен на C:. Куплен IPRoyal ISP Dedicated Poland на сутки: веб-тестер SOCKS5 — OK/200, Scamalytics — 0, AbuseIPDB — 0% без жалоб. Debian 13 установлен, IP браузера и терминала совпал с прокси. Claude Desktop 5.1231.2 авторизован и ответил на тестовое сообщение. Сохранение сессии, Claude Code и cold start ещё не проверены. См. [аудит окружения](docs/environment-audit.md), [установку Cage](docs/cage-install.md) и [результаты / инструкцию проверки прокси](docs/proxy-validation.md).

## Микрофон в Claude Desktop

Realtek USB2.0 Audio автоматически подключается после запуска Cage и готовности Linux. Управляйте диктовкой кнопкой в Claude; отдельные команды не нужны. Если Claude не увидел устройство, перезапустите только Claude Desktop. Пока мост работает, захват Realtek постоянный; записи на диск нет. [Подробная инструкция](docs/microphone-bridge.md).

## VS Code через Cage

Подключение **Cage** настроено через Microsoft Remote SSH; VS Code Server и расширение Claude Code установлены внутри Linux. Открыть: запустить Cage → в VS Code `Ctrl+Shift+P` → `Remote-SSH: Connect to Host…` → `Cage`. Тест чата отложен: текущему аккаунту требуется подходящая подписка. Порт SSH и ключ хоста после перезапуска VM обновляет `scripts\sync-cage-ssh.ps1` (запуск вручную; автозапуск написан, но не установлен). [Результаты и инструкция](docs/vscode-cage.md).

## Цель проекта

См. [GOAL.md](GOAL.md).

## План

См. [PLAN.md](PLAN.md).

## Принятый процесс разработки

- Язык общения и документации: русский.
- Контекст: `MEMORY.md`, `ARCHITECTURE.md`, `README.md`.
- Git/GitHub: да; push после завершённых проверяемых этапов.
- По команде «пуш коммит» сначала заполнять `MEMORY.md` контекстом прошедшей работы, затем выполнять commit/push. Подробности — в [AGENTS.md](AGENTS.md).
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


## Одна папка в двух окнах VS Code

- Для Codex откройте `%USERPROFILE%\.claude-cage-workspace` в обычном окне VS Code.
- Для Claude Code откройте `/c/Users/<Windows user>/.claude-cage-workspace` в окне `SSH: Cage`. Вставьте фактическое имя пользователя Windows вместо `<Windows user>`.
- Папку можно открыть сразу из PowerShell командой `code --new-window --remote ssh-remote+Cage /c/Users/<Windows user>/.claude-cage-workspace/`, заключив Linux-путь в кавычки. При запросе платформы выберите Linux.
- Для отдельного проекта добавьте имя его подпапки к обоим путям и откройте их в соответствующих окнах VS Code. Если диалог Cage выдаёт ошибку при добавлении подпапки, она всё равно может быть доступна через уже подключённую общую папку.
- Для графического выбора в Cage 0.1.7 используйте каталог проекта вне уже подключённой общей папки, например `%USERPROFILE%\CageProjects\my-project`. Этот вариант ещё предстоит проверить в графическом диалоге.
- В Linux Cage настроен пользовательский звук завершения Claude Code. Хук `Stop` запускает `sheep.mp3` с задержкой 1,5 секунды. Выполнение команды проверено, срабатывание после реального ответа ещё предстоит проверить.
- Если удалённое окно показывает тайм-аут, закройте лишние окна и повторите подключение. Результат виден в панели вывода **Remote - SSH**. См. [настройку подключения](docs/vscode-cage.md).
