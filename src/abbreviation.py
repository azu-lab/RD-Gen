PAC = {
    'Number of nodes': 'NN',
    'Number of entry nodes': 'NEN',
    'In-degree': 'ID',
    'out-degree': 'OD',
    'Execution time': 'ET',
    'Max number of same-depth nodes': 'MNSD',
    'Force merge to exit nodes': 'FME',
    'Number of exit nodes': 'NEX',
    'Use end-to-end deadline': 'UED',
    'Ratio of deadlines to critical path length': 'RDC',
    'Ratio of deadlines to max period': 'RDP',
    'Use communication time': 'UCT',
    'Use multi-period': 'UMP',
    'Periodic type': 'PT',
    'Period': 'P',
    'Entry node periods': 'ENP',
    'Exit node periods': 'EXP',
    'Max ratio of execution time to period': 'MREP',
    'Descendants have larger period': 'DLP',
    # chain
    'Number of chains': 'NC',
    'Chain length': 'CL',
    'Chain width': 'CW',
    'Vertically link chains': 'VLC',
    'Max level of vertical links': 'MLV',
    'Merge chains': 'MGC',
    'Middle of chain': 'MDC',
    'Exit node': 'EXN',
    'Head of chain': 'HDC'
}


def to_ori(val):
    keys = [k for k, v in PAC.items() if v == val]
    if keys:
        return keys[0]
    return None
