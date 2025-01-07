import pandas as pd
import time
from time import sleep
import os
from tqdm import tqdm
import praw
import praw.exceptions
import emoji
from collections import Counter
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt


# Set up the output directory
output_dir = 'data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)


reddit = praw.Reddit(
    client_id = '9AkNcQ17Z5pi_zo36Qrr6g',
    client_secret = 'bTQxJR7g2NVrYQZ1kNT1iipeMIGckA',
    user_agent = 'Dry_Try8800',
    check_for_async = False
)

def extract_emojis(text):
    return ''.join(char for char in text if char in emoji.EMOJI_DATA)

def fetch_posts(subreddit, total_posts_to_retrieve, time_filter='year'):
    all_posts = []
    for post in tqdm(subreddit.top(limit=total_posts_to_retrieve, time_filter=time_filter),
                     total=total_posts_to_retrieve, desc=f'Reddit posts in {subreddit.display_name}'):
        all_posts.append({
            'subreddit': post.subreddit.display_name,
            'selftext': post.selftext,
            'title': post.title,
            'author_fullname': post.author_fullname if post.author else 'N/A',
            'upvote_ratio': post.upvote_ratio,
            'ups': post.ups,
            'created': post.created,
            'created_utc': post.created_utc,
            'num_comments': post.num_comments,
            'author': str(post.author) if post.author else 'N/A',
            'id': post.id
        })
    return all_posts

def fetch_comments(post_ids):
    comments_list = []
    for post_id in post_ids:
        try:
            submission = reddit.submission(id=post_id)
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                comment_body = comment.body
                emojis_in_comment = extract_emojis(comment_body)

                comments_list.append({
                    'comment_id': comment.id,
                    'parent_id': comment.parent_id,
                    'post_id': post_id,
                    'comment_body': comment_body,
                    'emojis': emojis_in_comment
                })
        except Exception as e:
            print(f"Handling replace_more exception for post {post_id}: {e}")
            sleep(3)
    return comments_list

def save_to_csv(dataframe, file_path):
    try:
        dataframe.to_csv(file_path, index=False)
        print(f"CSV saved successfully: {file_path}")
    except Exception as e:
        print(f"Error saving CSV at {file_path}: {e}")

def analyze_emojis(comments_df, subreddit_name):
    all_emojis = ''.join(comments_df['emojis'])
    cleaned_string = re.sub(r'[\U0001fa77\U0001f979\U0001faf6\U0001fae1\U0001fab7\U0001faf3\U0001fae0\U0001faf0🏼]', '', all_emojis)
    emoji_counts = Counter(cleaned_string)
    print(f"Most common emojis in {subreddit_name}: {emoji_counts.most_common(10)}")
    return emoji_counts

def generate_wordcloud(emoji_counts, subreddit_name):
    try:
        wordcloud = WordCloud(font_path='/content/drive/MyDrive/Symbola.ttf',
                              width=800, height=400, background_color="white",
                              prefer_horizontal=1.0).generate_from_frequencies(emoji_counts)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.title(f"Emoji Word Cloud for {subreddit_name}")
        plt.show()
    except Exception as e:
        print(f"Error generating word cloud for {subreddit_name}: {e}")

def scrape_subreddits(subreddits, category_name, output_dir):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        total_posts_to_retrieve = 2
        all_posts = fetch_posts(subreddit, total_posts_to_retrieve)
        post_ids = [post['id'] for post in all_posts]

        # Fetch and save posts
        df_posts = pd.DataFrame(all_posts).drop_duplicates(subset='id')
        save_to_csv(df_posts, f"{output_dir}/{category_name}_{subreddit_name}_posts.csv")

        # Fetch and save comments
        comments_list = fetch_comments(post_ids)
        df_comments = pd.DataFrame(comments_list)
        save_to_csv(df_comments, f"{output_dir}/{category_name}_{subreddit_name}_comments.csv")

        # Emoji analysis and word cloud
        # emoji_counts = analyze_emojis(df_comments, subreddit_name)
        # generate_wordcloud(emoji_counts, subreddit_name)
