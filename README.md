# telegram_channel_subscription_bot

Subscribe messages between channels and groups.

You are also welcome to use my [@channel_subscription_bot](https://t.me/channel_subscription_bot) without create your own bot.

Feedback/Feature requests is welcomed at [@dushufenxiang_chat](https://t.me/dushufenxiang_chat).

Shared with a MIT license.

## commands

subscribe - `subscribe channel/group1 channel/group2` will automatically forward message from channel/group1 to channel/group2
unsubscribe - `unsubscribe channel/group1 channel/group2` will stop subscription

Both of the channels/groups should add this bot as admin.
channel/group can be room ID or room name.

## how to install

First, you need to create a Telegram bot. Talk with the [BotFather](https://t.me/botfather) and ask it for a bot (and its respective token)

Then, you need to add the `TOKEN` file with your token.

The next part is to install in your server the requirements of the bot using `pip3 install -r requirements.txt`.

Finally, adding it on all the relevent groups/channels, and talk to the bot to make subscription with them.

## notes

You are also welcome to use my [@channel_subscription_bot](https://t.me/channel_subscription_bot) without create your own bot.