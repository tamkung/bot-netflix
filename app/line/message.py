import requests

def send_line_notify(message, token):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': message}
    result = requests.post(url, headers=headers, data=data)
    return "OK" if result.status_code == 200 else f"Error: {result.status_code}"