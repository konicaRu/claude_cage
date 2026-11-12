# Аудит окружения — 2026-11-11

## Итог и Gate

**Gate 0 пройден:** локальная ветка main связана с origin `https://github.com/konicaRu/claude_cage.git`, подготовка отправлена commit `db421e4`, после push рабочее дерево было чистым.

**Gate 1 НЕ пройден:** Windows и ресурсы подходят для заявленной Linux-конфигурации, но обязательный `HypervisorPlatform` выключен. Работа QEMU/WHPX на этом ПК не проверена. Этап 2 не начинался. Никакие системные функции не включались.

## Обнаружено

| Параметр | Фактическое состояние |
|---|---|
| Windows | Windows 10 Pro, 22H2, 10.0.19045.7807, x64 |
| CPU | Intel Core i5-13400, 10 ядер / 16 потоков, AddressWidth 64 |
| RAM | 31,68 GiB физической памяти, видимой ОС |
| Гипервизор | Win32_ComputerSystem.HypervisorPresent = True |
| VBS | VirtualizationBasedSecurityStatus = 2 (работает) |
| CPU CIM-флаги | VirtualizationFirmwareEnabled, VMMonitorModeExtensions, SLAT = False; при активном гипервизоре это не доказательство отключённого VT-x в BIOS |
| Virtual Machine Platform | Включена (Win32_OptionalFeature.InstallState = 1) |
| Windows Hypervisor Platform | **Выключена** (HypervisorPlatform, InstallState = 2) |
| Полный Hyper-V и management tools | Все перечисленные Microsoft-Hyper-V-* выключены (2); vmms не обнаружен |
| WSL | Компонент включён; Ubuntu и docker-desktop зарегистрированы как WSL2, оба Stopped |
| Службы | vmcompute Running; WslService Running; LxssManager Stopped |
| Docker Desktop | 4.45.0 установлен; com.docker.service Stopped |
| VMware / VirtualBox / отдельный QEMU | Не обнаружены в проверенных uninstall-записях, PATH, процессах и службах; произвольные portable-копии/VM-файлы не искались по всему диску |
| Cage | Не обнаружен в uninstall-записях, процессах, стандартных каталогах установки и пользовательском .claude-cage |
| Claude Desktop на host | Appx-пакет Claude 2.42304.2.0; запуск и вход не проверялись |
| Claude Code на host | `claude --version` → 2.1.318, npm launcher |
| Git | 2.53.0.windows.3; clone/commit/push реально выполнены |
| Browser/runtime | Chrome 157.0.8103.50, Edge и WebView2 157.0.4341.42 |
| Прочие инструменты host | Node 22.16.0, npm 10.9.2, Python 3.11.9, winget в PATH |
| VPN | AmneziaVPN 5.0.0.5 установлен, служба Running; наличие активного туннеля/изменённого egress этим не доказано |

Свободное место (GiB):

| Диск | Файловая система | Размер | Свободно |
|---|---|---:|---:|
| C: | NTFS | 953,1 | 455,3 |
| D: | NTFS | 0,1 | 0,1 |
| E: | NTFS | 931,5 | 357,4 |
| F: | NTFS | 930,9 | 584,8 |
| G: | NTFS | 465,8 | 440,1 |
| H: | NTFS | 446,5 | 446,3 |

## Соответствует требованиям

- Cage upstream заявляет Windows 10 22H2 x64; установленная ОС подходит.
- Для будущего Linux guest пересечение поддержки Cage и официального Desktop: Debian 13 x86_64 или Ubuntu 22.04 x86_64. Это кандидаты, выбор ещё не сделан.
- На C: достаточно места для начального Linux-диска Cage с пределом 24 GiB и дополнительных компонентов; будущие рабочие данные потребуют отдельного запаса.
- RAM и CPU дают запас для Linux guest; конкретное распределение ресурсов не задавалось.
- Официальный Claude Desktop для Linux существует в beta; Anthropic поддерживает Ubuntu 22.04+ / Debian 12+, x64/arm64. Установка в guest ещё не выполнялась.

## Потенциальные проблемы

1. **HypervisorPlatform выключен.** Включённый VMP не заменяет WHPX API для QEMU Cage.
2. Последний элемент публичного releases на дату проверки — **v0.1.7-rc.1**, опубликован 2026-11-09, prerelease. Upstream прямо указывает, что hosted Windows/Linux acceptance не запускал VM; работоспособность на нашем host не следует из успешной проверки установщика.
3. CPU CIM-флаги неоднозначны на активном гипервизоре. Не менять BIOS и не отключать VBS/WSL для получения красивых флагов. Требуется фактический тест после отдельно согласованной подготовки.
4. Уже существуют WSL2/Docker/VBS: сохранять их настройки, учесть конкуренцию за RAM/CPU. Доказанного конфликта пока нет.
5. D: всего около 100 MiB. Upstream описывает D:\Cage как возможный default установщика: этот диск **не выбирать** для Cage или VM. Выбрать отдельный каталог на C:/E:/F:/G:/H: после согласования.
6. AmneziaVPN может влиять на host-загрузки и проверку обычного подключения. Сейчас службу, маршруты и proxy не меняли; активность туннеля и Browsec не проверены.
7. `Get-WindowsOptionalFeature -Online` требует административный токен даже вне sandbox. Состояния получены через read-only CIM Win32_OptionalFeature (1 enabled / 2 disabled); pending reboot этим способом не исключён.
8. Это инвентаризация, а не полный поиск всех portable-приложений и образов VM. Host Claude не означает наличия Claude в будущем guest.

## Что потребуется установить/изменить

Только после отдельного подтверждения:

