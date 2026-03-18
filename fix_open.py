import pathlib

f = pathlib.Path('pages/5_\U0001f4c6_Monthly_Performance.py')
content = f.read_text(encoding='utf-8')

fixed = content.replace(
    'wdf["Close"].iloc[-1] / wdf["Open"].iloc[0]',
    'wdf["Close"].iloc[-1] / wdf["Close"].iloc[0]'
).replace(
    'mdf["Close"].iloc[-1] / mdf["Open"].iloc[0]',
    'mdf["Close"].iloc[-1] / mdf["Close"].iloc[0]'
).replace(
    'hdf["Close"].iloc[-1] / hdf["Open"].iloc[0]',
    'hdf["Close"].iloc[-1] / hdf["Close"].iloc[0]'
)

f.write_text(fixed, encoding='utf-8')
remaining = fixed.count('"Open"].iloc[0]')
print(f'Open.iloc[0] noch vorhanden: {remaining} (soll 0)')
print('Fertig!')
