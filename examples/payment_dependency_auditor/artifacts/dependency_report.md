# Payment Infrastructure Dependency Report

Generated: 2026-09-09T05:43:12.067382
Files analyzed: 15
Lines analyzed: 1405
Total observations: 105

## Summary

- Total dependency edges: 105
- Documented dependencies: 25
- Documentation drift items: 130

## Dependency Status

| Source | Target | Type | Epistemic State | Proposition |
|--------|--------|------|-----------------|-------------|
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-redis.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 6379 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | https://api.stripe.com | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | http://fraud-ml-model:8080 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/staging.yaml | http://feature-flags:8080 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-checkout-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-payments-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-redis.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 6379 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | https://api.stripe.com | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-ledger-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-refunds-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | http://fraud-ml-model:8080 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | prod-reconciliation-db.internal | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | http://feature-flags:8080 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/config/production.yaml | http://tax-service:8080 | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | psycopg2 | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | datetime | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | database | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | PAYMENT_PROVIDER_KEY | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | http://ledger:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | http://payments:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | json | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | psycopg2 | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | datetime | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | database | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | REDIS_URL | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | PAYMENT_PROVIDER_KEY | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://ledger:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://fraud:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://customer-profile:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://feature-flags:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://tax-service:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | psycopg2 | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | datetime | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | database | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | REDIS_URL | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | http://fraud-ml-model:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | psycopg2 | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | database | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | CHECKOUT_DATABASE_URL | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://payments:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://customer-profile:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://feature-flags:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://fraud:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | psycopg2 | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | dataclasses | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | datetime | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | database | database | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://payments:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://ledger:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://customer-profile:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://feature-flags:8080 | network | observed | runtime_dependency |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | os | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | httpx | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | __future__ | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | typing | import | observed | static_reference |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | SENDGRID_API_KEY | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | TWILIO_ACCOUNT_SID | configuration | observed | configuration_dependency |
| examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | TWILIO_AUTH_TOKEN | configuration | observed | configuration_dependency |

## Documentation Drift

| Type | Source | Target | Description | Severity |
|------|--------|--------|-------------|----------|
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-redis.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-redis.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 6379 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 6379 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | https://api.stripe.com | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → https://api.stripe.com not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | http://fraud-ml-model:8080 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → http://fraud-ml-model:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | staging-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/staging.yaml | http://feature-flags:8080 | Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → http://feature-flags:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-checkout-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-checkout-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-payments-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-payments-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-redis.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-redis.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 6379 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 6379 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | https://api.stripe.com | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → https://api.stripe.com not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-ledger-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-ledger-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-refunds-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-refunds-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | http://fraud-ml-model:8080 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://fraud-ml-model:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | prod-reconciliation-db.internal | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-reconciliation-db.internal not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | 5432 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | http://feature-flags:8080 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://feature-flags:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/config/production.yaml | http://tax-service:8080 | Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://tax-service:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | psycopg2 | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → psycopg2 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | datetime | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → datetime not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | database | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → database not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | PAYMENT_PROVIDER_KEY | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → PAYMENT_PROVIDER_KEY not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | http://ledger:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://ledger:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py | http://payments:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://payments:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | json | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → json not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | psycopg2 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → psycopg2 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | datetime | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → datetime not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | database | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → database not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | redis | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | REDIS_URL | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → REDIS_URL not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | PAYMENT_PROVIDER_KEY | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → PAYMENT_PROVIDER_KEY not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://ledger:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://ledger:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://fraud:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://fraud:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://customer-profile:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://customer-profile:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://feature-flags:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://feature-flags:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/payments/payments.py | http://tax-service:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://tax-service:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | psycopg2 | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → psycopg2 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | datetime | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → datetime not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/ledger/ledger.py | database | Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → database not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | REDIS_URL | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → REDIS_URL not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/fraud/fraud.py | http://fraud-ml-model:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → http://fraud-ml-model:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | psycopg2 | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → psycopg2 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | database | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → database not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | CHECKOUT_DATABASE_URL | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → CHECKOUT_DATABASE_URL not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://payments:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://payments:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://customer-profile:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://customer-profile:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://feature-flags:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://feature-flags:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/checkout/checkout.py | http://fraud:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://fraud:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | psycopg2 | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → psycopg2 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | dataclasses | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → dataclasses not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | datetime | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → datetime not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | database | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → database not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://payments:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://payments:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://ledger:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://ledger:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://customer-profile:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://customer-profile:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/refunds/refunds.py | http://feature-flags:8080 | Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://feature-flags:8080 not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | os | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → os not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | httpx | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → httpx not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | __future__ | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → __future__ not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | typing | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → typing not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | SENDGRID_API_KEY | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → SENDGRID_API_KEY not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | TWILIO_ACCOUNT_SID | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_ACCOUNT_SID not documented | medium |
| undiscovered | examples/payment_dependency_auditor/fixture/services/notifications/notifications.py | TWILIO_AUTH_TOKEN | Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_AUTH_TOKEN not documented | medium |
| documented_removed | examples/payment_dependency_auditor/fixture/config/staging.yaml | payments | Documented dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → payments not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/staging.yaml | ledger | Documented dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → ledger not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/staging.yaml | payments | Documented dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → payments not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/staging.yaml | ledger | Documented dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → ledger not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/production.yaml | payments | Documented dependency examples/payment_dependency_auditor/fixture/config/production.yaml → payments not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/production.yaml | ledger | Documented dependency examples/payment_dependency_auditor/fixture/config/production.yaml → ledger not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/production.yaml | payments | Documented dependency examples/payment_dependency_auditor/fixture/config/production.yaml → payments not found in code | low |
| documented_removed | examples/payment_dependency_auditor/fixture/config/production.yaml | ledger | Documented dependency examples/payment_dependency_auditor/fixture/config/production.yaml → ledger not found in code | low |
| documented_removed | unknown | payments service | Documented dependency unknown → payments service not found in code | low |
| documented_removed | unknown | ledger service | Documented dependency unknown → ledger service not found in code | low |
| documented_removed | unknown | fraud service | Documented dependency unknown → fraud service not found in code | low |
| documented_removed | unknown | payments service | Documented dependency unknown → payments service not found in code | low |
| documented_removed | unknown | ledger service | Documented dependency unknown → ledger service not found in code | low |
| documented_removed | unknown | ledger service | Documented dependency unknown → ledger service not found in code | low |
| documented_removed | unknown | payments service | Documented dependency unknown → payments service not found in code | low |
| documented_removed | customer | checkout | Documented dependency customer → checkout not found in code | low |
| documented_removed | payments | ledger | Documented dependency payments → ledger not found in code | low |
| documented_removed | refunds | payments | Documented dependency refunds → payments not found in code | low |
| documented_removed | checkout | payments | Documented dependency checkout → payments not found in code | low |
| documented_removed | payments | ledger | Documented dependency payments → ledger not found in code | low |
| documented_removed | refunds | payments | Documented dependency refunds → payments not found in code | low |
| documented_removed | reconciliation | ledger | Documented dependency reconciliation → ledger not found in code | low |
| documented_removed | payments | customer | Documented dependency payments → customer not found in code | low |
| documented_removed | payments | feature | Documented dependency payments → feature not found in code | low |
| documented_removed | payments | external | Documented dependency payments → external not found in code | low |

