import requests

def send_discord_webhook(message, webhook_url):
    data = {'content': message}  # Discord Webhook ใช้ key 'content'
    response = requests.post(webhook_url, json=data)

    if response.status_code != 204:
        return f"❌ Failed to send message: {response.status_code} - {response.text}"
    return "✅ Message sent successfully!"