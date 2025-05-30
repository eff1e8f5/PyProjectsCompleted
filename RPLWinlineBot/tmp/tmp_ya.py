import requests

token = 'y0_AgAAAAAHk_krAAxlrQAAAAEQF6EWAAAYJ6fmGltNyrXzLpqA1I6EDGqhhg'

table_id = 'y4fe24c9b16bbdb1047a1c608ca0a1b70'

file_path = 'disk:/events_table.xlsx'

url = f'https://cloud-api.yandex.net/v1/disk/resources/download?path={file_path}'

headers = {
    'Authorization': f'OAuth {token}',
}
response = requests.get(url, headers=headers)
print(response.url)
download_url = response.json().get('href')

# Скачивание файла
file_data = requests.get(download_url)
with open('local_file.csv', 'wb') as f:
    f.write(file_data.content)

# Теперь файл доступен локально
print("Файл успешно скачан!")
