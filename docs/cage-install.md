# Установка Cage — 2026-11-12

## Результат

Cage 0.1.7 установлен в `C:\Users\w-w3\AppData\Local\Programs\Cage`. Установщик завершился с кодом 0; версия Cage.exe и HKCU uninstall-запись подтверждают 0.1.7. Приложение запущено, процессы отвечают. Первый экран визуально не проверен: Computer Use после повторной попытки и сброса сообщает `native pipe unavailable`.

**Gate 1 пройден:** требования хоста из предыдущего аудита дополнены включённым HypervisorPlatform и фактической проверкой WHPX. **Gate 2 не пройден:** постоянный Linux guest ещё не создан.

## Источник и проверка

- [Официальный стабильный релиз v0.1.7](https://github.com/Lee-xeo/Claude-Cage/releases/tag/v0.1.7), опубликован 2026-11-11, commit `9ade09f52981262916aacf404de34b018b602942`.
- Файл: `Cage-0.1.7-windows-amd64-setup.exe`, 483673728 байт.
- SHA256: `e1bfd27bf46f0d46bf4d4edd006fbc6ba4bbb8a71d4394f73b427d37ca2c0b5d`. Совпадает с опубликованным SHA256SUMS и digest release asset.
- Authenticode: Valid; signer `CN=LI SHI HAO, O=LI SHI HAO, L=Shanghai, C=CN`.
- Установщик и SHA256SUMS сохранены в игнорируемой `tmp/cage-install/`.
- [Исходный NSIS установщик](https://github.com/Lee-xeo/Claude-Cage/blob/v0.1.7/packaging/windows/Cage.nsi): пользовательская установка, явный каталог C: задан через `/D=`, тихий режим `/S`.

## Проверка WHPX

`WHvGetCapability(HypervisorPresent)` из WinHvPlatform.dll вернул HRESULT=0, True, 4 байта.

Комплектный `qemu-system-x86_64.exe` запущен с `-accel whpx -machine q35 -m 256 -nodefaults -display none -serial none -monitor none -nic none -S`. Через 4 секунды процесс продолжал работать и был остановлен. Диска, сети и постоянных данных у тестовой VM не было. Это проверка инициализации ускорителя, а не загрузки Linux.

Предупреждения: `Failed to get performance monitoring features, hr=80370300`; отсутствует CPU feature SVM. Раннего завершения процесса не было. При проблемах с постоянной VM учитывать эти сообщения.

## Следующий шаг

По [инструкции v0.1.7](https://github.com/Lee-xeo/Claude-Cage/blob/v0.1.7/docs/guide/installation.md) onboarding требует: система и отдельный каталог данных → прокси → установка guest → проверки → workbench. Проверку и настройку прокси из этапов 3–4 нужно выполнить до завершения этапа 2; критерии Gate 2–4 сохраняются. PLAN.md пока не переписан.

Для guest выбрать Debian 13 x86_64, отдельный пустой NTFS-каталог на C: вне репозитория и каталога приложения. Каталог ещё не создан и в Cage не выбран. D: не использовать. Секреты вводит пользователь локально. Claude-авторизация и изменения глобальной Git-защиты не выполнялись.
