# Security notes

Launch Preflight Checker принимает пользовательский URL и делает серверные HTTP-запросы, поэтому основной риск — SSRF.

Реализовано:

- разрешены только `http` / `https`;
- URL с credentials отклоняются;
- localhost, private, link-local, loopback и reserved IP отклоняются;
- каждый redirect target валидируется повторно;
- ограничено число redirect hops;
- установлен timeout;
- HTML ограничен 2 MB;
- число проверяемых ссылок ограничено 30;
- link-checking работает best-effort и не выполняет JavaScript;
- сервер не отправляет формы и не выполняет пользовательские действия на проверяемом сайте.

Ограничение: как и для любого DNS-based SSRF guard, production-версия для недоверенного публичного доступа должна дополнительно использовать сетевую изоляцию / egress policy, чтобы закрыть классы DNS-rebinding и инфраструктурных edge cases на уровне сети.
