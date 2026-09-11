# Payment Infrastructure Architecture

## Overview

The payment infrastructure processes customer transactions through a pipeline of services.

## Services

### Checkout Service
- Receives customer orders
- Initiates payment processing
- Depends on: Payments Service

### Payments Service
- Core payment processing
- Handles authorization and capture
- Depends on: Ledger Service, Fraud Service

### Ledger Service
- Records all financial transactions
- Maintains double-entry bookkeeping
- Depends on: (none — leaf service)

### Refunds Service
- Processes refund requests
- Depends on: Payments Service, Ledger Service

### Notifications Service
- Sends email/SMS notifications
- Depends on: (none — event-driven)

### Fraud Service
- Evaluates transaction risk
- Depends on: (none — stateless evaluation)

### Reconciliation Service
- Matches internal records with provider records
- Depends on: Ledger Service, Payments Service

## Data Flow

```
Customer → Checkout → Payments → Ledger
                  ↘ Fraud
```

## Payment Flow

1. Customer submits order via Checkout
2. Checkout sends payment request to Payments
3. Payments evaluates fraud risk via Fraud Service
4. Payments authorizes with external provider
5. Payments records transaction in Ledger
6. Notifications sends confirmation

## Environment

All services run in Docker Compose for development.
Production deployment uses Kubernetes.
