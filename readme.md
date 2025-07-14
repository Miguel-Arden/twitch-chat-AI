Hello! This is a random project I made over the past few months, hope you can find some form of use out of this.

I will now give you a general breakdown on how to use this.

So before you do anything you need to do the following:
- Install Python (https://www.python.org/downloads/) if you haven't already. I'm currently on version 3.12.8, but I'm 90% sure any version will work.
- Go to your terminal and run the following command, "pip install -r requirements.txt" this will automatically install all the libaries you need for this to work correctly.

- Next you need to make a brand new Twitch channel for the AI
- Make a Twitch Token for your new Twitch Channel (https://twitchtokengenerator.com/) Pick the bot token; please copy the access token.

Now that you have the twitch access token, we need to add it to our environment variables.
Go to your search bar and type the word "env", "Edit the system environment variables" should pop up.
Click that, then click "environment variables" Click that and another window should pop up. Click new on "user variables for *user*"
For variable name, set the name to "AI_TWITCH_ACCESS" then add the token you copied into "variable value"

Keep this window open, we'll be using it again in a second.

Now we need to sort out our OpenAI API.
- go to (https://auth.openai.com/log-in) and make an account
- Once logged in, click settings at the top right, then click "API keys" on the left side
- Then click the "create new secret key" button
- Your API key will be generated, copy it immediately because you won’t be able to see it again when you close the window.
- Now store it in your environment like we did earlier with the variable name of "OPENAI_API_KEY"

Then we need to add credits to our OpenAI account, to actually be able to use it.
- Click your profile on the top right
- Click "Your profile"
- Then click "Billing" on the left side
- Click "Add to credit balance" and then add your payment method and then pay. For me, I used this 3 times a week for about 2-3 hours at a time, and it'd normally take like
3-5 weeks for my credits to run out. I don't advise enabling auto recharge unless you don't care about money.

Go to Chatbot.py and change line 43 to your Twitch channel name, or whatever channel you want the AI to speak in. If the AI doesn't talk, give it Mod and it should work. However
this probably isn't vital, mine works without this step

I recommend messing with the prompt in Prompts.py to get the AI tailored to your stream, the one I provided should work well in general speaking.

Another thing that can help with how the AI talks is fine-tuning on OpenAI. Look into it if the AI doesn't respond to things the way you want.

If anything doesn't work, just ask ChatGPT, that will help you more than I can.

Enjoy! I hope this was helpful or fun for you!