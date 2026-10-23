# Delivered-Order Measurement Contract

Version 1.0 — 2026-10-23

## Purpose
Measure marketing against real sales outcomes, not message volume. Intended for direct sales through Messenger/WhatsApp and local delivery.

## Required order states
- `new_lead`: conversation exists, no order yet
- `confirmed`: customer confirmed the order
- `dispatched`: delivery started
- `delivered`: customer received the order
- `cancelled`: cancelled before successful delivery
- `returned`: delivered and later returned/refunded
- `failed_delivery`: delivery attempt did not complete

Keep state changes timestamped. Do not erase failed or returned orders from reporting.

## Core metrics
Use one currency and a consistent attribution window.
- Cost per retained delivered order = ad spend / retained delivered orders. Undefined if the denominator is zero.
- New-customer acquisition cost = ad spend / distinct first-time customers with a retained delivered order. Undefined if the denominator is zero.
- Retained delivered-sales ROAS = revenue from retained delivered orders, net of discounts/refunds / ad spend. Undefined if spend is zero.
- Contribution before ads = retained delivered revenue - product costs - business-paid delivery costs - payment fees - return/damage/failed-delivery losses.
- Contribution after ads = contribution before ads - ad spend.
- Retained delivery rate = retained delivered orders / confirmed orders eligible for delivery.
- Return rate = returned orders / delivered orders; always state the cohort and time window.

Do not substitute messages, leads, confirmed orders, or dispatched orders for delivered orders in acquisition-cost calculations.

## Cost treatment
- If unit product cost already includes serum, bottle, cap, label, filling and packing, do not add those components again.
- Record delivery cash cost separately. If the owner personally delivers, optional time/opportunity cost should be tracked separately rather than silently treating delivery as economically free.
- Avoid double-counting product costs when a failed delivery or return also incurs a loss.
- Do not add different currencies directly. Record exchange rate and date for conversions.
- Separate paid and organic acquisition; organic content still consumes time and production resources.

## Attribution and privacy
- Record campaign/ad identifiers only when actually available; do not guess attribution.
- Use a pseudonymous customer key in analytics exports. Keep names, phone numbers, addresses and private conversation contents out of the analytics ledger.
- Define one attribution window and apply it consistently. Report unattributed orders separately.
- Reconcile the ledger against actual delivery/payment records before using metrics to raise budgets.

## Minimum daily review
1. New conversations and qualified conversations.
2. Confirmed and dispatched orders.
3. Retained delivered orders.
4. Cancelled, failed-delivery and returned orders.
5. Ad spend, cost per retained delivered order and new-customer acquisition cost.
6. Contribution after ads.

## Decision rule
Do not scale based on message cost alone. Compare acquisition cost on retained delivered customers with contribution margin, include returns and failed deliveries, and allow enough time for delivery outcomes to mature. If attribution or delivery data is incomplete, mark the decision inconclusive rather than declaring a winner.
