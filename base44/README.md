# Base44-Ready Outline

Base44 CLI auth did not complete in this environment, so this repo includes the product outline instead of a deployed Base44 app.

## Entities

### FeedbackSource

- `product`
- `source`
- `source_type`
- `author`
- `text`
- `created_at`

### EvidenceEvent

- `product`
- `category`
- `severity`
- `source`
- `source_type`
- `evidence`
- `hidden_weight`

### InsightCluster

- `product`
- `category`
- `label`
- `score`
- `opportunity`
- `why_it_matters`

### ActionItem

- `product`
- `priority`
- `title`
- `owner`
- `expected_impact`
- `evidence_categories`

## Functions

### analyzeFeedbackBundle

Accepts a mixed feedback bundle and returns the same contract as `hidden_reviews_agent.py`.

### exportFounderBrief

Creates founder-facing Markdown and CSV evidence exports.

## Agent

### HiddenReviewsAgent

Goal: convert scattered customer feedback into evidence-backed product actions.

Instructions: preserve original quotes, rank hidden signals, avoid invented sources, and connect every action to an evidence category.
