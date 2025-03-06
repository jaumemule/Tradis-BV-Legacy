from slackclient import SlackClient


class Slack:
    slackClient = ''
    environmentName = ''

    def __init__(self, slackToken, environmentName, configurations):
        self.SlackClientSdk = SlackClient(slackToken)
        self.environmentName = environmentName
        self.configurations = configurations

    def send(self, message: str) -> None:

        runningMode = self.configurations.currentlyRunningMethodology

        channel = '#errors'

        if runningMode == 'sandbox' and self.environmentName == 'production':
            channel = '#director-production'

        if runningMode == 'real_money' and self.environmentName == 'production':
            channel = '#director-production'

        if runningMode == 'sandbox' and self.environmentName == 'staging':
            channel = '#director-staging'

        if runningMode == 'real_money' and self.environmentName == 'staging':
            channel = '#director-staging'

        if (self.environmentName == "production" or self.environmentName == 'staging') and runningMode != 'simulation':
            self.SlackClientSdk.api_call(
                "chat.postMessage",
                channel=channel,
                text=message
            )
        else:
            print(message)

    def forceSend(self, channel, message):
        self.SlackClientSdk.api_call(
            "chat.postMessage",
            channel=channel,
            text=message
        )
