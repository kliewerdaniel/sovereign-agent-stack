# Fulfillment Policy

## Overview

Acme Goods fulfillment process.

## Fulfillment Rules

1. Order is fulfilled only when inventory is available
2. Fulfillment records the shipment date and tracking number
3. Once fulfilled, order cannot be un-fulfilled
4. Unfulfilled orders may be cancelled or refunded

## Inventory Check

- Before fulfillment, inventory must be checked
- If inventory is unavailable, order cannot be fulfilled
- Inventory data may be stale (check timestamp)
