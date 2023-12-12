import streamlit as st
import pandas as pd
import streamlit_shadcn_ui as ui
import requests
import datetime
from markdownlit import mdlit
import time


def app():
    st.set_page_config(page_icon=":eyes:",page_title="2023 LinkedIn Lookback")

st.title(":eyes: :blue[LinkedIn Lookback]")
mdlit("""This app collects your basic LinkedIn post data (without needing to sign in) from the past 2 years. It then compares posts and engagements to give you an analysis and grade of your content performance.""")
input_value = st.text_input(placeholder="Enter your LinkedIn profile URL here", key="input1", label='Enter the URL of the profile you want to analyze below and click submit.')
clicked = ui.button("Submit", key="submit_btn")
st.text("Here are some examples:")
value = ui.tabs(options=['Lenny Rachitsky', 'Angela Duckworth', 'Dan Martell', 'Alex Hormozi', 'Steven Bartlett'], default_value='Lenny Rachitsky', key="kanaries")

with ui.card(key="image"):
    if value == "Lenny Rachitsky":
        ui.element("img", src="/Users/brocpacholik/LinkedInLookback/lenny_rachitsky.png", className="w-full")
        ui.element("link_button", text=value + " LinkedIn", url="https://www.linkedin.com/in/lennyrachitsky", className="mt-2", key="btn2")
    elif value == "Angela Duckworth":
        ui.element("img", src="./angela_duckworth.png", className="w-full")
        ui.element("link_button", text=value + " LinkedIn", url="https://www.linkedin.com/in/angeladuckworth/", className="mt-2", key="btn2")
    elif value == "Dan Martell":
        ui.element("img", src="./dan_martell.png", className="w-full")
        ui.element("link_button", text=value + " LinkedIn", url="https://www.linkedin.com/in/dmartell/", className="mt-2", key="btn2")
    elif value == "Alex Hormozi":
        ui.element("img", src="./alex_hormozi.png", className="w-full")
        ui.element("link_button", text=value + " LinkedIn", url="https://www.linkedin.com/in/alexhormozi", className="mt-2", key="btn2")
    elif value == "Steven Bartlett":
        ui.element("img", src="./steven_bartlett.png", className="w-full")
        ui.element("link_button", text=value + " LinkedIn", url="https://www.linkedin.com/in/stevenbartlett-123", className="mt-2", key="btn2")

#if not input_value.startswith("https://www.linkedin.com/in"):
#   st.warning("The post analysis only works with a personal profile URL.")

