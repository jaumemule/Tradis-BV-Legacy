from slackclient import SlackClient

slackToken = "xxxxxxxx"


class Slack:

    def __init__(self, slackToken, environmentName):
        self.SlackClientSdk = SlackClient(slackToken)
        self.environmentName = environmentName

    def send(self, message: str) -> None:
        if self.environmentName == "production":
            self.SlackClientSdk.api_call(
                "chat.postMessage",
                channel="#model-training",
                text=message)
        else:
            print(message)
