# Changelog

All notable changes to `innovanote-observability` are documented here.
Format inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Initial library scaffold for InnovaNote observability standardization.
- `logging_config`, `logging_context`, `logging_filters`, `logging_decorators`.
- `error_codes` unified enum + default status/message tables.
- `exceptions` hierarchy (`AppException` and subclasses).
- `log_events` canonical event names.
- `correlation` HTTP + SQS propagation helpers.
- `tracing` AWS X-Ray wrappers (optional dependency).
- `metrics` CloudWatch Embedded Metric Format emitter.
- `middleware_fastapi` request middleware + exception handlers (optional dependency).
- `sqs_helpers` publish/consume with correlation injection (optional dependency).
