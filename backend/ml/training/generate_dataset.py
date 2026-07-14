import pandas as pd
import numpy as np
import random
import os

# Fixed random seed for reproducibility
np.random.seed(42)
random.seed(42)

NUM_SAMPLES = 5000

incident_types = ['Flood', 'Earthquake', 'Fire', 'Medical', 'Structural Collapse', 'Chemical Spill']
severities = ['low', 'medium', 'high', 'critical']

def label_priority(row):
    # Base interaction rules (Separate from exact app rules to mimic a slightly different perspective)
    score = 0
    
    # Base severity
    if row['severity'] == 'critical': score += 30
    elif row['severity'] == 'high': score += 20
    elif row['severity'] == 'medium': score += 10
    
    # Ratios
    affected = max(1, row['affected_people'])
    trapped_ratio = row['trapped_people'] / affected
    injured_ratio = row['injured_people'] / affected
    
    # Rule 1: High trapped plus injuries may become critical
    if row['trapped_people'] > 5 and row['injured_people'] > 2:
        score += 35
        
    # Rule 2: Small affected but most are trapped -> critical
    if affected < 20 and trapped_ratio > 0.5:
        score += 40
        
    # Rule 3: Children, elderly and injuries increase urgency
    vulnerable_total = row['children_count'] + row['elderly_count'] + row['vulnerable_people']
    if vulnerable_total > 5 and row['injured_people'] > 0:
        score += 25
        
    # Rule 4: High affected without injuries/trapped -> high rather than critical
    if affected > 100 and row['injured_people'] == 0 and row['trapped_people'] == 0:
        score += 15 # not enough to hit critical alone usually
        
    # Wait time gradually increases
    score += min(15, row['waiting_time_hours'] * 1.5)
    
    # Raw volume bumps
    score += (row['injured_people'] * 1.5)
    score += (row['trapped_people'] * 2.0)
    
    # Assign class based on continuous score
    if score >= 75:
        return 'critical'
    elif score >= 50:
        return 'high'
    elif score >= 25:
        return 'medium'
    else:
        return 'low'

data = []
for _ in range(NUM_SAMPLES):
    itype = random.choice(incident_types)
    sev = random.choice(severities)
    
    # Generate realistic correlated numbers
    if sev == 'critical':
        affected = np.random.randint(10, 500)
    elif sev == 'high':
        affected = np.random.randint(5, 200)
    else:
        affected = np.random.randint(0, 50)
        
    # Constraints: injured/trapped <= affected
    injured = np.random.randint(0, affected + 1) if affected > 0 else 0
    # Make some completely uninjured to balance
    if random.random() < 0.4: injured = 0
    
    trapped = np.random.randint(0, affected + 1) if affected > 0 else 0
    if random.random() < 0.6: trapped = 0
    
    # Vulnerable constraints (they can overlap with affected, we assume they are subsets conceptually but independent counts)
    vulnerable = np.random.randint(0, int(affected*0.3) + 1)
    children = np.random.randint(0, int(affected*0.4) + 1)
    elderly = np.random.randint(0, int(affected*0.2) + 1)
    
    wait_time = round(np.random.uniform(0.0, 48.0), 1)
    
    row = {
        'incident_type': itype,
        'severity': sev,
        'affected_people': affected,
        'injured_people': injured,
        'trapped_people': trapped,
        'vulnerable_people': vulnerable,
        'children_count': children,
        'elderly_count': elderly,
        'waiting_time_hours': wait_time
    }
    
    # Calculate label
    priority = label_priority(row)
    row['priority_level'] = priority
    data.append(row)

df = pd.DataFrame(data)

# Ensure balanced dataset by downsampling majority classes
min_count = df['priority_level'].value_counts().min()
df_balanced = df.groupby('priority_level').sample(n=min_count, random_state=42).reset_index(drop=True)

# Shuffle
df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'incident_priority_synthetic.csv')
df_balanced.to_csv(output_path, index=False)

print(f"Generated synthetic dataset with {len(df_balanced)} balanced samples.")
print(df_balanced['priority_level'].value_counts())
