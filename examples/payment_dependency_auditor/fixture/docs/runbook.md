# Operations Runbook

## Service Dependencies

### Documented Dependencies
- Checkout → Payments
- Payments → Ledger, Fraud
- Refunds → Payments, Ledger
- Reconciliation → Ledger, Payments

### Undocumented Dependencies
- Payments → Customer Profile (for KYC verification)
- Payments → Feature Flags (for gradual rollout)
- Payments → External Tax (for international transactions)

## Critical Operations

### Payment Authorization
1. Validate order with Checkout
2. Check fraud score
3. Verify customer KYC status
4. Check feature flags for new payment methods
5. Calculate tax if international
6. Authorize with provider
7. Record in ledger

### Refund Processing
1. Validate original transaction
2. Check refund eligibility window
3. Reverse with provider
4. Record refund in ledger
5. Send notification

## Troubleshooting

### Payment Failures
- Check Payments service health
- Verify Ledger connectivity
- Check Fraud service response time
- Verify external provider status

### Reconciliation Issues
- Check for missing ledger entries
- Verify provider settlement files
- Run manual reconciliation script