- Подготовить Windows Hypervisor Platform (`HypervisorPlatform`); затем при необходимости перезагрузить и повторить Gate 1. Сейчас НЕ включён.
- После Gate 1 и подтверждения перехода к этапу 2: подписанный Windows x64 Cage из проверенного release, сверка SHA256SUMS/Authenticode, отдельный каталог данных и поддерживаемый Linux guest.
- Desktop, Code, browser и Git внутри guest проверять на их этапах. Наличие на host не заменяет эти проверки.
- Proxy пока не выбирать, не покупать и не настраивать.

Важное расхождение плана с upstream: PLAN.md предполагает запуск guest до настройки proxy (этап 2 перед этапами 3–4), а текущий onboarding Cage просит proxy до начала установки и допуска в workbench. Нужна согласованная поправка последовательности; PLAN.md без согласования не переписан.

## Что менять НЕ требуется

- Не включать полный Hyper-V для выбранной Linux/WHPX-схемы.
- Не включать заново и не удалять существующие VMP/WSL/Docker.
- Не менять VBS, Firewall, DNS, маршруты, системный proxy, VPN и BIOS по результатам этого аудита.
- Не устанавливать на host Go/Node/Docker/Clash ради Cage: upstream описывает комплектный установщик с QEMU, OpenSSH, proxy core и runtime-компонентами. WebView2 уже обнаружен; конкретные runtime проверит будущая установка.
- Не переносить host cookies, ключи, токены и Claude sessions в guest.

## Метод и границы проверки

Read-only: CIM Win32_OperatingSystem/ComputerSystem/Processor/LogicalDisk/OptionalFeature/Service, DeviceGuard, registry Windows version/uninstall, Get-AppxPackage, Get-Service, Get-Command, Get-Process, Get-NetAdapter, `wsl --list --verbose`, версии CLI и Test-Path стандартных Cage-каталогов. VM и WSL-дистрибутивы не запускались. Содержимое credential/config/session файлов не читалось.

Sandbox блокировал CIM и сеть Git; повторные проверки вне sandbox разрешили чтение CIM и Git clone/push. Это не предоставило административного токена DISM. Глобальный safe.directory не менялся; для sandbox Git использован параметр `-c safe.directory=C:/claude_code_projects/claude_cage`.

## Проверенные upstream, 2026-11-11

- [Cage Windows requirements](https://github.com/Lee-xeo/Claude-Cage/blob/main/docs/windows.md), blob `2b655f08bf00a64aed49a0d4b5bb9c5f4ddae410`.
- [Cage installation](https://github.com/Lee-xeo/Claude-Cage/blob/main/docs/guide/installation.md), blob `683f5ac20f77f3636f778a02fa2a0eec64427dde`.
- [Guest systems](https://github.com/Lee-xeo/Claude-Cage/blob/main/docs/guide/guest-systems.md).
- [Release v0.1.7-rc.1 and acceptance limits](https://github.com/Lee-xeo/Claude-Cage/releases/tag/v0.1.7-rc.1).
- [Anthropic Desktop requirements/install](https://support.claude.com/en/articles/10065433-install-claude-desktop).
- [Claude Code requirements](https://code.claude.com/docs/en/setup).
- [Microsoft hypervisor requirements visibility](https://learn.microsoft.com/en-gb/windows-server/virtualization/hyper-v/host-hardware-requirements).
- [Karpathy upstream](https://github.com/multica-ai/andrej-karpathy-skills): старый forrestchang URL перенаправляет сюда; основные локальные принципы совпадают.
- [Superpowers](https://github.com/obra/superpowers) и upstream verification-before-completion проверены; применены установленные навыки для минимального вмешательства и проверки фактов.
- [Matt Pocock skills](https://github.com/mattpocock/skills): каталог проверен; для заданной инвентаризации дополнительный skill не подключался. Спецификация/диагностика понадобятся при согласовании следующего изменения.
- [claude-plugins-official](https://github.com/anthropics/claude-plugins-official): upstream проверен, плагины не устанавливались.
- Новые OpenAI/Codex plugins/skills не использовались и не устанавливались; их подбор отложен по принятому MEMORY. Replica, Humanizer, ub-mode, Playwright не подключались.

## Следующий шаг и остановка

Остановиться до этапа 2. Предложить отдельно согласовать минимальную подготовку HypervisorPlatform и уточнение proxy/onboarding-порядка.

Для будущего подтверждения: включение HypervisorPlatform добавляет WHPX-интерфейс для QEMU, может потребовать перезагрузку и повлиять на сторонние гипервизоры. Существующие WSL/VMP/VBS сохраняются. Откат — отключить только HypervisorPlatform и перезагрузить; существующие VM/данные не удалять. Команды включения/отключения в этой сессии не выполнялись.
## Обновление 2026-11-12 — WHPX включён

С подтверждения пользователя включён только HypervisorPlatform командой Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All -NoRestart через UAC. Результат: exit 0, Online=True, RestartNeeded=False. Повторная независимая проверка Win32_OptionalFeature: InstallState=1 (Enabled). Прежние записи о выключенном WHPX относятся к аудиту 2026-11-11. Перезагрузка не выполнялась и по результату DISM не требуется. Cage и guest ещё не установлены; работоспособность QEMU/WHPX пока не проверена, Gate 1 остаётся открытым.

## Gate 1 — закрыт 2026-11-12

WHPX API доступен: WHvGetCapability вернул HRESULT=0 и HypervisorPresent=True. После проверенной установки Cage 0.1.7 комплектный QEMU успешно инициализирован с -accel whpx: пустая приостановленная VM без диска/сети оставалась запущенной 4 секунды, затем тестовый процесс остановлен. Предупреждения и границы проверки см. docs/cage-install.md. Это закрывает проверку требований хоста; загрузка постоянного Linux guest и повторный запуск относятся к Gate 2 и ещё не проверены.