@st.cache_data()
def get_posts_data(input_value):
    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-profile-posts"
    querystring = {"linkedin_url":input_value,"type":"posts"}
    headers = {
        "X-RapidAPI-Key": "9c1847dc95msh72942d9ba1779e6p14cfc2jsn060cb7a3a6b0",
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    posts_data = []
    for i in range(15):  # 6 requests to get 300 posts
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        if 'paging' not in data:
            break
        # Update the querystring with the pagination_token and start number for the next request
        querystring.update({
            "start": str(data['paging']['start'] + 50),
            "pagination_token": data['paging']['pagination_token']
        })
        # Append the new posts to the posts_data list
        posts_data.extend(data['data'])
    return posts_data

def get_month(relative_time):
    current_date = datetime.datetime.now()
    if 'mo' in relative_time:
        months = int(relative_time.replace('mo', ''))
        date = current_date - datetime.timedelta(days=months*30)
    elif 'w' in relative_time:
        weeks = int(relative_time.replace('w', ''))
        date = current_date - datetime.timedelta(weeks=weeks)
    elif 'd' in relative_time:
        days = int(relative_time.replace('d', ''))
        date = current_date - datetime.timedelta(days=days)
    else:
        return None
    return date.strftime('%b')

if clicked:
    progress_text = "Collecting post data. Please be patient, this could take up to a minute."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.2)  # Increased sleep time to slow down the progress bar
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1.2)  # Increased sleep time to slow down the progress bar
    my_bar.empty()

    posts_data = get_posts_data(input_value)
    posts_df = pd.json_normalize(posts_data)

    # Check if 'reshared' column exists in the DataFrame and if it does, drop rows where reshared is True or Yes
    if 'reshared' in posts_df.columns:
        posts_df = posts_df[~posts_df['reshared'].isin([True, 'Yes'])]

    # Select only the required columns and rename them
    posts_df = posts_df[['images', 'time', 'text', 'num_likes', 'num_comments', 'num_reposts', 'post_url']]
    posts_df.rename(columns={'num_likes': 'Likes', 'num_comments': 'Comments', 'num_reposts': 'Reposts', 'post_url': 'Post Link'}, inplace=True)

    # Apply the function to the 'time' column to create the 'Month' column
    posts_df['Month'] = posts_df['time'].apply(get_month)

    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/get-linkedin-profile"
    querystring = {"linkedin_url":input_value}
    headers = {
        "X-RapidAPI-Key": "9c1847dc95msh72942d9ba1779e6p14cfc2jsn060cb7a3a6b0",
        "X-RapidAPI-Host": "fresh-linkedin-profile-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    # Remove print statements and add error handling for percentage calculations
    followers_count = "{:,}".format(data['data']['followers_count']) if 'followers_count' in data['data'] else 'N/A'
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="LinkedIn Followers", content=followers_count, key="card1")
    with cols[1]:
        # Calculate total posts and posts from last year
        total_posts = posts_df['Month'].count()
        posts_last_year = posts_df[posts_df['time'] == '1yr'].shape[0]
        # Calculate the percentage change in posts from last year
        if posts_last_year != 0 and posts_last_year <= 260:
            posts_change = round(((total_posts - posts_last_year) / posts_last_year) * 100)
            posts_change_description = "+ {}% ({})".format(posts_change, posts_last_year) if posts_change > 0 else "{}% ({})".format(abs(posts_change), posts_last_year)
        else:
            posts_change_description = ""
        ui.metric_card(title="Total Posts", content=str(total_posts), description=posts_change_description, key="card2")
    with cols[2]: 
        # Calculate total engagements and engagements from last year
        total_engagements = "{:,}".format(posts_df[posts_df['Month'].notna()]['Likes'].sum() + posts_df[posts_df['Month'].notna()]['Comments'].sum())
        engagements_last_year = posts_df[posts_df['time'] == '1yr']['Likes'].sum() + posts_df[posts_df['time'] == '1yr']['Comments'].sum()
        if engagements_last_year != 0 and posts_last_year <= 260:
            try:
                engagement_change = round(((int(total_engagements.replace(',', '')) - engagements_last_year) / engagements_last_year) * 100)
                change_description = "+ {}% ({})".format(engagement_change, engagements_last_year) if engagement_change > 0 else "{}% ({})".format(abs(engagement_change), engagements_last_year)
            except Exception as e:
                st.error(f"An error occurred: {e}")
                change_description = ""
        else:
            change_description = ""
        ui.metric_card(title="Total Engagements", content=str(total_engagements), description=change_description, key="card3")
    def generate_posts_data(posts_df):
        # Group by 'Month' and count the number of posts
        posts_data = posts_df.groupby('Month').size().reset_index(name='Posts')
        # Reorder the months
        months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        posts_data['Month'] = pd.Categorical(posts_data['Month'], categories=months_order, ordered=True)
        posts_data.sort_values('Month', inplace=True)
        return posts_data

    def generate_engagements_data(posts_df):
        # Group by 'Month' and sum the number of likes and comments
        engagements_data = posts_df.groupby('Month')[['Likes', 'Comments']].sum().reset_index()
        engagements_data['Engagements'] = engagements_data['Likes'] + engagements_data['Comments']
        # Reorder the months
        months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        engagements_data['Month'] = pd.Categorical(engagements_data['Month'], categories=months_order, ordered=True)
        engagements_data.sort_values('Month', inplace=True)
        return engagements_data

    with st.expander("Posts Per Month", expanded=True):
        st.vega_lite_chart(generate_posts_data(posts_df), {
            'mark': {'type': 'bar', 'tooltip': False, 'fill': 'rgb(0, 0, 0)', 'cornerRadiusEnd': 4 },
            'encoding': {
                'x': {'field':'Month','type': 'ordinal', 'sort': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 'axis': {'label': False}},
                'y': {'field': 'Posts', 'type': 'quantitative', 'axis': {'grid': False}},
            },
        }, use_container_width=True)

    with st.expander("Engagements Per Month", expanded=False):
        st.vega_lite_chart(generate_engagements_data(posts_df), {
            'mark': {'type': 'bar', 'tooltip': False, 'fill': 'rgb(0, 0, 0)', 'cornerRadiusEnd': 4 },
            'encoding': {
                'x': {'field':'Month','type': 'ordinal', 'sort': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 'axis': {'label': False}},
                'y': {'field': 'Engagements', 'type': 'quantitative', 'axis': {'grid': False}},
            },
        }, use_container_width=True)
    # Create a new column for the image column
    image_column = st.column_config.ImageColumn(label="Images")

    # Manipulate the 'images' column to extract the image URL
    posts_df['images'] = posts_df['images'].apply(lambda x: x[0]['url'] if x else None)

    # Display the dataframe with the image column inside an expander
    with st.expander("All Post Data"):
        st.dataframe(posts_df, hide_index=True, column_config={"images": image_column})


