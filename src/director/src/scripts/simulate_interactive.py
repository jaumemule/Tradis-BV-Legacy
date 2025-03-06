from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from prompt_toolkit.validation import Validator, ValidationError
import datetime
import os

class DateValidator(Validator):
    def validate(self, document):
        ok = True

        try:
            datetime.datetime.strptime(document.text, '%Y-%m-%d %H:%M')
        except Exception:
            ok = False

        if not ok:
            raise ValidationError(
                message='Please enter a valid date',
                cursor_position=len(document.text))  # Move cursor to end

class IntValidator(Validator):
    def validate(self, document):
        ok = True

        try:
            int(document.text)
        except Exception:
            ok = False

        if not ok:
            raise ValidationError(
                message='Please enter a valid number',
                cursor_position=len(document.text))  # Move cursor to end

questions = [
    {
        'type': 'list',
        'name': 'strategyName',
        'message': 'Tell me the strategy',
        'choices': ['procyon', 'ploutos', 'procyon_bitcoin'],
    },
    {
        'type': 'input',
        'name': 'startAt',
        'message': 'Okay, when does it start? Type a valid date (like 2021-01-01 00:51)',
        'validate' : DateValidator
    },
    {
        'type': 'input',
        'name': 'endsAt',
        'message': 'Spectacular, when does it end? Type a valid date',
        'validate' : DateValidator
    },
    {
        'type': 'input',
        'name': 'candleSize',
        'message': 'What is the lenght forecast? (60 procyon, 240 ploutos...)',
        'validate' : IntValidator,
    },
    {
        'type': 'confirm',
        'name': 'tradingBotsEnabled',
        'message': 'Chan chan. Shall we enable the trading bot?',
        'default': False,
    },
    {
        'type': 'input',
        'name': 'lockingMinutes',
        'message': 'How many minutes shall the AI be locked after trading bot trades?',
        'validate': IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'confirm',
        'name': 'lockStrategyAlsoForTradingBot',
        'message': 'Shall we lock the trader bot too?',
        'default': False,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'input',
        'name': 'stoploss',
        'message': 'Stop loss % (0 for disabling)',
        'validate' : IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'input',
        'name': 'jumptomarket',
        'message': 'Jump to market % (0 for disabling)',
        'validate': IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'input',
        'name': 'whaleDownPercent',
        'message': 'Whale down % (0 for disabling)',
        'validate': IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'input',
        'name': 'whaleUpPercent',
        'message': 'Whale up % (0 for disabling)',
        'validate': IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'input',
        'name': 'whaleMinuteLookup',
        'message': 'Whale minute lookup (0 for disabling)',
        'validate': IntValidator,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'confirm',
        'name': 'ignoreStrategyLockOnHardSignal',
        'message': 'Do we ignore strategy lock on hard signal?',
        'default': False,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'confirm',
        'name': 'extendLockUntilHardPrediction',
        'message': 'Do we lock the strategy until there is a hard prediction from AI?',
        'default': False,
        'when': lambda answers: answers['tradingBotsEnabled']
    },
    {
        'type': 'confirm',
        'name': 'slack',
        'message': 'FANTASTIC, we are done. Send results to Slack? (obviously, if you want to see them...)',
        'default': True,
    },
]

answers = prompt(questions)

print(answers['strategyName'])

command = "gcloud beta compute ssh techtradis@study-badass --command 'cd projects/crypto-backup-deployments && docker-compose exec -d director python __simulate__.py \
 --from={startAt} \
 --until={endsAt} \
 --lockingMinutes {lockingMinutes} \
 --strategyName {strategyName} \
 --candleSize {candleSize}  \
 --whaleUpPercent {whaleUpPercent}  \
 --whaleDownPercent {whaleDownPercent} \
 --whaleMinuteLookup {whaleMinuteLookup} {tradingBotsEnabled} {slack}'"

tradingBotsEnabled = ''
if answers['tradingBotsEnabled']:
    tradingBotsEnabled = '--tradingBotsEnabled'

slack = ''
if answers['slack']:
    slack = '--slack'

lockingMinutes = 0
if 'lockingMinutes' in answers:
    lockingMinutes = answers['lockingMinutes']

whaleUpPercent = 1000
if 'whaleUpPercent' in answers:
    whaleUpPercent = answers['whaleUpPercent']

whaleDownPercent = 1000
if 'whaleDownPercent' in answers:
    whaleDownPercent = answers['whaleDownPercent']

whaleMinuteLookup = 0
if 'whaleMinuteLookup' in answers:
    whaleMinuteLookup = answers['whaleMinuteLookup']

final = command.format(
    startAt=answers['startAt'],
    endsAt=answers['endsAt'],
    lockingMinutes=lockingMinutes,
    strategyName=answers['strategyName'],
    candleSize=answers['candleSize'],
    whaleUpPercent=whaleUpPercent,
    whaleDownPercent=whaleDownPercent,
    whaleMinuteLookup=whaleMinuteLookup,
    slack=slack,
    tradingBotsEnabled=tradingBotsEnabled,
)

print('*************************************')
print('ESPECTACULAR! Command auto generated:')
print(final)
os.system(command)
print('*************************************')
# startAt
# untilDate
# sendToSlack
# lockingMinutes
# stoploss
# jumptomarket
# whaleDownPercent
# whaleUpPercent
# whaleMinuteLookup
# takeprofit
# lockStrategyAlsoForTradingBot
# tradingBotsEnabled
# candleSize
# strategyName
# ignoreStrategyLockOnHardSignal
# extendLockUntilHardPrediction