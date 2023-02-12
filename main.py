from instagrapi import Client
import openai
import os
import dotenv
import re
import json
from fastapi import FastAPI, Body
app = FastAPI()

dotenv_path = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_path)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.post("/comment")
async def comment(
    hashtag:            str = Body(..., description="The hashtag to search for"),
    number_of_comments: int = Body(..., description="The number of comments to place"),
    instagram_username: str = Body(..., description="The Instagram username"),
    instagram_password: str = Body(..., description="The Instagram password"),
):
    comments = post_comments(hashtag, number_of_comments, instagram_username, instagram_password)
    return json.dumps(comments)

def clean_output(output):
    """
    Clean the output from GPT-3.
    :type output: str the output from GPT-3
    :rtype: str the cleaned output
    """
    print(output)
    leading_empty_removed_1 = output.strip()
    leading_hashtags_removed = re.sub(r'^(#\w+\s)+', '', leading_empty_removed_1)
    leading_empty_removed_2 = leading_hashtags_removed.strip()
    return leading_empty_removed_2

def generate_comment(full_name, caption_text, location_name, taken_at_date):
    """
    Query OpenAI GPT-3 for a comment to post on Instagram.
    :type full_name: str the full name of the user
    :type caption_text: str the caption text of the post
    :type location_name: str the location name of the post
    :type taken_at: int the time the post was taken
    :rtype: str the comment to post on Instagram
    """
    prompt = "Write a comment for an Instagram post by " + full_name

    if location_name != "None":
        prompt += " in " + location_name

    prompt += " at " + str(taken_at_date) + \
        " with this caption:\n\n" + caption_text

    completions = openai.Completion.create(
        engine='text-davinci-003',  # Determines the quality, speed, and cost.
        temperature=1,              # Level of creativity in the response
        prompt=prompt,              # What to query GPT-3 with
        max_tokens=256,             # Maximum tokens in the prompt AND response
        n=1,                        # The number of completions to generate
        stop=None,                  # An optional setting to control response generation
    )

    # Return the first choice's text
    return clean_output(completions.choices[0].text)

def post_comments(hashtag, number_of_comments, instagram_username, instagram_password):
    """
    Get the most recent posts from a hashtag and post a comment on each one.
    :type hashtag: str the hashtag to get posts from
    :type number_of_comments: int the number of comments to post
    :type instagram_username: str the Instagram username to log in with
    :type instagram_password: str the Instagram password to log in with
    :rtype: list a list of comments posted
    """
    cl = Client()
    cl.login(instagram_username, instagram_password)

    openai.api_key = credentials.openai_api_key

    results = cl.hashtag_medias_recent(hashtag, amount=number_of_comments)
    print(results)

    comment_list = []
    for i in range(0, len(results)):
        media_id = results[i].pk
        code = results[i].code
        taken_at = results[i].taken_at
        taken_at_date = taken_at.strftime("%d %B %Y")
        full_name = results[i].user.full_name
        comment_count = results[i].comment_count
        caption_text = results[i].caption_text
        location = results[i].location
        if location:
            location_name = location.name
        else:
            location_name = "None"
        comments_disabled = results[i].comments_disabled

        print("Media ID: " + media_id)
        print("Code: " + code)
        print("Date: " + taken_at_date)
        print("Full name: " + full_name)
        print("Number of comments: " + str(comment_count))
        print("Caption: " + caption_text)
        print("Location: " + location_name)

        cl.media_like(media_id)

        if (not comments_disabled):
            comment = generate_comment(
                full_name, caption_text, location_name, taken_at_date)

            print("Comment: " + comment)

            cl.media_comment(media_id, comment)

            comment_list.append(["https://instagram.com/p/"+code, comment])
    
    return comment_list