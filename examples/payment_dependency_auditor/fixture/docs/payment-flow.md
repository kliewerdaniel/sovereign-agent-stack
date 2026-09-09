# Payment Flow Documentation

## Standard Payment Processing

The standard payment flow involves three core services:

1. **Checkout** - receives order, initiates payment
2. **Payments** - processes authorization, captures funds
3. **Ledger** - records the transaction

## Refund Processing

Refunds are processed by the Refunds Service, which coordinates with:
- Payments Service (to reverse the charge)
- Ledger Service (to record the refund entry)

## Fraud Detection

All payments are evaluated for fraud by the Fraud Service before authorization.

## Notifications

The Notifications Service sends confirmation emails after successful processing.

## Reconciliation

Nightly reconciliation matches internal ledger records with payment provider records.

## Architecture Decision

The system was designed with minimal coupling:
- Checkout depends only on Payments
- Payments depends only on Ledger and Fraud
- Refunds depends on Payments and Ledger
- Notifications is fully event-driven and independent
- Fraud is stateless and independent

This minimal coupling ensures that no single service failure can cascade.
