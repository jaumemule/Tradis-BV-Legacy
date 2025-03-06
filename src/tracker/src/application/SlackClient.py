from slackclient import SlackClient

class Slack:
    slackClient = ''
    environmentName = ''

    def __init__(self, slackToken, environmentName):
        self.SlackClientSdk = SlackClient(slackToken)
        self.environmentName = environmentName

    def send(self, message: str) -> None:

        channel = '#errors'

        if self.environmentName == 'production':
            channel = '#tracker-production'

        if self.environmentName == 'staging':
            channel = '#tracker-staging'

        if self.environmentName == "production" or self.environmentName == 'staging':
            self.SlackClientSdk.api_call(
                "chat.postMessage",
                channel=channel,
                text=message)
        else:
            print(message)
