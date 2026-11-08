"""Translate WIQL metadata and work item fields for the shared grid."""
from app.common.grid import GridColumn


def wiql_columns(result):
    columns = []
    for column in result.get('columns', []):
        key = column['referenceName']
        kind = 'html' if key in {'System.Description', 'Microsoft.VSTS.Common.AcceptanceCriteria',
                                 'Microsoft.VSTS.TCM.ReproSteps'} else 'text'
        if key in {'System.Id', 'System.Rev', 'Microsoft.VSTS.Common.Priority',
                   'Microsoft.VSTS.Scheduling.StoryPoints', 'Microsoft.VSTS.Scheduling.Effort',
                   'Microsoft.VSTS.Scheduling.OriginalEstimate', 'Microsoft.VSTS.Scheduling.RemainingWork',
                   'Microsoft.VSTS.Scheduling.CompletedWork'}:
            kind = 'number'
        columns.append(GridColumn(key, column.get('name') or key,
                                  width=400 if key == 'System.Title' else 180, type=kind))
    return columns


def wiql_rows(items):
    return [{**item.get('fields', {}), 'System.Id': item['id']} for item in items]
