"""Summarize finch bill depths by survival status and island."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED = ['daphne_all', 'survive', 'both_islands', 'location']

def analyze(frame):
    missing = set(REQUIRED) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    d = frame[REQUIRED].apply(pd.to_numeric, errors='raise')
    if len(d) == 0:
        raise ValueError('Input is empty')
    if np.isinf(d.to_numpy()).any():
        raise ValueError('Infinite values are not supported')
    tables = []
    groups = []
    for measure, category, labels in [
        ('daphne_all', 'survive', {0: 'Daphne: did not survive', 1: 'Daphne: survived'}),
        ('both_islands', 'location', {0: 'Daphne: all', 1: 'Santa Cruz: all'})
    ]:
        if (d[measure].isna() != d[category].isna()).any():
            raise ValueError(f'{measure} and {category} must be jointly present or absent')
        sub = d[[measure, category]].dropna()
        if sub.empty or not sub[category].isin([0, 1]).all():
            raise ValueError(f'{category} must contain binary 0/1 values')
        if (sub[measure] <= 0).any():
            raise ValueError('Bill depths must be positive')
        for code, label in labels.items():
            values = sub.loc[sub[category] == code, measure]
            if len(values) < 2:
                raise ValueError(f'At least two observations required for {label}')
            tables.append({'group': label, 'n': len(values), 'mean': values.mean(),
                           'median': values.median(), 'sd': values.std(ddof=1),
                           'minimum': values.min(), 'maximum': values.max()})
            groups.append(values.to_numpy())
    summary = pd.DataFrame(tables)
    all_daphne = d.daphne_all.dropna()
    survivor = d.loc[d.survive == 1, 'daphne_all']
    metrics = {'daphne_observations': len(all_daphne), 'survivors': len(survivor),
               'survival_fraction': len(survivor) / len(all_daphne),
               'survivor_minus_population_mean': float(survivor.mean() - all_daphne.mean()),
               'survivor_minus_nonsurvivor_mean': float(summary.iloc[1]['mean'] - summary.iloc[0]['mean'])}
    return summary, metrics, groups

def run(source, output):
    summary, metrics, groups = analyze(pd.read_csv(source))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / 'group_summary.csv', index=False)
    (output / 'summary.json').write_text(json.dumps(metrics, indent=2) + '\n')
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(groups, vert=False, showfliers=True)
    ax.set_yticks(range(1, 5), summary['group'])
    ax.set_xlabel('Bill depth (input units)')
    ax.set_title('Finch bill-depth distributions')
    ax.grid(axis='x', alpha=.2)
    fig.tight_layout()
    fig.savefig(output / 'bill_depth.svg')
    plt.close(fig)
    return metrics

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), indent=2))