## Key Findings

### Undocumented Dependencies

The following dependencies were observed in code but not documented:

- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-redis.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-redis.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 6379**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 6379 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → https://api.stripe.com**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → https://api.stripe.com not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → http://fraud-ml-model:8080**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → http://fraud-ml-model:8080 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → staging-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/staging.yaml → http://feature-flags:8080**: Observed dependency examples/payment_dependency_auditor/fixture/config/staging.yaml → http://feature-flags:8080 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-checkout-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-checkout-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-payments-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-payments-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-redis.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-redis.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 6379**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 6379 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → https://api.stripe.com**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → https://api.stripe.com not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-ledger-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-ledger-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-refunds-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-refunds-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → http://fraud-ml-model:8080**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://fraud-ml-model:8080 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → prod-reconciliation-db.internal**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → prod-reconciliation-db.internal not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → 5432**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → 5432 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → http://feature-flags:8080**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://feature-flags:8080 not documented
- **examples/payment_dependency_auditor/fixture/config/production.yaml → http://tax-service:8080**: Observed dependency examples/payment_dependency_auditor/fixture/config/production.yaml → http://tax-service:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → psycopg2**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → psycopg2 not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → datetime**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → datetime not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → database**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → database not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → PAYMENT_PROVIDER_KEY**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → PAYMENT_PROVIDER_KEY not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://ledger:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://ledger:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://payments:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/reconciliation/reconciliation.py → http://payments:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → json**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → json not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → psycopg2**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → psycopg2 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → datetime**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → datetime not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → database**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → database not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → redis not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → REDIS_URL**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → REDIS_URL not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → PAYMENT_PROVIDER_KEY**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → PAYMENT_PROVIDER_KEY not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://ledger:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://ledger:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://fraud:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://fraud:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://customer-profile:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://customer-profile:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://feature-flags:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://feature-flags:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://tax-service:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/payments/payments.py → http://tax-service:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → psycopg2**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → psycopg2 not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → datetime**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → datetime not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → database**: Observed dependency examples/payment_dependency_auditor/fixture/services/ledger/ledger.py → database not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → REDIS_URL**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → REDIS_URL not documented
- **examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → http://fraud-ml-model:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/fraud/fraud.py → http://fraud-ml-model:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → psycopg2**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → psycopg2 not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → database**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → database not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → CHECKOUT_DATABASE_URL**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → CHECKOUT_DATABASE_URL not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://payments:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://payments:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://customer-profile:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://customer-profile:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://feature-flags:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://feature-flags:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://fraud:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/checkout/checkout.py → http://fraud:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → psycopg2**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → psycopg2 not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → dataclasses**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → dataclasses not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → datetime**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → datetime not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → database**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → database not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://payments:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://payments:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://ledger:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://ledger:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://customer-profile:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://customer-profile:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://feature-flags:8080**: Observed dependency examples/payment_dependency_auditor/fixture/services/refunds/refunds.py → http://feature-flags:8080 not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → os**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → os not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → httpx**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → httpx not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → __future__**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → __future__ not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → typing**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → typing not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → SENDGRID_API_KEY**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → SENDGRID_API_KEY not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_ACCOUNT_SID**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_ACCOUNT_SID not documented
- **examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_AUTH_TOKEN**: Observed dependency examples/payment_dependency_auditor/fixture/services/notifications/notifications.py → TWILIO_AUTH_TOKEN not documented

### Epistemic State Distribution

- observed: 105

## Limitations

1. Static analysis cannot prove runtime behavior
2. Some dependencies may be conditional or environment-specific
3. Dead code may produce false positives
4. Transitive dependencies may not be fully resolved

## Architectural Invariants

- STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY
- MODEL OUTPUT ≠ AUTHORITY
- Evidence scope is preserved across transformations
- The system is READ-ONLY with respect to the target infrastructure