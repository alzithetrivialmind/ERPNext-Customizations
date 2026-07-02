import csv
with open('Items to Import SR data_1.csv', encoding='utf-8-sig') as f:
    r = list(csv.reader(f))[3:]
    dates = set()
    for row in r:
        dates.add(row[24])
        dates.add(row[26])
        dates.add(row[40])
    print('Unique Dates:')
    for d in sorted(list(dates)):
        print(f'"{d}"')
