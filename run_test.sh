#!/bin/bash
# Clean test run wrapper

source venv/bin/activate
python main.py --test 2>&1 | grep -v "^\[36m\[apify" | grep -E "^(2025|STAGE|===|Pipeline|Duration|Estimated|Scraped|Filtered|Uploaded|Stage|Creating|Processing|batch|Querying|✓|✗)" ||  python main.py --test 2>&1 | tail -60
