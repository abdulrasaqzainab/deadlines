#!/usr/bin/env python3

import yaml

# Load the conferences YAML
with open('_data/conferences.yml', 'r') as file:
    conferences = yaml.safe_load(file)

print("Conferences missing deadline fields:")
print("=" * 50)

missing_deadline = []
tba_deadline = []
valid_deadline = []

for conf in conferences:
    title = conf.get('title', 'Unknown')
    year = conf.get('year', 'Unknown')
    deadline = conf.get('deadline')
    
    if deadline is None:
        missing_deadline.append(f"{title} {year}")
    elif deadline == "TBA":
        tba_deadline.append(f"{title} {year}")
    else:
        valid_deadline.append(f"{title} {year}")

print(f"Missing deadline field ({len(missing_deadline)}):")
for conf in missing_deadline[:10]:  # Show first 10
    print(f"  - {conf}")
if len(missing_deadline) > 10:
    print(f"  ... and {len(missing_deadline) - 10} more")

print(f"\nTBA deadlines ({len(tba_deadline)}):")
for conf in tba_deadline[:5]:  # Show first 5
    print(f"  - {conf}")

print(f"\nValid deadlines: {len(valid_deadline)}")
print(f"Total conferences: {len(conferences)}")