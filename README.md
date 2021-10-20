# say-my-name
A slack bot that will visibly shame you for daring to utter one of the keywords.

For some, a return to a tradition once held sacred.
For the rest, kind of a buzzkill.

Also includes OCR functionality so that the message is interpreted as the user sees it.

Based on https://github.com/danieljabailey/two-bot

## Setup
Copy the example-config.yaml to config.yaml and enter all fields.
Ensure keywords are formatted as follows.
```
keywords:
  <keyword-name>:
    - <keywords>
```

If you are using OCR (don't) you will need a ttf file with a suitable font.

## Evaluated keywords
If you want the bot to evaluate the input to match the keyword simply write the keyword as follows
```
keywords:
  <keyword-name>:
    - eval: <keywords>
```
Evaluation is done with http://newville.github.io/asteval/index.html

## Case Sensitive keywords
If you want a keyword to be case sensitive use the case_sensitive tag
```
keywords:
  <keyword-name>:
    - case_sensitive: <keywords>
```

## Bot Command
Set the bot command with the `command: !say-my-name` config option.

To use the command, with `!say-my-name`

```
!say-my-name
  equivalent to !say-my-name top 5

!say-my-name top {n}
  show the top n users

!say-my-name user @user
  show the record of the specified user
```

## shelve schema
```
{
  <user_id>: {
    'kwords': {
      <kword>: <score>
    },
    'lasttime': <time>
  }
}
```

## Notes
Currently the storage uses python's shelve libary, this is rather primative.
You will have to open the file in python to edit it.

Also, The scores on each individual keyword is stored seperatly but summed each time.
This is a relic of me not thinking things through, although I'm still not sure if I want to get rid of it.

Multiline messages are considered one line, so `same \n <keyword> \n message` would not trigger the keyword.